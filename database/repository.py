"""Validated CRUD operations used by Streamlit pages and backend services."""
import json
import sqlite3
import hashlib
import secrets
import hmac
import math
from database.connection import get_connection
from database.schema import initialize_database, SCHEMA

def _ready():
    initialize_database()

def _valid_text(value, name, limit=240):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(f"Enter {name.lower()} using 1 to {limit} characters")
    return value.strip()

def _number(value, name, minimum=0, maximum=None):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not math.isfinite(value): raise ValueError(f"{name} must be a finite number")
    if value < minimum: raise ValueError(f"{name} cannot be less than {minimum}")
    if maximum is not None and value > maximum: raise ValueError(f"{name} cannot be greater than {maximum}")
    return value

def _password_digest(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 600_000).hex()

def create_user(email, display_name, password=None):
    _ready()
    email = _valid_text(email, "Email", 254).lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise ValueError("Email address is invalid")
    display_name = _valid_text(display_name, "Display name", 120)
    if password is not None and (not isinstance(password, str) or len(password) < 12 or len(password) > 1024):
        raise ValueError("Password must contain at least 12 characters")
    salt = secrets.token_hex(16) if password is not None else None
    digest = _password_digest(password, salt) if password is not None else None
    try:
        with get_connection() as db:
            cursor = db.execute("INSERT INTO users(email,display_name,password_salt,password_hash) VALUES(?,?,?,?)", (email, display_name, salt, digest))
            return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError("A user with that email already exists") from exc

def authenticate_user(email, password):
    _ready()
    email = _valid_text(email, "Email", 254).lower()
    with get_connection() as db:
        row = db.execute("SELECT user_id,email,display_name,password_salt,password_hash FROM users WHERE email=?", (email,)).fetchone()
    # Run a comparable hash for missing/legacy accounts to reduce account enumeration timing.
    salt = row["password_salt"] if row and row["password_salt"] else "00" * 16
    expected = row["password_hash"] if row and row["password_hash"] else "00" * 32
    candidate = _password_digest(password if isinstance(password, str) else "", salt)
    if not row or not row["password_hash"] or not hmac.compare_digest(candidate, expected):
        return None
    return {"user_id":row["user_id"],"email":row["email"],"display_name":row["display_name"]}

def get_or_create_user(email="demo@example.local", display_name="Demo User"):
    _ready()
    email = _valid_text(email, "Email", 254).lower()
    with get_connection() as db:
        row = db.execute("SELECT user_id FROM users WHERE email=?", (email,)).fetchone()
        if row:
            return row["user_id"]
        cursor = db.execute("INSERT INTO users(email,display_name) VALUES(?,?)", (email, _valid_text(display_name,"Display name",120)))
        return cursor.lastrowid

def get_user(user_id):
    _ready()
    with get_connection() as db:
        row = db.execute("SELECT user_id,email,display_name,created_at,updated_at FROM users WHERE user_id=?", (int(user_id),)).fetchone()
        return dict(row) if row else None

def get_user_by_email(email):
    _ready()
    email = _valid_text(email, "Email", 254).lower()
    with get_connection() as db:
        row = db.execute("SELECT user_id,email,display_name,created_at,updated_at FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None

def update_user(user_id, *, email=None, display_name=None):
    _ready()
    fields, values = [], []
    if email is not None:
        email = _valid_text(email, "Email", 254).lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]: raise ValueError("Email address is invalid")
        fields.append("email=?"); values.append(email)
    if display_name is not None:
        fields.append("display_name=?"); values.append(_valid_text(display_name,"Display name",120))
    if not fields: raise ValueError("Provide at least one field to update")
    fields.append("updated_at=CURRENT_TIMESTAMP"); values.append(int(user_id))
    try:
        with get_connection() as db:
            cursor = db.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id=?", values)
            if cursor.rowcount == 0: raise ValueError("User not found")
    except sqlite3.IntegrityError as exc:
        raise ValueError("Email is already in use") from exc

