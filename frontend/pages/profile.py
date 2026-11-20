import streamlit as st

def render():
    st.title("Profile")
    st.caption("Your saved demo lifestyle information and preferences.")
    p=st.session_state.profile
    st.markdown(f"### {p['name']}  ·  {p['city']}")
    a,b,c=st.columns(3)
    a.metric("Commute mode",p['commute']); b.metric("Housing",p['housing']); c.metric("Monthly budget",f"₹{p['budget']:,}")
    st.write(f"Diet: **{p['diet']}** · Electricity: **{p['electricity']} kWh/month** · Waste separation: **{p['segregation']}**")
    st.button("Edit lifestyle questionnaire",type="primary",on_click=lambda: _go_questionnaire())
    st.info("Sample profile is held in Streamlit session state. Add persistent storage and privacy controls before production use.")

def _go_questionnaire():
    st.session_state.page="Questionnaire"; st.session_state.nav="Questionnaire"
