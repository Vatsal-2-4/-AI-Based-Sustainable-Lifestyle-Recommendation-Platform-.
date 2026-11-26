import streamlit as st
from database.repository import create_user, authenticate_user
from frontend.styles import DEFAULT_PROFILE

def render():
    st.title("Create your account" if not st.session_state.authenticated else "Welcome back")
    st.caption("Your sustainable living companion for everyday decisions.")
    left,right=st.columns([1.1,1])
    with left: st.markdown('<div class="hero"><div class="eyebrow" style="color:#c7ebd2">WELCOME TO EVERGREEN</div><h1>Better habits start with a clearer picture.</h1><p>Your footprint and recommendations, shaped around your lifestyle.</p></div>',unsafe_allow_html=True)
    with right:
        mode=st.radio("Account",["Sign in","Create account"],horizontal=True)
        with st.form("account_form"):
            if mode=="Create account": name=st.text_input("Full name",value=st.session_state.profile['name'])
            email=st.text_input("Email address",placeholder="you@example.com")
            password=st.text_input("Password",type="password",help="Use at least 12 characters when creating an account.")
            confirm=st.text_input("Confirm password",type="password") if mode=="Create account" else None
            submitted=st.form_submit_button(mode,type="primary",use_container_width=True)
        if submitted:
            if not email.strip(): st.error("Enter your email address to continue.")
            elif mode=="Create account" and not name.strip(): st.error("Enter your name to create an account.")
            elif not password: st.error("Enter your password to continue.")
            elif mode=="Create account" and len(password)<12: st.error("Choose a password with at least 12 characters.")
            elif mode=="Create account" and password!=confirm: st.error("Passwords do not match.")
            else:
                try:
                    if mode=="Create account":
                        user_id=create_user(email.strip(),name.strip(),password)
                        user={"user_id":user_id,"email":email.strip(),"display_name":name.strip()}
                    else:
                        user=authenticate_user(email.strip(),password)
                        if not user: raise ValueError("Email or password is incorrect.")
                    # Replace the previous account's in-memory profile and cached record IDs.
                    st.session_state.profile={**DEFAULT_PROFILE,"name":user["display_name"]}
                    for key in ("latest_response_id","latest_footprint_record_id","questionnaire_saved","db_profile_loaded","db_latest_footprint_loaded","db_goals_loaded","goals"):
                        st.session_state.pop(key,None)
                    st.session_state.user_id=user["user_id"]
                    st.session_state.user_email=user["email"]
                    st.session_state.authenticated=True
                    destination="Questionnaire" if mode=="Create account" else "Dashboard"
                    st.session_state.page=destination
                    st.session_state.pending_navigation=destination
                    st.rerun()
                except ValueError as exc: st.error(str(exc))
                except Exception: st.error("The account service is temporarily unavailable. Please try again.")
        st.caption("Passwords are stored as salted PBKDF2 hashes. Account recovery is not available in this prototype. Accounts created before password sign-in need a new email address.")
