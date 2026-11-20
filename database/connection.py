from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "sustainable_lifestyle.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection
