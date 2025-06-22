from loguru import logger
from sqlalchemy import inspect

from src.database.session import db
from src.models.db_models import Base


def init_db() -> None:
    if db.engine is None:
        raise RuntimeError("Database engine is not initialized.")

    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    if "issues" in existing_tables and "comments" in existing_tables:
        logger.info("Tables already exist. Skipping creation.")
    else:
        logger.info("Creating tables in the database...")
        Base.metadata.create_all(bind=db.engine)
        logger.success("Tables created successfully!")


if __name__ == "__main__":
    init_db()
