import os
from typing import ClassVar

from loguru import logger
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=f".env.{os.getenv('APP_ENV', 'dev')}",
        env_file_encoding="utf-8",
    )

    AWS_REGION: str = "eu-central-1"
    GH_TOKEN: str = ""
    ISSUES_TABLE_NAME: str = "issues"
    COMMENTS_TABLE_NAME: str = "comments"
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "github_issues"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    ADMINER_PORT: str = "8080"
    SECRET_NAME: str = ""
    APP_ENV: str = "dev"
    LEN_EMBEDDINGS: int = 1024
    QDRANT_API_KEY: str = ""
    QDRANT_URL: str = ""
    DENSE_MODEL_NAME: str = "BAAI/bge-large-en-v1.5"
    SPARSE_MODEL_NAME: str = "Qdrant/minicoil-v1"
    COLLECTION_NAME: str = "github_issues_embeddings"
    CHUNK_SIZE: int = 1000
    BATCH_SIZE: int = 20
    CONCURRENT_COMMENTS: int = 5
    LANGSMITH_API_KEY: str = ""
    OPENAI_API_KEY: SecretStr = SecretStr("")
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    TEMPERATURE: float = 0
    REPOS_CONFIG: str = "src/config/repos.yaml"
    GUARDRAILS_CONFIG: str = "src/config/guardrails.yaml"
    GUARDRAILS_API_KEY: str = ""


# Determine environment first
app_env = os.environ.get("APP_ENV", "dev")

# Map environment to specific env file
env_file_map = {
    "dev": ".env.dev",
    "staging": ".env.staging",
    "prod": ".env.prod",
}

# Select the right env file or fallback to default ".env"
env_file = env_file_map.get(app_env, ".env")

# Dynamically set env_file for Pydantic
Settings.model_config["env_file"] = env_file

# Load settings
settings = Settings()

logger.info(f"App env: {settings.APP_ENV}")
logger.info(f"DB host: {settings.POSTGRES_HOST}")
