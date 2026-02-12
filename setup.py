"""
Setup configuration for Cortex Core.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version
with open('cortex_core/version.py', 'r') as f:
    exec(f.read())  # Defines __version__

# Read long description
readme_path = Path(__file__).parent / 'README.md'
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="cortex-core",
    version=__version__,
    author="Cortex Core Team",
    author_email="contact@cortex-core.ai",
    description="Advanced Neural-Symbolic AI System with Security & Autonomy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cortex-core/cortex-core",
    packages=find_packages(include=['cortex_core', 'cortex_core.*']),
    package_data={
        'cortex_core': ['config/*.yaml', 'config/*.yml'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scipy>=1.7.0",
        "scikit-learn>=1.0.0",
        "torch>=1.9.0",
        "pyyaml>=6.0",
        "fastapi>=0.85.0",
        "uvicorn>=0.18.0",
        "pydantic>=1.10.0",
        "click>=8.0.0",
        "tqdm>=4.62.0",
        "cachetools>=5.2.0",
    ],
    extras_require={
        "enterprise": [
            "aioredis>=2.0.0",
            "sqlalchemy>=1.4.0",
            "cryptography>=36.0.0",
            "prometheus-client>=0.14.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.9.0",
        ],
        "gpu": [
            "torch>=1.9.0+cu113",
            "nvidia-ml-py3>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cortex=cortex_core.cli.main:cli",
            "cortex-core=cortex_core.cli.main:cli",
        ],
    },
)
