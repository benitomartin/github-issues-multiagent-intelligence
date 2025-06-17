# Makefile

# Check if .env exists
ifeq (,$(wildcard .env))
$(error .env file is missing at .env. Please create one based on .env.example)
endif

# Load environment variables from .env
include .env

.PHONY: all ruff mypy clean help

#################################################################################
## Testing Commands
#################################################################################

tests: ## Run all tests
	@echo "Running all tests..."
	uv run pytest
	@echo "All tests completed."

################################################################################
## Linting and Formatting
################################################################################

all: ruff mypy clean ## Run all linting and formatting commands

ruff-check: ## Check Ruff formatting
	@echo "Checking Ruff formatting..."
	uv run ruff format --check .
	@echo "Ruff checks complete."

ruff-format: ## Format code with Ruff
	@echo "Formatting code with Ruff..."
	uv run ruff format .
	@echo "Formatting complete."

ruff-lint: ## Run Ruff linter with auto-fix
	@echo "Running Ruff linter..."
	uv run ruff check . --fix --exit-non-zero-on-fix
	@echo "Ruff checks complete."

mypy: ## Run MyPy static type checker
	@echo "Running MyPy static type checker..."
	uv run mypy
	@echo "MyPy static type checker complete."

clean: ## Clean up cached generated files
	@echo "Cleaning up generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."


################################################################################
## Help Command
################################################################################

help: ## Display this help message
	@echo "Default target: $(.DEFAULT_GOAL)"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help