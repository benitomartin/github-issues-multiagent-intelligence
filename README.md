# Project Name

## Table of Contents

- [Project Name](#project-name)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Project Structure](#project-structure)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Configuration](#configuration)
    - [PostgreSQL](#postgresql)
      - [Alembic](#alembic)
    - [AWS CDK](#aws-cdk)
    - [Testing](#testing)
  - [License](#license)

## Overview

Briefly describe the project, its purpose, and key features.

## Project Structure

```text
├── LICENSE
├── Makefile
├── README.md
├── alembic.ini
├── configs
│   ├── dev.yaml                  # Configuration file for development environment
│   └── staging.yaml              # Configuration file for staging environment
├── github_test_request.py
├── infrastructure
│   └── docker-compose.yml        # Docker Compose file for development environment
├── migrations                    # Alembic migration files
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── d84b3a18383b_describe_change.py
├── pyproject.toml
├── scripts
│   └── lint-makefile.sh
├── src
│   ├── __init__.py
│   ├── config
│   │   └── repos.yaml              # Repository configuration file
│   ├── data_pipeline
│   │   ├── __init__.py
│   │   └── ingestion.py            # Module for data ingestion
│   ├── database                    # Module for database operations
│   │   ├── __init__.py
│   │   ├── drop_tables.py
│   │   ├── init_db.py
│   │   └── session.py
│   ├── models                      # Module for database models
│   │   ├── __init__.py
│   │   ├── db_models.py
│   │   └── repo_models.py
│   └── utils                       # Module for utility functions
│       └── config.py
└── uv.lock
```

```text
github-issues-multiagent-intelligence/
├── README.md
├── .gitignore
├── uv.lock
├── pyproject.toml
├── Makefile
├── docker-compose.yml               # Compose file for Qdrant + Postgres + API + optional tools
├── .dockerignore
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── infrastructure/
│   ├── cdk/
│   │   ├── app.py
│   │   ├── cdk.json
│   │   ├── requirements.txt
│   │   └── stacks/
│   │       ├── __init__.py
│   │       ├── vector_db_stack.py
│   │       ├── api_stack.py
│   │       ├── agent_stack.py
│   │       └── monitoring_stack.py
│   └── docker/                      # Docker-specific files for services
│       ├── qdrant/                  # Qdrant-specific Docker setup (configs, maybe init scripts)
│       │   └── README.md
│       ├── postgres/                # PostgreSQL-specific configs, init scripts
│       │   ├── init.sql             # Example: DB schema or seed data scripts
│       │   └── README.md
│       └── README.md
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── research_agent.py
│   │   └── orchestrator.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_search.py
│   │   ├── document_retrieval.py
│   │   └── calculator.py
│   ├── vector_store/
│   │   ├── __init__.py
│   │   ├── qdrant_client.py
│   │   └── embeddings.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # Pydantic and/or SQLAlchemy models for PostgreSQL
│   │   ├── crud.py                  # DB access layer (create/read/update/delete)
│   │   └── session.py               # DB connection/session management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routes/
│   │       ├── agents.py
│   │       └── health.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── bedrock_client.py
│   │   └── prompt_templates.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── issue_prompts.py         # Prompt templates for GitHub issues agent(s)
│   ├── models/
│   │   ├── __init__.py
│   │   └── github_issue_models.py  # Pydantic models representing issue data structures
│   ├── data_pipeline/
│   │   ├── __init__.py
│   │   ├── ingestion.py             # ETL pipeline: from raw GitHub to DB to Qdrant
│   │   └── preprocessing.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py               # Evaluation metrics (e.g. accuracy, precision for classification)
│   │   └── observability.py         # Integrations with Opik or other monitoring
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       ├── logging.py
│       └── metrics.py
├── tests/
│   ├── unit/
│   │   ├── test_agents.py
│   │   └── test_tools.py
│   └── integration/
│       └── test_api.py
├── configs/
│   ├── dev.yaml
│   ├── staging.yaml
│   └── prod.yaml
├── monitoring/
│   ├── cloudwatch_dashboards.py
│   ├── alerts.py
│   └── custom_metrics.py
├── scripts/
│   ├── deploy.sh
│   ├── seed_vector_db.py
│   └── cost_analysis.py
└── docs/
    ├── architecture.md
    ├── api-documentation.md
    └── business-case.md

```

## Prerequisites

- Python 3.12
- XXX

## Installation

1. Clone the repository:

   ```bash
   git clone XXX
   cd XXX
   ```

1. Create a virtual environment:

   ```bash
   uv venv
   ```

1. Activate the virtual environment:

   - On Windows:

     ```bash
     .venv\Scripts\activate
     ```

   - On Unix or MacOS:

     ```bash
     source .venv/bin/activate
     ```

1. Install the required packages:

   ```bash
   uv sync --all-groups --all-extra
   ```

1. Create a `.env` file in the root directory:

   ```bash
    cp .env.example .env
   ```

## Usage

### Configuration

Configure API keys, model names, and other settings by editing:

src/configs/settings.py
src/configs/config.yaml

### PostgreSQL

Initialize the PostgreSQL database:

```bash
docker-compose up -d
```

Then got to http://localhost:8080 to connect to your database GUI via Adminer.

| Field        | Value           |
| ------------ | --------------- |
| **System**   | PostgreSQL      |
| **Server**   | `postgres`      |
| **Username** | `myuser`        |
| **Password** | `mypassword`    |
| **Database** | `github_issues` |

#### Alembic

To modify the Schema run this to create the `alembic.ini` and migrations folders:

```bash
alembic init migrations
```

Add the following to alembic.ini:

```ini
sqlalchemy.url = postgresql+psycopg2://myuser:mypassword@localhost:5432/github_issues
```

Also in env.py point to the `db_models.py`

Then run to update the schema:

```bash
alembic revision --autogenerate -m "Change issue_id to BigInteger"
alembic upgrade head
```

### AWS CDK

From the root of the project:

```bash
cd aws_cdk_infra
cdk init
cdk bootstrap
cdk deploy
```

### Testing

Run all tests:

Run all quality checks (lint, format, type check, clean):

```bash
make all
```

Individual Commands:

- Display all available commands:

  ```bash
  make help
  ```

- Check code formatting:

  ```bash
  make ruff-check
  ```

- Format code:

  ```bash
  make ruff-format
  ```

- Lint code:

  ```bash
  make ruff-lint
  ```

- Type check

  ```bash
  make mypy
  ```

- Clean cache and build files:

  ```bash
  make clean
  ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/detect_jailbreak
guardrails hub install hub://guardrails/secrets_present
