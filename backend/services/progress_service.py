"""Store and retrieve goal progress through the SQLite repository layer."""
from database.connection import get_connection

def list_goals(user_id):
    with get_connection() as connection:
        return connection.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,)).fetchall()
