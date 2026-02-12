#!/bin/bash

# Cortex Core Enterprise Setup Script

set -e

echo "🚀 Setting up Cortex Core Enterprise"
echo "===================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install basic dependencies
echo "📦 Installing basic dependencies..."
pip install -r requirements.txt

# Install enterprise dependencies if available
if [ -f "requirements-enterprise.txt" ]; then
    echo "🏢 Installing enterprise dependencies..."
    pip install -r requirements-enterprise.txt
fi

# Install in development mode
echo "🔧 Installing Cortex Core in development mode..."
pip install -e .

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs config

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔐 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Create local config if it doesn't exist
if [ ! -f "config/local.yaml" ]; then
    echo "⚙️ Creating local configuration..."
    cat > config/local.yaml << EOF
system:
  environment: "development"
  log_level: "DEBUG"

api:
  debug: true

storage:
  database:
    type: "sqlite"
    path: "data/cortex.db"
  cache:
    type: "memory"
EOF
fi

# Run basic health check
echo "🏥 Running basic health check..."
python -c "import cortex_core; print('✅ Cortex Core imported successfully')"

# Setup pre-commit hooks if available
if command -v pre-commit &> /dev/null; then
    echo "🔗 Setting up pre-commit hooks..."
    pre-commit install
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run 'make run-dev' to start development server"
echo "3. Visit http://localhost:8080/docs for API documentation"
echo ""
echo "Useful commands:"
echo "- make run-dev     : Start development server"
echo "- make test        : Run tests"
echo "- make format      : Format code"
echo "- make lint        : Run linting"
echo ""

# Deactivate virtual environment
deactivate
