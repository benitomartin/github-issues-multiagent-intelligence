from loguru import logger
from sqlalchemy import inspect

from src.database.session import engine
from src.models.db_models import Base


def init_db() -> None:
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "issues" in existing_tables and "comments" in existing_tables:
        logger.info("Tables already exist. Skipping creation.")
    else:
        logger.info("Creating tables in the database...")
        Base.metadata.create_all(bind=engine)
        logger.success("Tables created successfully!")


if __name__ == "__main__":
    init_db()
