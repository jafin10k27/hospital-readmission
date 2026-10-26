"""Database Management Module (FR-4).

Manages SQLite storage, table creation, indexing, and transactional logging
for healthcare encounter data and pipeline artifacts.
"""

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from hospital_readmission.logging_config import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """Handles SQLite database operations for the hospital readmission platform."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Creates and returns an active SQLite connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self, schema_file: str | Path | None = None) -> None:
        """Initializes database tables and indexes from schema.sql."""
        if schema_file is None:
            # Look relative to standard project structure
            schema_file = self.db_path.parent.parent.parent / "sql" / "schema.sql"

        schema_path = Path(schema_file)
        if not schema_path.exists():
            # Fallback search
            fallback = Path("sql/schema.sql")
            if fallback.exists():
                schema_path = fallback
            else:
                logger.warning("schema.sql not found at %s. Creating base tables directly.", schema_path)
                self._create_base_tables_direct()
                return

        logger.info("Executing database initialization from %s", schema_path)
        with open(schema_path, encoding="utf-8") as f:
            ddl = f.read()

        with self.get_connection() as conn:
            conn.executescript(ddl)
            conn.commit()
        logger.info("Database schema initialized successfully at %s", self.db_path)

    def _create_base_tables_direct(self) -> None:
        """Fallback DDL executed if schema.sql cannot be located."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS encounters (
                    encounter_id INTEGER PRIMARY KEY,
                    patient_nbr INTEGER,
                    readmitted_30d INTEGER
                );
                """
            )
            conn.commit()

    def store_encounters(
        self,
        df: pd.DataFrame,
        table_name: str = "encounters",
        if_exists: str = "replace",
        index_cols: list[str] | None = None,
    ) -> int:
        """Stores encounter DataFrame into SQLite table and creates index."""
        logger.info("Storing %d rows into SQLite table '%s'...", len(df), table_name)
        with self.get_connection() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)

            # Create indexes on key columns
            default_indexes = ["encounter_id", "patient_nbr", "readmitted_30d"]
            cols_to_index = set(index_cols or default_indexes).intersection(set(df.columns))

            for col in cols_to_index:
                idx_name = f"idx_{table_name}_{col}"
                try:
                    conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({col});")
                except Exception as e:
                    logger.debug("Could not create index on %s: %s", col, e)
            conn.commit()

        logger.info("Successfully stored %d encounters in table '%s'", len(df), table_name)
        return len(df)

    def store_log(
        self,
        df_log: pd.DataFrame,
        table_name: str,
        if_exists: str = "replace",
    ) -> None:
        """Stores a pipeline audit log (cleaning or validation) into SQLite."""
        if df_log.empty:
            return
        with self.get_connection() as conn:
            df_log.to_sql(table_name, conn, if_exists=if_exists, index=False)
            conn.commit()
        logger.info("Stored %d entries in log table '%s'", len(df_log), table_name)

    def execute_query(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Executes a parameterized SQL query and returns results as a DataFrame."""
        with self.get_connection() as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            return pd.read_sql_query(query, conn)
