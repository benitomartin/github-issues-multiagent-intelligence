# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session, sessionmaker

# from src.utils.config import settings

# DATABASE_URL = (
#     f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
#     f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
# )

# engine = create_engine(DATABASE_URL, echo=False)
# SessionLocal = sessionmaker(bind=engine)


# def get_session() -> Session:
#     return SessionLocal()

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.utils.config import settings


# Only import boto3 if needed (avoid importing in dev/staging)
def get_db_credentials_from_aws(secret_name: str, region_name: str = "eu-central-1") -> dict:
    import json

    import boto3

    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])


# Detect environment
app_env = os.getenv("APP_ENV", "dev").lower()

if app_env == "prod":
    creds = get_db_credentials_from_aws(settings.SECRET_NAME)
    print(f"creds: {creds}")
    DATABASE_URL = (
        f"postgresql+psycopg2://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['dbname']}"
    )
    print(f"DATABASE_URL: {DATABASE_URL}")
else:
    # Use settings loaded from .env
    DATABASE_URL = (
        f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

# Initialize SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    return SessionLocal()
