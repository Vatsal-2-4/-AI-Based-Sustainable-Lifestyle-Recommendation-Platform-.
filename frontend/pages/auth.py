import streamlit as st

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
                st.session_state.authenticated=True
                if mode=="Create account": st.session_state.profile['name']=name
                st.success("Signed in for this demo session.")
                st.session_state.page="Dashboard"; st.rerun()
        st.caption("Demo authentication only. No credentials are stored or sent to a server.")
