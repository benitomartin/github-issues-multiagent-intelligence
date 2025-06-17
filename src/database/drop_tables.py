from loguru import logger
from sqlalchemy import inspect, text

from src.database.session import engine


def drop_all_tables() -> None:
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if not existing_tables:
        logger.info("No tables found to drop.")
        return

    logger.info(f"Dropping tables: {existing_tables} ...")
    with engine.connect() as conn:
        # Disable FK constraints temporarily (Postgres-specific)
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()

    logger.success("All tables dropped successfully!")


if __name__ == "__main__":
    drop_all_tables()
