import streamlit as st
from database.repository import get_or_create_user, get_user, get_progress, get_latest_lifestyle_response, get_footprint_records

DEFAULT_PROFILE = {"name":"Demo User", "city":"Bengaluru", "commute":"Petrol / diesel car", "commute_km":18, "commute_days":5, "diet":"Mixed diet", "housing":"Rented apartment", "budget":1000, "electricity":240, "ac":"Some days", "segregation":"Sometimes", "water_usage":"Moderate", "food_waste":"Sometimes", "shopping_habit":"Monthly", "public_transport_available":True, "shops_in_person":True, "composting_possible":False}

def initialize_state():
    st.session_state.setdefault("user_email", "demo@example.local")
    st.session_state.setdefault("profile", DEFAULT_PROFILE.copy())
    st.session_state.setdefault("goals", [])
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("page", "Dashboard")
    user_id = get_or_create_user(st.session_state.user_email, st.session_state.profile["name"])
    st.session_state.user_id = user_id
    user = get_user(user_id)
    if user:
        st.session_state.profile["name"] = user["display_name"]
    if not st.session_state.get("db_profile_loaded", False):
        response=get_latest_lifestyle_response(user_id)
        if response:
            st.session_state.latest_response_id=response["response_id"]
            st.session_state.profile.update({
                "city":response["city"],"commute":response["commute_mode"],"commute_km":response["commute_km_day"],
                "commute_days":response["commute_days_week"],"diet":response["diet_pattern"],"housing":response["housing_type"],
                "budget":response["monthly_budget_inr"],"electricity":response["electricity_kwh_month"],"ac":response["ac_usage"],
                "segregation":response["waste_segregation"],**response["preferences"]})
            st.session_state.questionnaire_saved=True
        st.session_state.db_profile_loaded=True
    if not st.session_state.get("db_latest_footprint_loaded", False):
        records=get_footprint_records(user_id,limit=1)
        if records:
            st.session_state.latest_footprint_record_id=records[0]["record_id"]
        else:
            st.session_state.pop("latest_footprint_record_id",None)
        st.session_state.db_latest_footprint_loaded=True
    if not st.session_state.get("db_goals_loaded", False):
        st.session_state.goals = [{"db_id":row["progress_id"], "title":row["goal_title"], "category":row["category"], "progress":row["progress_percent"]/100, "done":row["status"]=="completed"} for row in get_progress(user_id)]
        st.session_state.db_goals_loaded = True

def load_styles():
    st.markdown("""<style>
    .stApp{background:#f5f8f5;color:#17231d}
    [data-testid="stSidebar"]{background:#fff;border-right:1px solid #e5ece7}
    .card{background:#fff;border:1px solid #e5ece7;border-radius:16px;padding:1.2rem;min-height:120px}
    .label{font-size:.78rem;color:#718078;font-weight:700}
    .value{font-size:1.8rem;font-weight:800;color:#17231d;margin:.45rem 0}
    .green{color:#16734a;font-weight:700;font-size:.8rem}
    .tag{background:#e9f5ee;color:#16734a;border-radius:30px;padding:.25rem .6rem;font-size:.75rem;font-weight:700}
    </style>""", unsafe_allow_html=True)
