from database.connection import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, email TEXT UNIQUE, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS profiles (profile_id INTEGER PRIMARY KEY, user_id INTEGER, city TEXT, housing_type TEXT, monthly_budget REAL, preferences TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(user_id));
CREATE TABLE IF NOT EXISTS footprint_reports (report_id INTEGER PRIMARY KEY, profile_id INTEGER, total_kg_co2e REAL, factor_version TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(profile_id) REFERENCES profiles(profile_id));
CREATE TABLE IF NOT EXISTS footprint_breakdown (breakdown_id INTEGER PRIMARY KEY, report_id INTEGER, category TEXT, kg_co2e REAL, FOREIGN KEY(report_id) REFERENCES footprint_reports(report_id));
CREATE TABLE IF NOT EXISTS actions (action_id TEXT PRIMARY KEY, category TEXT, title TEXT, annual_saving_kg REAL, annual_cost_inr REAL, difficulty INTEGER, eligibility_json TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS recommendations (recommendation_id INTEGER PRIMARY KEY, report_id INTEGER, action_id TEXT, rank INTEGER, score REAL, explanation TEXT, FOREIGN KEY(report_id) REFERENCES footprint_reports(report_id), FOREIGN KEY(action_id) REFERENCES actions(action_id));
CREATE TABLE IF NOT EXISTS goals (goal_id INTEGER PRIMARY KEY, user_id INTEGER, action_id TEXT, status TEXT, started_at TEXT, completed_at TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id), FOREIGN KEY(action_id) REFERENCES actions(action_id));
CREATE TABLE IF NOT EXISTS progress_updates (update_id INTEGER PRIMARY KEY, goal_id INTEGER, progress_value REAL, note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(goal_id) REFERENCES goals(goal_id));
"""

def initialize_database():
    with get_connection() as connection:
        connection.executescript(SCHEMA)
