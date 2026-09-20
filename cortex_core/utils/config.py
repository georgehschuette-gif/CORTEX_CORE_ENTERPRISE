"""
Configuration utilities for Cortex Core.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file and environment variables.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    # Load environment variables
    load_dotenv()

    # Determine config file path
    if config_path is None:
        config_path = os.getenv("CORTEX_CONFIG_PATH", "config/base.yaml")

    config_file = Path(config_path)

    # Load base configuration
    config = _load_base_config()

    # Load environment-specific configuration
    if config_file.exists():
        with open(config_file, "r") as f:
            env_config = yaml.safe_load(f) or {}
        config = _merge_configs(config, env_config)

    # Override with environment variables
    config = _apply_env_overrides(config)

    return config


def _load_base_config() -> Dict[str, Any]:
    """Load base configuration."""
    base_config_path = Path(__file__).parent.parent.parent / "config" / "base.yaml"

    if base_config_path.exists():
        with open(base_config_path, "r") as f:
            return yaml.safe_load(f) or {}
    else:
        return _get_default_config()


def _get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        "system": {
            "name": "Cortex Core",
            "version": "3.0.0",
            "environment": "development",
            "log_level": "INFO",
            "mode": "adaptive",
        },
        "security": {
            "enabled": True,
            "encryption": True,
            "validation": True,
            "audit_logging": True,
        },
        "api": {"enabled": True, "host": "0.0.0.0", "port": 8080},
    }


def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge configuration dictionaries."""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides."""
    env_mappings = {
        "CORTEX_ENVIRONMENT": ("system", "environment"),
        "CORTEX_LOG_LEVEL": ("system", "log_level"),
        "CORTEX_MODE": ("system", "mode"),
        "CORTEX_API_HOST": ("api", "host"),
        "CORTEX_API_PORT": ("api", "port"),
        "CORTEX_SECURITY_KEY": ("security", "master_key"),
        "CORTEX_DATABASE_URL": ("storage", "database", "url"),
        "CORTEX_REDIS_URL": ("storage", "cache", "url"),
    }

    for env_var, config_path in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            _set_nested_value(config, config_path, value)

    return config


def _set_nested_value(config: Dict[str, Any], path: tuple, value: Any):
    """Set a value in a nested dictionary."""
    current = config
    for key in path[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Convert string values where appropriate
    final_key = path[-1]
    if final_key == "port" and isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            pass

    current[final_key] = value


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration.

    Args:
        config: Configuration to validate

    Returns:
        True if valid, raises exception otherwise
    """
    required_sections = ["system", "security"]

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")

    # Validate system section
    system = config["system"]
    if "mode" in system:
        valid_modes = ["adaptive", "conservative", "aggressive"]
        if system["mode"] not in valid_modes:
            raise ValueError(f"Invalid mode '{
                    system['mode']}'. Must be one of: {valid_modes}")

    # Validate API section
    if "api" in config:
        api = config["api"]
        if "port" in api:
            port = api["port"]
            if not isinstance(port, int) or not (1 <= port <= 65535):
                raise ValueError(f"Invalid port number: {port}")

    return True


def save_config(config: Dict[str, Any], path: str):
    """
    Save configuration to file.

    Args:
        config: Configuration to save
        path: File path
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(path_obj, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def get_config_value(config: Dict[str, Any], key: str, default=None):
    """
    Get configuration value by dot-separated key.

    Args:
        config: Configuration dictionary
        key: Dot-separated key (e.g., 'api.port')
        default: Default value if key not found

    Returns:
        Configuration value
    """
    keys = key.split(".")
    value = config

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value
