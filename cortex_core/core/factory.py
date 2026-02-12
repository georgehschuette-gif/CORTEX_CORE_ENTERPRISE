"""
Factory for creating Cortex Core instances.
"""

import logging
from typing import Dict, Any, Optional
import yaml
from pathlib import Path

from cortex_core.core.cortex_core import CortexCore
from cortex_core.core.distributed_core import DistributedCortexCore
from cortex_core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def create_cortex(
    config_path: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    security_key: Optional[str] = None,
    mode: str = "adaptive"
) -> CortexCore:
    """
    Create a Cortex Core instance.

    Args:
        config_path: Path to configuration file
        config_dict: Configuration dictionary
        security_key: Security key for encryption
        mode: Operation mode

    Returns:
        CortexCore instance
    """
    try:
        # Load configuration
        config = _load_config(config_path, config_dict)

        # Set mode
        config['system']['mode'] = mode

        # Create instance
        cortex = CortexCore(config=config, security_key=security_key)

        logger.info(f"Cortex Core created in {mode} mode")
        return cortex

    except Exception as e:
        logger.error(f"Failed to create Cortex Core: {e}")
        raise


def create_distributed_cortex(
    node_id: str,
    peers: list,
    config_path: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    bootstrap_node: Optional[str] = None
) -> DistributedCortexCore:
    """
    Create a distributed Cortex Core instance.

    Args:
        node_id: Node identifier
        peers: List of peer addresses
        config_path: Path to configuration file
        config_dict: Configuration dictionary
        bootstrap_node: Bootstrap node for joining cluster

    Returns:
        DistributedCortexCore instance
    """
    try:
        # Load configuration
        config = _load_config(config_path, config_dict)

        # Enable cluster mode
        config['cluster'] = {
            'enabled': True,
            'node_id': node_id,
            'peers': peers,
            'bootstrap_node': bootstrap_node
        }

        # Create instance
        cortex = DistributedCortexCore(
            node_id=node_id,
            peers=peers,
            config=config,
            bootstrap_node=bootstrap_node
        )

        logger.info(f"Distributed Cortex Core created for node {node_id}")
        return cortex

    except Exception as e:
        logger.error(f"Failed to create distributed Cortex Core: {e}")
        raise


def _load_config(
    config_path: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Load configuration from file or dictionary."""
    if config_dict is not None:
        return config_dict

    if config_path is None:
        # Use default config
        return _get_default_config()

    # Load from file
    path = Path(config_path)
    if not path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")

    if path.suffix in ['.yaml', '.yml']:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
    elif path.suffix == '.json':
        import json
        with open(path, 'r') as f:
            config = json.load(f)
    else:
        raise ConfigurationError(f"Unsupported config format: {path.suffix}")

    return config


def _get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        'system': {
            'name': 'Cortex Core',
            'version': '3.0.0',
            'mode': 'adaptive',
            'log_level': 'INFO'
        },
        'security': {
            'encryption': True,
            'validation': True,
            'audit_logging': True
        },
        'performance': {
            'caching': True,
            'optimization': True
        },
        'cognitive': {
            'intuition': {},
            'logic': {},
            'fusion': {},
            'executive': {},
            'memory': {}
        }
    }
