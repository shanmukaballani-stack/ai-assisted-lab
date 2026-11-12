import os
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path


DATABASE_PATH = Path(
    os.environ.get(
        "PLACEMENTS_DATABASE_PATH",
        Path(__file__).with_name("placements.db"),
    )
).expanduser().resolve()


@contextmanager
def database_connection(database_path=DATABASE_PATH):
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            yield connection


def initialize_database(database_path=DATABASE_PATH):
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS applications (
                    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    job_role TEXT NOT NULL,
                    application_date TEXT,
                    status TEXT,
                    interview_date TEXT
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(applications)")
            }
            if "interview_date" not in columns:
                connection.execute(
                    "ALTER TABLE applications ADD COLUMN interview_date TEXT"
                )
