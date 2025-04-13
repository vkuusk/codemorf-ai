"""
CbxConfig Module

This module provides a configuration management system for CBX applications.
It allows loading configuration from various sources with priority order.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)




class CbxConfig:
    """
    This class handles loading configuration from multiple sources with priority:
    1. Command line arguments
    2. Environment variables
    3. Configuration files (JSON, YAML)
    4. Default values
    """

    def __init__(self, app_name, default_config):
        """
        Initialize a new configuration instance.

        Args:
            app_name: Name of the application (used for logging and ENV vars prefix
            default_config: Optional dictionary with default configuration values.
                     If not provided, the module's DEFAULT_CONFIG will be used.
        """
        self.app_name = app_name
        self._config = {}
        self._defaults = default_config

        # Apply defaults
        self.reset_to_defaults()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self._deep_copy(self._defaults)

    def _deep_copy(self, obj: Any) -> Any:
        """Create a deep copy of a configuration object."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key path.

        Args:
            key: Dot-notation key path (e.g., 'database.connection_string')
            default: Value to return if key is not found

        Returns:
            The configuration value or default if not found
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key path.

        Args:
            key: Dot-notation key path (e.g., 'database.host')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        # Navigate to the nested dictionary, creating dictionaries as needed
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # Set the value at the final key
        config[keys[-1]] = value

    def load_file(self, file_path: str) -> bool:
        """
        Load configuration from a file (JSON or YAML).

        Args:
            file_path: Path to the configuration file

        Returns:
            True if the file was loaded successfully, False otherwise
        """
        if not os.path.exists(file_path):
            logger.warning(f"Configuration file not found: {file_path}")
            return False

        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    config_data = json.load(f)
                elif file_path.endswith(('.yaml', '.yml')):
                    config_data = yaml.safe_load(f)
                else:
                    logger.error(f"Unsupported file format: {file_path}")
                    return False

            self._merge_config(config_data)
            logger.info(f"Loaded configuration from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading configuration file {file_path}: {str(e)}")
            return False

    def load_env(self, prefix: str = "CBX_") -> int:
        """
        Load configuration from environment variables.

        Environment variables should be in the format PREFIX_SECTION_KEY.
        For example, CBX_SERVER_PORT=8000 would set config['server']['port'] = 8000

        Args:
            prefix: Prefix for environment variables to consider

        Returns:
            Number of configuration values loaded from environment
        """
        # # Load environment variables first
        current_dir = os.getcwd()
        self.set('current_dir', current_dir )

        env_path = os.path.join(current_dir, '.env')
        if os.path.isfile(env_path):
            dotenv_result = load_dotenv(env_path)
            logger.info(f"load_dotenv result: {dotenv_result}")



        count = 0
        prefix = prefix.upper()

        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                # Remove prefix and split by underscore
                key_parts = env_key[len(prefix):].lower().split('_')

                if len(key_parts) >= 2:
                    # Convert to dot notation (e.g., 'server.port')
                    key_path = '.'.join(key_parts)

                    # Try to parse value as JSON, fall back to string if not valid JSON
                    try:
                        value = json.loads(env_value)
                    except json.JSONDecodeError:
                        value = env_value

                    self.set(key_path, value)
                    count += 1

        if count > 0:
            logger.info(f"Loaded {count} configuration values from environment variables")

        return count









    def _merge_config(self, config_data: Dict[str, Any], target: Optional[Dict[str, Any]] = None,
                      path: str = "") -> None:
        """
        Recursively merge configuration dictionaries.

        Args:
            config_data: Source configuration to merge from
            target: Target configuration to merge into (uses self._config if None)
            path: Current path in dot notation for logging
        """
        if target is None:
            target = self._config

        for key, value in config_data.items():
            current_path = f"{path}.{key}" if path else key

            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively merge dictionaries
                self._merge_config(value, target[key], current_path)
            else:
                # Set or override value
                target[key] = self._deep_copy(value)
                logger.debug(f"Set configuration: {current_path} = {value}")

    def load_args(self, args: List[str]) -> int:
        """
        Load configuration from command line arguments.

        Args should be in the format --section.key=value or --section.key value

        Args:
            args: List of command line arguments

        Returns:
            Number of configuration values loaded from arguments
        """
        count = 0
        i = 0

        while i < len(args):
            arg = args[i]

            # Check for --key=value format
            if arg.startswith('--') and '=' in arg:
                key, value = arg[2:].split('=', 1)
                i += 1
            # Check for --key value format
            elif arg.startswith('--') and i + 1 < len(args) and not args[i + 1].startswith('--'):
                key = arg[2:]
                value = args[i + 1]
                i += 2
            else:
                i += 1
                continue

            # Try to parse value as JSON, fall back to string if not valid JSON
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            self.set(key, parsed_value)
            count += 1

        if count > 0:
            logger.info(f"Loaded {count} configuration values from command line arguments")

        return count

    def as_dict(self) -> Dict[str, Any]:
        """
        Return the complete configuration as a dictionary.

        Returns:
            A deep copy of the current configuration dictionary
        """
        return self._deep_copy(self._config)

    def save_to_file(self, file_path: str) -> bool:
        """
        Save the current configuration to a file (JSON or YAML).

        Args:
            file_path: Path to the output file

        Returns:
            True if the file was saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            with open(file_path, 'w') as f:
                if file_path.endswith('.json'):
                    json.dump(self._config, f, indent=2)
                elif file_path.endswith(('.yaml', '.yml')):
                    yaml.dump(self._config, f, default_flow_style=False)
                else:
                    logger.error(f"Unsupported file format: {file_path}")
                    return False

            logger.info(f"Saved configuration to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving configuration to {file_path}: {str(e)}")
            return False

    def load_from_sources(self,
                          config_files: Optional[List[str]] = None,
                          env_prefix: str = "CBX_",
                          cmd_args: Optional[List[str]] = None) -> None:
        """
        Load configuration from multiple sources with priority.

        Lower priority sources are loaded first, so higher priority sources
        can override their values.

        Priority order (lowest to highest):
        1. Default values (already loaded in __init__)
        2. Configuration files
        3. Environment variables
        4. Command line arguments

        Args:
            config_files: List of configuration file paths
            env_prefix: Prefix for environment variables
            cmd_args: List of command line arguments
        """
        # Load configuration files
        if config_files:
            for file_path in config_files:
                self.load_file(file_path)

        # Load environment variables
        self.load_env(env_prefix)

        # Load command line arguments
        if cmd_args:
            self.load_args(cmd_args)

        logger.info("Configuration loaded from all sources")


def configure_logging(log_file, quiet_flag, log_level=logging.INFO):
    """Configure logging for the entire application."""

    # Create handlers
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file)

    if not quiet_flag:
        console_handler = logging.StreamHandler()

    # Create formatters and add it to handlers
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Get the root logger and set its level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Add handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def load_config(app_name,default_config):

    current_dir = os.getcwd()

    cfg = CbxConfig(app_name,default_config)

    cfg.set('current_dir', current_dir)

    cfg.load_from_sources()

    return cfg

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create configuration with defaults
    config = CbxConfig()

    # Load from different sources
    config.load_from_sources(
        config_files=["config.json", "config.local.yaml"],
        cmd_args=["--app.debug=false", "--server.port", "9000"]
    )

    # Access configuration values
    print(f"App name: {config.get('app.name')}")
    print(f"Server port: {config.get('server.port')}")
    print(f"Debug mode: {config.get('app.debug')}")

    # Full configuration
    print("\nFull configuration:")
    print(json.dumps(config.as_dict(), indent=2))