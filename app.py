import streamlit as st
from frontend.main import run_app

st.set_page_config(page_title="Evergreen", page_icon="🌿", layout="wide")
run_app()
