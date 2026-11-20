"""SQLite connection factory with foreign-key enforcement."""
from pathlib import Path
import sqlite3
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent / "sustainable_lifestyle.db"

@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
