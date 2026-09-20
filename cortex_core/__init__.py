"""
Cortex Core - Advanced Neural-Symbolic AI System
Enterprise Edition v3.0
"""

from cortex_core.core.factory import create_cortex, create_distributed_cortex
from cortex_core.exceptions import ConfigurationError, CortexError, SecurityError
from cortex_core.version import __version__, get_version

# Export main classes
__all__ = [
    # Main classes
    "create_cortex",
    "create_distributed_cortex",
    # Exceptions
    "CortexError",
    "SecurityError",
    "ConfigurationError",
    # Version
    "__version__",
    "get_version",
]

# Don't import CortexCore directly to avoid circular imports
# Use factory methods instead
