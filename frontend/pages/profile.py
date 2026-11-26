import streamlit as st
import json
from frontend.styles import DEFAULT_PROFILE
from database.repository import export_user_data, backup_user_database, reset_demo_data, delete_user

def render():
    st.title("Profile")
    st.caption("Your saved lifestyle information and preferences.")
    if st.session_state.get("profile_reset_message"):
        st.success(st.session_state.pop("profile_reset_message"))
    p=st.session_state.profile
    st.markdown(f"### {p['name']}  ·  {p['city']}")
    st.caption(st.session_state.get("user_email","Demo profile"))
    a,b,c=st.columns(3)
    a.metric("Commute mode",p['commute']); b.metric("Housing",p['housing']); c.metric("Monthly budget",f"₹{p['budget']:,}")
    st.write(f"Diet: **{p['diet']}** · Electricity: **{p['electricity']} kWh/month** · Waste separation: **{p['segregation']}**")
    st.button("Edit lifestyle questionnaire",type="primary",on_click=lambda: _go_questionnaire())
    st.info("Your lifestyle responses, estimates, recommendations, and goals are stored in the local SQLite database on this computer.")
    st.subheader("Your data")
    st.caption("Choose JSON for a portable data copy, or SQLite for an account-only database backup. Password credentials are not included in either download.")
    data_cols=st.columns(2)
    try:
        bundle=export_user_data(st.session_state.user_id)
        data_cols[0].download_button("Download my data · JSON",data=json.dumps(bundle,ensure_ascii=False,indent=2),file_name="evergreen-data-export.json",mime="application/json",use_container_width=True)
    except Exception:
        st.error("Your data export is temporarily unavailable. Please try again.")
    try:
        backup=backup_user_database(st.session_state.user_id)
        data_cols[1].download_button("Download account backup · SQLite",data=backup,file_name=f"evergreen-account-{st.session_state.user_id}-backup.sqlite3",mime="application/x-sqlite3",use_container_width=True)
    except Exception:
        st.error("The account database backup is temporarily unavailable. Your JSON export may still be downloaded.")
    is_demo=(not st.session_state.get("authenticated",False) and st.session_state.get("user_email")=="demo@example.local")
    if is_demo:
        st.subheader("Reset demo data")
        st.warning("This clears the demo profile’s saved questionnaire answers, estimates, recommendations, and goals. It keeps the built-in demo profile and cannot be undone.")
        confirmed=st.checkbox("I understand this will permanently clear the demo profile’s saved data",key="confirm_reset_demo")
        if st.button("Reset demo data",disabled=not confirmed,use_container_width=True):
            try:
                reset_demo_data(st.session_state.user_id)
                uid=st.session_state.user_id
                st.session_state.profile=DEFAULT_PROFILE.copy()
                st.session_state.goals=[]
                st.session_state.pop("latest_response_id",None)
                st.session_state.pop("latest_footprint_record_id",None)
                st.session_state.pop("questionnaire_saved",None)
                for key in list(st.session_state.keys()):
                    if key.startswith((f"calc_{uid}_",f"profile_{uid}_",f"calculator_inputs_loaded_{uid}","progress_","dashboard_progress_")):
                        st.session_state.pop(key,None)
                st.session_state.db_profile_loaded=True
                st.session_state.db_latest_footprint_loaded=True
                st.session_state.db_goals_loaded=True
                st.session_state.profile_reset_message="Demo data reset. Your profile is ready to start again."
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("We could not reset the demo data. Check that the local database is writable and try again.")
    st.divider()
    st.subheader("Delete account and saved data")
    st.warning("This permanently removes this profile, questionnaire responses, estimates, recommendations, and goals from the local database.")
    confirmed=st.checkbox("I understand this cannot be undone",key="confirm_delete_account")
    if st.button("Delete account and data",type="secondary",disabled=not confirmed):
        try:
            delete_user(st.session_state.user_id)
            st.session_state.authenticated=False
            st.session_state.user_email="demo@example.local"
            st.session_state.profile={**DEFAULT_PROFILE}
            st.session_state.goals=[]
            for key in list(st.session_state.keys()):
                if key.startswith("db_") or key.startswith("calculator_inputs_loaded_") or key in {"latest_response_id","latest_footprint_record_id","questionnaire_saved"}:
                    st.session_state.pop(key,None)
            st.session_state.page="Home"; st.session_state.pending_navigation="Home"
            st.success("The account and associated data were deleted.")
            st.rerun()
        except Exception:
            st.error("We could not delete this data. Please try again or inspect the local database status.")

def _go_questionnaire():
    st.session_state.page="Questionnaire"; st.session_state.nav="Questionnaire"