def save_lifestyle_response(user_id, response):
    _ready()
    required = ("city","commute_mode","commute_km_day","commute_days_week","diet_pattern","housing_type","monthly_budget_inr","electricity_kwh_month","ac_usage","waste_segregation")
    missing = [key for key in required if key not in response]
    if missing: raise ValueError("Missing questionnaire fields: " + ", ".join(missing))
    row = dict(response)
    for key in ("city","commute_mode","diet_pattern","housing_type","ac_usage","waste_segregation"):
        row[key] = _valid_text(row[key], key.replace("_"," "), 120)
    row["commute_km_day"] = _number(row["commute_km_day"], "Commute distance", 0, 500)
    days = _number(row["commute_days_week"], "Commute days", 0, 7)
    if not days.is_integer(): raise ValueError("Commute days must be a whole number")
    row["commute_days_week"] = int(days)
    row["monthly_budget_inr"] = _number(row["monthly_budget_inr"], "Monthly budget")
    row["electricity_kwh_month"] = _number(row["electricity_kwh_month"], "Monthly electricity")
    prefs = row.get("preferences", {})
    try: prefs_json = json.dumps(prefs, allow_nan=False)
    except (TypeError, ValueError) as exc: raise ValueError("Preferences must be JSON-compatible") from exc
    with get_connection() as db:
        cursor = db.execute("""INSERT INTO lifestyle_questionnaire_responses
          (user_id,city,commute_mode,commute_km_day,commute_days_week,diet_pattern,housing_type,monthly_budget_inr,electricity_kwh_month,ac_usage,waste_segregation,preferences_json)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (int(user_id),row["city"],row["commute_mode"],row["commute_km_day"],row["commute_days_week"],row["diet_pattern"],row["housing_type"],row["monthly_budget_inr"],row["electricity_kwh_month"],row["ac_usage"],row["waste_segregation"],prefs_json))
        return cursor.lastrowid

def get_latest_lifestyle_response(user_id):
    _ready()
    with get_connection() as db:
        row = db.execute("SELECT * FROM lifestyle_questionnaire_responses WHERE user_id=? ORDER BY response_id DESC LIMIT 1", (int(user_id),)).fetchone()
        if not row: return None
        result = dict(row); result["preferences"] = json.loads(result.pop("preferences_json")); return result

def create_footprint_record(user_id, total_kg_co2e, category_breakdown, *, response_id=None, factor_version="demo-v1", is_estimate=True, input_snapshot=None):
    _ready()
    total = _number(total_kg_co2e, "Total footprint")
    if not isinstance(category_breakdown, dict) or not category_breakdown: raise ValueError("Category breakdown must be a non-empty object")
    breakdown = {str(k): _number(v, f"{k} footprint") for k,v in category_breakdown.items()}
    if not math.isclose(total, sum(breakdown.values()), rel_tol=1e-6, abs_tol=0.02):
        raise ValueError("Total footprint must match the category breakdown")
    encoded = json.dumps(breakdown, allow_nan=False)
    try: snapshot_json=json.dumps(input_snapshot or {}, allow_nan=False)
    except (TypeError, ValueError) as exc: raise ValueError("Activity inputs must be JSON-compatible") from exc
    with get_connection() as db:
        if response_id is not None:
            own_response=db.execute("SELECT 1 FROM lifestyle_questionnaire_responses WHERE response_id=? AND user_id=?",(int(response_id),int(user_id))).fetchone()
            if not own_response: raise ValueError("Lifestyle response not found for this user")
        cur = db.execute("INSERT INTO carbon_footprint_records(user_id,response_id,total_kg_co2e,category_breakdown_json,input_snapshot_json,factor_version,is_estimate) VALUES(?,?,?,?,?,?,?)", (int(user_id),response_id,total,encoded,snapshot_json,_valid_text(factor_version,"Factor version",40),int(bool(is_estimate))))
        return cur.lastrowid

def get_footprint_records(user_id, limit=20):
    _ready(); limit = int(_number(limit,"Limit",1,500))
    with get_connection() as db:
        rows = db.execute("SELECT * FROM carbon_footprint_records WHERE user_id=? ORDER BY record_id DESC LIMIT ?", (int(user_id),limit)).fetchall()
        result=[]
        for row in rows:
            item=dict(row); item["category_breakdown"] = json.loads(item.pop("category_breakdown_json")); item["input_snapshot"] = json.loads(item.pop("input_snapshot_json", "{}")); result.append(item)
        return result

def export_user_data(user_id):
    """Return user-owned records as a JSON-serializable export bundle."""
    _ready()
    with get_connection() as db:
        user=db.execute("SELECT email,display_name,created_at FROM users WHERE user_id=?",(int(user_id),)).fetchone()
        if not user: raise ValueError("Account not found")
        responses=[dict(r) for r in db.execute("SELECT * FROM lifestyle_questionnaire_responses WHERE user_id=? ORDER BY response_id",(int(user_id),)).fetchall()]
        for row in responses: row["preferences"]=json.loads(row.pop("preferences_json"))
        footprint_rows=db.execute("SELECT * FROM carbon_footprint_records WHERE user_id=? ORDER BY record_id",(int(user_id),)).fetchall()
        footprints=[]
        for row in footprint_rows:
            item=dict(row)
            item["category_breakdown"]=json.loads(item.pop("category_breakdown_json"))
            item["input_snapshot"]=json.loads(item.pop("input_snapshot_json","{}"))
            footprints.append(item)
        recommendations=[dict(r) for r in db.execute("SELECT * FROM ai_recommendations WHERE user_id=? ORDER BY recommendation_id",(int(user_id),)).fetchall()]
        for recommendation in recommendations:
            if recommendation["estimated_saving_kg_co2e"]==0:
                recommendation["estimated_saving_kg_co2e"]=None
                recommendation["saving_estimate_available"]=False
        progress=[dict(r) for r in db.execute("SELECT * FROM user_progress WHERE user_id=? ORDER BY progress_id",(int(user_id),)).fetchall()]
    return {"account":dict(user),"lifestyle_responses":responses,"footprint_estimates":footprints,"recommendations":recommendations,"goals":progress}

def backup_user_database(user_id):
    """Create a portable SQLite backup containing only this user's records."""
    _ready()
    tables=(
        ("users","SELECT user_id,email,display_name,created_at,updated_at FROM users WHERE user_id=?"),
        ("lifestyle_questionnaire_responses","SELECT * FROM lifestyle_questionnaire_responses WHERE user_id=? ORDER BY response_id"),
        ("carbon_footprint_records","SELECT * FROM carbon_footprint_records WHERE user_id=? ORDER BY record_id"),
        ("ai_recommendations","SELECT * FROM ai_recommendations WHERE user_id=? ORDER BY recommendation_id"),
        ("user_progress","SELECT * FROM user_progress WHERE user_id=? ORDER BY progress_id"),
    )
    with get_connection() as source, sqlite3.connect(":memory:") as backup:
        backup.executescript(SCHEMA)
        backup.execute("PRAGMA foreign_keys = ON")
        for table,query in tables:
            rows=source.execute(query,(int(user_id),)).fetchall()
            if not rows:
                if table=="users": raise ValueError("Account not found")
                continue
            columns=list(rows[0].keys())
            placeholders=",".join("?" for _ in columns)
            column_sql=",".join(f'"{column}"' for column in columns)
            backup.executemany(f'INSERT INTO "{table}" ({column_sql}) VALUES ({placeholders})',[[row[column] for column in columns] for row in rows])
        backup.commit()
        return backup.serialize()

def reset_demo_data(user_id):
    """Clear records for the built-in demo profile while retaining the demo account."""
    _ready()
    with get_connection() as db:
        user=db.execute("SELECT email FROM users WHERE user_id=?",(int(user_id),)).fetchone()
        if not user or user["email"].lower()!="demo@example.local":
            raise ValueError("Reset is available only for the built-in demo profile")
        deleted={}
        for table in ("user_progress","ai_recommendations","carbon_footprint_records","lifestyle_questionnaire_responses"):
            cursor=db.execute(f"DELETE FROM {table} WHERE user_id=?",(int(user_id),))
            deleted[table]=cursor.rowcount
        return deleted

def delete_user(user_id):
    """Delete a user's profile and linked application records."""
    _ready()
    with get_connection() as db:
        cursor=db.execute("DELETE FROM users WHERE user_id=?",(int(user_id),))
        if cursor.rowcount==0: raise ValueError("Account not found")

def save_recommendation(user_id, recommendation, record_id=None):
    _ready()
    fields={"action_key":_valid_text(recommendation["action_key"],"Action key",100),"category":_valid_text(recommendation["category"],"Category",80),"title":_valid_text(recommendation["title"],"Title",240),"explanation":str(recommendation.get("explanation", "")),"saving":_number(recommendation.get("estimated_saving_kg_co2e",0),"Estimated saving"),"cost":recommendation.get("estimated_cost_inr"),"difficulty":int(_number(recommendation.get("difficulty",1),"Difficulty",1,5)),"score":_number(recommendation.get("relevance_score",0),"Relevance score",0,1),"rank":int(_number(recommendation.get("rank_position",1),"Rank",1))}
    if fields["cost"] is not None: fields["cost"]=_number(fields["cost"],"Estimated cost")
    with get_connection() as db:
        if record_id is not None:
            own_record=db.execute("SELECT 1 FROM carbon_footprint_records WHERE record_id=? AND user_id=?",(int(record_id),int(user_id))).fetchone()
            if not own_record: raise ValueError("Footprint record not found for this user")
        if record_id is None:
            existing=db.execute("SELECT recommendation_id FROM ai_recommendations WHERE user_id=? AND action_key=? AND record_id IS NULL",(int(user_id),fields["action_key"])).fetchone()
            if existing:
                db.execute("UPDATE ai_recommendations SET category=?,title=?,explanation=?,estimated_saving_kg_co2e=?,estimated_cost_inr=?,difficulty=?,relevance_score=?,rank_position=? WHERE recommendation_id=?",(fields["category"],fields["title"],fields["explanation"],fields["saving"],fields["cost"],fields["difficulty"],fields["score"],fields["rank"],existing["recommendation_id"]))
                return existing["recommendation_id"]
        db.execute("""INSERT INTO ai_recommendations(user_id,record_id,action_key,category,title,explanation,estimated_saving_kg_co2e,estimated_cost_inr,difficulty,relevance_score,rank_position)
        VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(user_id,action_key,record_id) DO UPDATE SET title=excluded.title,explanation=excluded.explanation,estimated_saving_kg_co2e=excluded.estimated_saving_kg_co2e,estimated_cost_inr=excluded.estimated_cost_inr,difficulty=excluded.difficulty,relevance_score=excluded.relevance_score,rank_position=excluded.rank_position RETURNING recommendation_id""", (int(user_id),record_id,fields["action_key"],fields["category"],fields["title"],fields["explanation"],fields["saving"],fields["cost"],fields["difficulty"],fields["score"],fields["rank"]))
        row=db.execute("SELECT recommendation_id FROM ai_recommendations WHERE user_id=? AND action_key=? AND record_id IS ?",(int(user_id),fields["action_key"],record_id)).fetchone()
        return row["recommendation_id"]

def get_recommendations(user_id, limit=100):
    _ready(); limit=int(_number(limit,"Limit",1,500))
    with get_connection() as db:
        return [dict(r) for r in db.execute("SELECT * FROM ai_recommendations WHERE user_id=? ORDER BY created_at DESC,rank_position LIMIT ?",(int(user_id),limit)).fetchall()]

def update_recommendation_status(user_id, recommendation_id, status):
    _ready()
    if status not in {"suggested","saved","dismissed"}: raise ValueError("Invalid recommendation status")
    with get_connection() as db:
        cur=db.execute("UPDATE ai_recommendations SET status=? WHERE recommendation_id=? AND user_id=?",(status,int(recommendation_id),int(user_id)))
        if cur.rowcount==0: raise ValueError("Recommendation not found")

def create_progress(user_id, title, category, recommendation_id=None):
    _ready(); title=_valid_text(title,"Goal title",240); category=_valid_text(category,"Category",80)
    with get_connection() as db:
        if recommendation_id is not None:
            own=db.execute("SELECT 1 FROM ai_recommendations WHERE recommendation_id=? AND user_id=?",(int(recommendation_id),int(user_id))).fetchone()
            if not own: raise ValueError("Recommendation not found for this user")
        cur=db.execute("INSERT INTO user_progress(user_id,recommendation_id,goal_title,category) VALUES(?,?,?,?)",(int(user_id),recommendation_id,title,category))
        return cur.lastrowid

def get_progress(user_id):
    _ready()
    with get_connection() as db:
        return [dict(r) for r in db.execute("""SELECT p.*,r.action_key,r.explanation AS recommendation_explanation
          FROM user_progress p LEFT JOIN ai_recommendations r ON r.recommendation_id=p.recommendation_id AND r.user_id=p.user_id
          WHERE p.user_id=? ORDER BY p.status='completed',p.updated_at DESC,p.progress_id DESC""",(int(user_id),)).fetchall()]

def update_progress(user_id, progress_id, *, progress_percent=None, status=None, notes=None):
    _ready(); fields=[]; values=[]
    if progress_percent is not None:
        progress_value=_number(progress_percent,"Progress",0,100)
        if not progress_value.is_integer(): raise ValueError("Progress must be a whole number")
        progress_percent=int(progress_value); fields.append("progress_percent=?"); values.append(progress_percent)
        if progress_percent==100 and status is None: status="completed"
    if status is not None:
        if status not in {"active","completed","paused"}: raise ValueError("Invalid progress status")
        fields.extend(["status=?","completed_at=CASE WHEN ?='completed' THEN CURRENT_TIMESTAMP ELSE NULL END"]); values.extend([status,status])
    if notes is not None: fields.append("notes=?"); values.append(_valid_text(notes,"Notes",1000) if notes else "")
    if not fields: raise ValueError("Provide at least one progress field to update")
    fields.append("updated_at=CURRENT_TIMESTAMP"); values.extend([int(progress_id),int(user_id)])
    with get_connection() as db:
        cur=db.execute(f"UPDATE user_progress SET {', '.join(fields)} WHERE progress_id=? AND user_id=?",values)
        if cur.rowcount==0: raise ValueError("Progress goal not found")

def delete_progress(user_id, progress_id):
    _ready()
    with get_connection() as db:
        cur=db.execute("DELETE FROM user_progress WHERE progress_id=? AND user_id=?",(int(progress_id),int(user_id)))
        if cur.rowcount==0: raise ValueError("Progress goal not found")
