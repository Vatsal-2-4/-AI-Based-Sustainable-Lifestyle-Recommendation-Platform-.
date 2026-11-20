import streamlit as st
import logging
from frontend.styles import load_styles, initialize_state, DEFAULT_PROFILE
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
    try:
        initialize_state()
    except Exception:
        logging.exception("Could not initialize the application state or local database")
        st.error("The app could not load its local data. Check that the project folder is writable, then restart the app.")
        return
    pending=st.session_state.pop("pending_navigation",None)
    if pending in PAGES:
        st.session_state.page=pending
        st.session_state.nav=pending
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
        st.caption("ACCOUNT" if st.session_state.authenticated else "DEMO PROFILE")
        st.markdown(f"**{st.session_state.profile['name']}**")
        st.caption(f"{st.session_state.profile['city']}, India")
        if st.session_state.authenticated:
            st.button("Sign out", use_container_width=True, on_click=_sign_out)
        else:
            st.button("Create account / sign in", use_container_width=True, on_click=_go_to_account)
    try:
        PAGES[page]()
    except Exception:
        logging.exception("Page rendering failed: %s", page)
        st.error("This page could not load right now. Your saved data has not been changed; reload the page or restart the app.")

def _sign_out():
    st.session_state.authenticated=False
    st.session_state.user_email="demo@example.local"
    st.session_state.profile=DEFAULT_PROFILE.copy()
    st.session_state.goals=[]
    for key in list(st.session_state.keys()):
        if key.startswith("db_") or key in {"latest_response_id","latest_footprint_record_id","questionnaire_saved"}:
            st.session_state.pop(key,None)
    st.session_state.page="Home"
    st.session_state.nav="Home"

def _go_to_account():
    st.session_state.page="Login / Register"
    st.session_state.nav="Login / Register"
