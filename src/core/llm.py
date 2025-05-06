# core/llm.py - LLM client for interacting with LLM providers

import os
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any

import requests
import ollama
import openai
import anthropic

# Get Ollama API mode from environment
OLLAMA_API_ENABLED = os.getenv("OLLAMA_API_ENABLED", "true").lower() == "true"

class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class BaseLLMProvider(ABC):
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to the LLM provider."""
        pass

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using the LLM provider."""
        pass

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name: str, host: str, logger: logging.Logger):
        super().__init__(logger)
        self.model_name = model_name
        self.host = host if host.startswith(("http://", "https://")) else f"http://{host}"
        self.logger.debug(f"Ollama API mode: {'Direct API' if OLLAMA_API_ENABLED else 'Package'}")
        
    def test_connection(self) -> bool:
        try:
            if OLLAMA_API_ENABLED:
                # Use direct API call
                response = requests.get(f"{self.host}/api/tags")
                if response.status_code == 200:
                    available_models = [model["name"] for model in response.json().get("models", [])]
                    self.logger.debug(f"Available Ollama models: {', '.join(available_models) if available_models else 'None'}")
                    if self.model_name not in available_models and available_models:
                        self.logger.warning(f"Model '{self.model_name}' not found on server.")
                    return True
                return False
            else:
                # Use ollama package
                models = ollama.list()
                available_models = [model["name"] for model in models]
                self.logger.debug(f"Available Ollama models: {', '.join(available_models) if available_models else 'None'}")
                if self.model_name not in available_models and available_models:
                    self.logger.warning(f"Model '{self.model_name}' not found on server.")
                return True
        except Exception as e:
            self.logger.warning(f"Could not connect to Ollama server at {self.host}: {e}")
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            if OLLAMA_API_ENABLED:
                # Use direct API call
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                }
                if system_prompt:
                    payload["system"] = system_prompt

                response = requests.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=90
                )

                if response.status_code == 200:
                    return response.json().get("response", "")
                error_msg = f"API request failed with status {response.status_code}"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
            else:
                # Use ollama package
                options = {
                    "temperature": 0.7
                }
                if system_prompt:
                    options["system"] = system_prompt
                
                response = ollama.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options=options
                )
                return response['response']
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error generating response: {error_msg}")
            return f"Error: {error_msg}"

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_name: str, api_key, logger: logging.Logger = None):
        super().__init__(logger)
        self.model_name = model_name
        self.api_key = api_key

        openai.api_key = self.api_key
        self.logger.debug("Initialized OpenAI client")

    def test_connection(self) -> bool:
        try:
            # List models to test connection
            models = openai.models.list()
            available_models = [model.id for model in models.data]
            self.logger.debug(f"Available OpenAI models: {', '.join(available_models)}")
            if self.model_name not in available_models:
                self.logger.warning(f"Model '{self.model_name}' not found in available models")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to OpenAI: {e}")
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            self.logger.debug(f"Generating response with provider openai")
            self.logger.debug(f"Prompt length: {len(prompt)} characters")
            self.logger.debug(f"First 100 chars of prompt: {prompt[:100]}...")
            
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            
            self.logger.debug("Got LLM response")
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error generating response: {error_msg}")
            return f"Error: {error_msg}"

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, model_name: str, api_key: Optional[str] = None, logger: logging.Logger = None):
        super().__init__(logger)
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not found in environment variables")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.logger.debug("Initialized Anthropic client")

    def test_connection(self) -> bool:
        try:
            # Anthropic doesn't have a direct way to list models, so we'll make a minimal request
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            self.logger.debug(f"Successfully connected to Anthropic using model {self.model_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Anthropic: {e}")
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            self.logger.debug(f"Generating response with provider anthropic")
            self.logger.debug(f"Prompt length: {len(prompt)} characters")
            self.logger.debug(f"First 100 chars of prompt: {prompt[:100]}...")
            
            response = self.client.messages.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1000
            )
            
            self.logger.debug("Got LLM response")
            return response.content[0].text
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error generating response: {error_msg}")
            return f"Error: {error_msg}"

class LLMClient:
    def __init__(self, provider_type: Optional[str] = None, model_name: Optional[str] = None, logger: logging.Logger = None, **kwargs):
        self.logger = logger or logging.getLogger('codemorf')
        
        # Get provider from environment or parameter
        self.provider_type = provider_type
        self.provider_type = self.provider_type.lower()
        
        self.logger.debug(f"Selected provider type: {self.provider_type}")

        # Initialize the appropriate provider
        if self.provider_type == LLMProvider.OLLAMA.value:
            model = model_name
            host = kwargs.get("host")
            self.logger.debug(f"Initializing Ollama provider with model: {model}, host: {host}")
            self.provider = OllamaProvider(model, host, self.logger)
        
        elif self.provider_type == LLMProvider.OPENAI.value:
            model = model_name
            api_key = kwargs.get("api_key")
            self.logger.debug(f"Initializing OpenAI provider with model: {model}")
            self.provider = OpenAIProvider(model, api_key, self.logger)
        
        elif self.provider_type == LLMProvider.ANTHROPIC.value:
            model = model_name
            api_key = kwargs.get("api_key")
            self.logger.debug(f"Initializing Anthropic provider with model: {model}")
            self.provider = AnthropicProvider(model, api_key, self.logger)
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider_type}")

        # Test connection
        self._test_connection()

    def _test_connection(self):
        """Test connection to the LLM provider."""
        self.provider.test_connection()

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using the configured LLM provider."""
        self.logger.debug(f"Generating response with provider {self.provider_type}")
        self.logger.debug(f"Prompt length: {len(prompt)} characters")
        self.logger.debug(f"First 100 chars of prompt: {prompt[:100]}...")
        
        response = self.provider.generate(prompt, system_prompt)
        self.logger.debug("Got LLM response")
        return response

def get_llm_client(appcfg):
    # Get provider type
    provider_type = appcfg.get("llm_provider")
    # model_name = appcfg.get("model_name")

    # Create kwargs dictionary
    kwargs = {}

    # Add provider-specific parameters to kwargs
    if provider_type == "ollama":
        kwargs["host"] = appcfg.get("ollama_host")
        kwargs["api_enabled"] = appcfg.get("ollama_api_enabled")
        kwargs["model_name"] = appcfg.get("ollama_model")

    elif provider_type == "openai":
        kwargs["api_key"] = appcfg.get("openai_api_key")
        kwargs["model_name"] = appcfg.get("openai_model")

    elif provider_type == "anthropic":
        kwargs["api_key"] = appcfg.get("anthropic_api_key")
        kwargs["model_name"] = appcfg.get("anthropic_model")

    # Pass the entire config dictionary
    kwargs["appconfig"] = appcfg._config


    model_name = appcfg.get("model_name")

    return LLMClient(provider_type, **kwargs)