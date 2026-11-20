import streamlit as st
from frontend.styles import load_styles
from frontend.pages import dashboard, calculator, recommendations, progress, questionnaire, profile, auth

PAGES = {
    "Overview": dashboard.render,
    "Carbon calculator": calculator.render,
    "Recommendations": recommendations.render,
    "Progress": progress.render,
    "Lifestyle questionnaire": questionnaire.render,
    "Profile": profile.render,
    "Sign in / Register": auth.render,
}

def run_app():
    load_styles()
    with st.sidebar:
        st.markdown("## 🌿 evergreen")
        st.caption("SUSTAINABLE LIVING PLATFORM")
        page = st.radio("Navigation", list(PAGES), label_visibility="collapsed")
        st.divider()
        st.caption("DEMO PROFILE · Bengaluru, IN")
    PAGES[page]()
