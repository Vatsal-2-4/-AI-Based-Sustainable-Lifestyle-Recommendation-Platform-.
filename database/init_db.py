"""Initialize the local SQLite database schema."""
from database.schema import initialize_database

if __name__ == "__main__":
    initialize_database()
    print("Database initialized.")
