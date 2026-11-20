import streamlit as st
from database.repository import create_user, get_user_by_email

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
            password=st.text_input("Password",type="password")
            submitted=st.form_submit_button(mode,type="primary",use_container_width=True)
        if submitted:
            if not email or not password: st.error("Enter an email and password to continue.")
            else:
                try:
                    if mode=="Create account":
                        user_id=create_user(email,name)
                        user={"user_id":user_id,"email":email,"display_name":name}
                    else:
                        user=get_user_by_email(email)
                        if not user: raise ValueError("No demo account exists for this email. Choose Create account first.")
                    st.session_state.user_id=user["user_id"]
                    st.session_state.user_email=user["email"]
                    st.session_state.profile['name']=user['display_name']
                    st.session_state.db_goals_loaded=False
                    st.session_state.authenticated=True
                    st.session_state.page="Dashboard"; st.session_state.nav="Dashboard"
                    st.rerun()
                except ValueError as exc: st.error(str(exc))
                except Exception as exc: st.error(f"Could not save account to SQLite: {exc}")
        st.caption("Demo accounts store email and display name only. Passwords are not persisted; this is not production authentication.")
