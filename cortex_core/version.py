"""
Version information for Cortex Core.
"""

__version__ = "3.0.0"
__version_info__ = (3, 0, 0)

# Build information
__build__ = "enterprise"
__build_date__ = "2024-01-15"
__build_commit__ = "a1b2c3d4e5f6"

# Feature flags
FEATURES = {
    "distributed": True,
    "security": True,
    "autonomy": True,
    "monitoring": True,
    "enterprise": True,
    "production_ready": True,
}

# API versions
API_VERSION = "v3"
MIN_API_VERSION = "v2"
COMPATIBLE_VERSIONS = ["v2", "v3"]


def get_version():
    """Get complete version information."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "build": __build__,
        "build_date": __build_date__,
        "build_commit": __build_commit__,
        "features": FEATURES,
        "api_version": API_VERSION,
        "compatible_versions": COMPATIBLE_VERSIONS,
    }
