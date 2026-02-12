# Cortex Core Enterprise Makefile

.PHONY: help install install-dev install-enterprise clean lint test test-unit test-integration test-performance run run-dev build docker-build docker-run docker-compose-up docker-compose-down docs format check security audit

# Default target
help: ## Show this help message
	@echo "Cortex Core Enterprise - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install basic dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-enterprise.txt
	pip install -e ".[dev]"

install-enterprise: ## Install enterprise dependencies
	pip install -r requirements-enterprise.txt

# Development
clean: ## Clean up build artifacts and cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf build/ dist/ .eggs/

lint: ## Run linting
	flake8 cortex_core tests
	mypy cortex_core

format: ## Format code
	black cortex_core tests
	isort cortex_core tests

check: ## Run all checks (lint, format, test)
	make lint
	make test-unit
	make security

# Testing
test: ## Run all tests
	pytest

test-unit: ## Run unit tests
	pytest tests/unit/ -v

test-integration: ## Run integration tests
	pytest tests/integration/ -v

test-performance: ## Run performance tests
	pytest tests/performance/ -v --durations=10

# Running
run: ## Run Cortex Core
	python -m cortex_core.cli.main run

run-dev: ## Run Cortex Core in development mode
	CORTEX_ENVIRONMENT=development CORTEX_LOG_LEVEL=DEBUG python -m cortex_core.cli.main run

# Docker
docker-build: ## Build Docker image
	docker build -t cortex-core .

docker-run: ## Run Docker container
	docker run -p 8080:8080 -p 8081:8081 cortex-core

docker-compose-up: ## Start all services with Docker Compose
	docker-compose up -d

docker-compose-down: ## Stop all services
	docker-compose down

# Documentation
docs: ## Build documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

# Security
security: ## Run security checks
	bandit -r cortex_core
	safety check

audit: ## Run full security audit
	make security
	# Add additional security checks here

# Deployment
build: ## Build package
	python -m build

publish: ## Publish to PyPI (requires credentials)
	twine upload dist/*

# Development helpers
setup-dev: ## Setup development environment
	pre-commit install
	make install-dev
	cp .env.example .env

update-deps: ## Update dependencies
	pip-compile requirements.in
	pip-compile requirements-enterprise.in
	pip-compile requirements-dev.in

# Database
db-init: ## Initialize database
	python -m cortex_core.cli.main db init

db-migrate: ## Run database migrations
	python -m cortex_core.cli.main db migrate

db-upgrade: ## Upgrade database
	python -m cortex_core.cli.main db upgrade

# Monitoring
metrics: ## Show metrics
	curl http://localhost:8081/metrics

health: ## Check health
	curl http://localhost:8080/health

# Logs
logs: ## Show logs
	tail -f logs/cortex.log

# Environment
env-check: ## Check environment
	python -c "import cortex_core; print('Cortex Core version:', cortex_core.__version__)"
	python -c "import sys; print('Python version:', sys.version)"

# CI/CD
ci: ## Run CI pipeline locally
	make clean
	make check
	make test
	make build
