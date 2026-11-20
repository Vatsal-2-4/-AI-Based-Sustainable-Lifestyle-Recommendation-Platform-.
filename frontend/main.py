import streamlit as st
from frontend.styles import load_styles, initialize_state
from frontend.pages import home, dashboard, calculator, recommendations, progress, questionnaire, profile, auth

PAGES = {
    "Home": home.render,
    "Dashboard": dashboard.render,
    "Questionnaire": questionnaire.render,
    "Recommendations": recommendations.render,
    "Carbon footprint": calculator.render,
    "Progress tracking": progress.render,
    "Profile": profile.render,
    "Login / Register": auth.render,
}

def run_app():
    load_styles()
    initialize_state()
    with st.sidebar:
        st.markdown('<div class="brand">🌿 evergreen<span>.</span></div>', unsafe_allow_html=True)
        st.caption("SUSTAINABLE LIVING PLATFORM")
        pages = list(PAGES)
        current = st.session_state.get("page", "Dashboard")
        if current not in PAGES:
            current = "Dashboard"
        page = st.radio("Navigation", pages, index=pages.index(current), label_visibility="collapsed", key="nav")
        st.session_state.page = page
        st.divider()
        st.caption("DEMO PROFILE")
        st.markdown(f"**{st.session_state.profile['name']}**")
        st.caption(f"{st.session_state.profile['city']}, India")
    PAGES[page]()
