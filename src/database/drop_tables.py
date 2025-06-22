from loguru import logger
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from src.database.session import db


def drop_all_tables() -> None:
    if db.engine is None:
        raise RuntimeError("Database engine is not initialized.")

    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    if not existing_tables:
        logger.info("No tables found to drop.")
        return

    logger.warning(f"About to drop all tables: {existing_tables}")
    confirmation = input("Are you sure you want to drop all tables? This action cannot be undone! (y/n): ").strip().lower()

    if confirmation != "y":
        logger.info("Aborted dropping tables.")
        return

    try:
        with db.engine.connect() as conn:
            logger.info("Dropping and recreating public schema to drop all tables...")
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.commit()

        logger.success("All tables dropped successfully!")

    except SQLAlchemyError as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting drop_all_tables script...")
    drop_all_tables()
    logger.info("Script finished.")
