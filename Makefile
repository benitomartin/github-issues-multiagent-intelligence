# Makefile

APP_ENV ?= dev

ENV_FILE := .env.$(APP_ENV)

# Check if .env exists
ifeq (,$(wildcard $(ENV_FILE)))
$(error $(ENV_FILE) is missing. Please create it based on .env.example)
endif

# Load environment variables from .env
include $(ENV_FILE)
export

.PHONY: mypy clean help

#################################################################################
## Docker Commands
#################################################################################

docker-build: ## Build the Docker image for the 'app' service
	@echo "Building Docker image for 'app' service =$(APP_ENV).."
	COMPOSE_BAKE=true docker compose -f docker/docker-compose.yml build \
        --build-arg APP_ENV=$(APP_ENV) \
        app
	@echo "Docker image github-issues built."

docker-up: ## Start Docker containers
	@echo "Starting Docker containers with $(ENV_FILE)..."
	docker compose --env-file $(ENV_FILE) -f docker/docker-compose.yml up -d
	@echo "Docker containers started."

docker-down: ## Stop and remove Docker containers
	@echo "Stopping Docker containers..."
	docker compose --env-file $(ENV_FILE) -f docker/docker-compose.yml down
	@echo "Docker containers stopped."

#################################################################################
## PostgreSQL Commands
#################################################################################

init-db: ## Initialize the PostgreSQL database
	@echo "Initializing PostgreSQL database for $(APP_ENV)..."
	APP_ENV=$(APP_ENV) uv run src/database/init_db.py
	@echo "PostgreSQL database initialized."

drop-tables: ## Drop all tables in the PostgreSQL database
	@echo "Dropping all tables in the PostgreSQL database for $(APP_ENV)..."
	APP_ENV=$(APP_ENV) uv run src/database/drop_tables.py
	@echo "All tables dropped successfully."

ingest-github-issues: ## Ingest GitHub issues
	@echo "Ingesting GitHub issues for $(APP_ENV)..."
	APP_ENV=$(APP_ENV) uv run src/data_pipeline/ingestion_raw_data.py
	@echo "GitHub issues ingested successfully."

#################################################################################
## Qdrant Commands
#################################################################################

create-collection: ## Create Qdrant collection
	@echo "Creating Qdrant collection for $(APP_ENV)..."
	APP_ENV=$(APP_ENV) uv run src/vectorstore/create_collection.py
	@echo "Qdrant collection created successfully."

create-indexes: ## Create Qdrant collection
	@echo "Creating Qdrant indexes for $(APP_ENV)..."
	APP_ENV=$(APP_ENV) uv run src/vectorstore/create_index.py
	@echo "Qdrant indexes created successfully."


delete-collection: ## Delete Qdrant collection
	@echo "Deleting Qdrant collection for $(APP_ENV)..."
	APP_ENV=$(APP_ENV) uv run src/vectorstore/delete_collection.py
	@echo "Qdrant collection deleted successfully."

ingest-embeddings: ## Ingest embeddings into Qdrant
	@echo "Ingesting embeddings into Qdrant for $(APP_ENV)..."
	APP_ENV=$(APP_ENV) uv run src/data_pipeline/ingest_embeddings.py
	@echo "Embeddings ingested successfully."

#################################################################################
## Graph Commands
#################################################################################

query-graph: ## Query the graph
	@echo "Querying the graph for $(APP_ENV)..."
	APP_ENV=$(APP_ENV) uv run src/agents/graph.py
	@echo "Querying the graph completed."

#################################################################################
## Testing Commands
#################################################################################

all-tests: ## Run all tests
	@echo "Running all tests..."
	APP_ENV=$(APP_ENV) uv run pytest
	@echo "All tests completed."

unit-tests: ## Run only unit tests
	@echo "Running unit tests..."
	APP_ENV=$(APP_ENV) uv run pytest tests/unit
	@echo "Unit tests completed."

integration-tests: ## Run only integration tests
	@echo "Running integration tests..."
	APP_ENV=$(APP_ENV) uv run pytest tests/integration
	@echo "Integration tests completed."


################################################################################
## Pre-commit Commands
################################################################################

pre-commit-run: ## Run pre-commit hooks
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "Pre-commit checks complete."

################################################################################
## Linting and Formatting
################################################################################

all-lint-format: ruff-lint mypy clean ## Run all linting and formatting commands

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
	find . -type d -name ".langgraph_api" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."

lint-makefile: ## Lint Makefile for missing help comments
	@echo "Linting Makefile for missing help comments..."
	chmod +x scripts/lint-makefile.sh
	scripts/lint-makefile.sh
	@echo "Linting complete."

################################################################################
## Help Command
################################################################################

help: ## Display this help message
	@echo "Default target: $(.DEFAULT_GOAL)"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
