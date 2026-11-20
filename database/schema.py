"""Additive SQLite schema for application users and sustainability records."""
from database.connection import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  display_name TEXT NOT NULL CHECK(length(trim(display_name)) BETWEEN 1 AND 120),
  password_salt TEXT,
  password_hash TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS lifestyle_questionnaire_responses (
  response_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  city TEXT NOT NULL CHECK(length(trim(city)) BETWEEN 1 AND 120),
  commute_mode TEXT NOT NULL,
  commute_km_day REAL NOT NULL CHECK(commute_km_day >= 0 AND commute_km_day <= 500),
  commute_days_week INTEGER NOT NULL CHECK(commute_days_week BETWEEN 0 AND 7),
  diet_pattern TEXT NOT NULL,
  housing_type TEXT NOT NULL,
  monthly_budget_inr REAL NOT NULL CHECK(monthly_budget_inr >= 0),
  electricity_kwh_month REAL NOT NULL CHECK(electricity_kwh_month >= 0),
  ac_usage TEXT NOT NULL,
  waste_segregation TEXT NOT NULL,
  preferences_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_lifestyle_user_created ON lifestyle_questionnaire_responses(user_id, created_at DESC);
CREATE TABLE IF NOT EXISTS carbon_footprint_records (
  record_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  response_id INTEGER,
  total_kg_co2e REAL NOT NULL CHECK(total_kg_co2e >= 0),
  category_breakdown_json TEXT NOT NULL,
  input_snapshot_json TEXT NOT NULL DEFAULT '{}',
  factor_version TEXT NOT NULL DEFAULT 'demo-v1',
  is_estimate INTEGER NOT NULL DEFAULT 1 CHECK(is_estimate IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY(response_id) REFERENCES lifestyle_questionnaire_responses(response_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_footprint_user_created ON carbon_footprint_records(user_id, created_at DESC);
CREATE TABLE IF NOT EXISTS ai_recommendations (
  recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  record_id INTEGER,
  action_key TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 240),
  explanation TEXT NOT NULL DEFAULT '',
  estimated_saving_kg_co2e REAL NOT NULL CHECK(estimated_saving_kg_co2e >= 0),
  estimated_cost_inr REAL,
  difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5),
  relevance_score REAL NOT NULL CHECK(relevance_score BETWEEN 0 AND 1),
  rank_position INTEGER NOT NULL CHECK(rank_position > 0),
  status TEXT NOT NULL DEFAULT 'suggested' CHECK(status IN ('suggested','saved','dismissed')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY(record_id) REFERENCES carbon_footprint_records(record_id) ON DELETE SET NULL,
  UNIQUE(user_id, action_key, record_id)
);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON ai_recommendations(user_id, created_at DESC);
CREATE TABLE IF NOT EXISTS user_progress (
  progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  recommendation_id INTEGER,
  goal_title TEXT NOT NULL CHECK(length(trim(goal_title)) BETWEEN 1 AND 240),
  category TEXT NOT NULL,
  progress_percent INTEGER NOT NULL DEFAULT 0 CHECK(progress_percent BETWEEN 0 AND 100),
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','paused')),
  notes TEXT NOT NULL DEFAULT '',
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY(recommendation_id) REFERENCES ai_recommendations(recommendation_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_progress_user_status ON user_progress(user_id, status, updated_at DESC);
"""

def initialize_database():
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        # Migrate the earlier scaffold users table without discarding its rows.
        user_columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
        if "display_name" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN display_name TEXT NOT NULL DEFAULT 'User'")
        if "updated_at" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
        if "password_salt" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN password_salt TEXT")
        if "password_hash" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        footprint_columns = {row["name"] for row in connection.execute("PRAGMA table_info(carbon_footprint_records)")}
        if "input_snapshot_json" not in footprint_columns:
            connection.execute("ALTER TABLE carbon_footprint_records ADD COLUMN input_snapshot_json TEXT NOT NULL DEFAULT '{}'")
