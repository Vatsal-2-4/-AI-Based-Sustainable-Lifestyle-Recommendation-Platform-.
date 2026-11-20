import streamlit as st
import json
from frontend.styles import DEFAULT_PROFILE
from database.repository import export_user_data, delete_user

def render():
    st.title("Profile")
    st.caption("Your saved lifestyle information and preferences.")
    p=st.session_state.profile
    st.markdown(f"### {p['name']}  ·  {p['city']}")
    st.caption(st.session_state.get("user_email","Demo profile"))
    a,b,c=st.columns(3)
    a.metric("Commute mode",p['commute']); b.metric("Housing",p['housing']); c.metric("Monthly budget",f"₹{p['budget']:,}")
    st.write(f"Diet: **{p['diet']}** · Electricity: **{p['electricity']} kWh/month** · Waste separation: **{p['segregation']}**")
    st.button("Edit lifestyle questionnaire",type="primary",on_click=lambda: _go_questionnaire())
    st.info("Your lifestyle responses, estimates, recommendations, and goals are stored in the local SQLite database on this computer.")
    st.subheader("Your data")
    try:
        bundle=export_user_data(st.session_state.user_id)
        st.download_button("Download my data (JSON)",data=json.dumps(bundle,ensure_ascii=False,indent=2),file_name="evergreen-data-export.json",mime="application/json",use_container_width=True)
    except Exception:
        st.error("Your data export is temporarily unavailable. Please try again.")
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
