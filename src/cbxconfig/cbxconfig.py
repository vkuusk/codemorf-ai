"""
CbxConfig Module

This module provides a configuration management system for CBX applications.
It allows loading configuration from various sources with priority order.
"""

import os
import json
import yaml
import toml
import logging
from typing import Dict, Any
from dynaconf import Dynaconf


# Set up logging
logger = logging.getLogger(__name__)




class CbxConfig:
    """
    This class manages configuration for the APP
    1. loads using Dynaconf
    2. has methods to update and save configuration
    """

    def __init__(self, app_name, args, default_config=None):
        """
        Initialize a new configuration instance.

        Args:
            app_name: Name of the application (used for logging and ENV vars prefix
            args: command line arguments
            default_config: Optional dictionary with default configuration values.
        """

        self.app_name = app_name.upper()
        self._config = {}


        self.set('_current_dir', os.getcwd())
        self.set('_user_home', os.path.expanduser('~'))
        if args.config_dir:
            self.set('_config_dir',args.config_dir)
        else:
            self.set('_config_dir', os.path.join(self.get('_user_home'),".{}".format(self.app_name.lower())) )

        # assign defaults
        self._defaults = default_config

        settings_files = []
        config_dir = self.get('_config_dir')
        config_path = os.path.join(config_dir,"config.toml")
        secrets_path = os.path.join(config_dir,"secrets.toml")

        if os.path.isfile(config_path):
            settings_files.append(config_path)
        if os.path.isfile(secrets_path):
            settings_files.append(secrets_path)

        if len(settings_files) == 0:
            settings_files = None

        settings = Dynaconf(
            envvar_prefix=self.app_name,  # Prefix for environment variables
            settings_files=settings_files,
            default_settings=self._defaults,  # Apply default values
            lowercase_read=True
        )

        # Update settings from Args
        for key, value in vars(args).items():
            if value is not None:
                settings_key = key.replace('-', '_').lower()  # Convert to lowercase here
                settings.set(settings_key, value)

        # Get full settings dictionary and normalize everything to lowercase
        settings_dict = settings.as_dict()
        final_config = {}

        # First, initialize with defaults (all lowercase)
        for key, value in self._defaults.items():
            final_config[key.lower()] = value

        # Then extract from DEFAULT_SETTINGS if present
        if 'DEFAULT_SETTINGS' in settings_dict:
            for key, value in settings_dict['DEFAULT_SETTINGS'].items():
                if value:  # Only update if the value is not empty or None
                    final_config[key.lower()] = value

        # Then add top-level settings (like environment variables)
        for key, value in settings_dict.items():
            if key != 'DEFAULT_SETTINGS' and not key.startswith('_'):
                # Only override if value is not empty
                if value:
                    final_config[key.lower()] = value

        # Apply the final normalized configuration
        self._config = final_config


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
                elif file_path.endswith('.toml'):
                    toml.dump(self._config, f)
                else:
                    logger.error(f"Unsupported file format: {file_path}")
                    return False

            logger.info(f"Saved configuration to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving configuration to {file_path}: {str(e)}")
            return False





def _flatten_dict(d, parent_key='', sep='.'):
    """Convert nested dict to flat dict with dot-notation keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def _unflatten_dict(d, sep='.'):
    """Convert flat dict with dot-notation keys to nested dict."""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result

def _update_config(target, source):
    """Update target dict with values from source dict, maintaining structure."""
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            # If both are dicts, update recursively
            _update_config(target[key], value)
        else:
            # Otherwise, update the value
            target[key] = value





def configure_logging(log_file=None, quiet_flag=False, log_level="INFO"):
    """
    Configure logging for the entire application.

    Args:
        log_file (str, optional): Path to log file. If None or empty, no file logging.
        quiet_flag (bool, optional): If True, suppress console output.
        log_level (str or int, optional): Logging level (DEBUG, INFO, etc. or corresponding int values)
    """
    # Create formatters
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)

    # Get the root logger
    root_logger = logging.getLogger()

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Convert string log level to actual level if needed
    if log_level is None:
        numeric_level = logging.INFO
    elif isinstance(log_level, str):
        try:
            numeric_level = getattr(logging, log_level.upper())
        except (AttributeError, TypeError):
            numeric_level = logging.INFO
            print(f"Invalid log level: {log_level}, defaulting to INFO")
    else:
        numeric_level = log_level

    # Set the log level
    root_logger.setLevel(numeric_level)

    # Create and add file handler if log_file is provided
    if log_file:
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error setting up file logging: {e}")

    # Create and add console handler if not quiet
    if not quiet_flag:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # If no handlers were added, add a NullHandler to prevent warnings
    if not root_logger.handlers:
        root_logger.addHandler(logging.NullHandler())




# Example usage
if __name__ == "__main__":

    pass
