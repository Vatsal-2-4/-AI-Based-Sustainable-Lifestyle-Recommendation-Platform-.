import streamlit as st

def load_styles():
    st.markdown("""<style>
    .stApp{background:#f5f8f5;color:#17231d}
    [data-testid="stSidebar"]{background:#fff;border-right:1px solid #e5ece7}
    .card{background:#fff;border:1px solid #e5ece7;border-radius:16px;padding:1.2rem;min-height:120px}
    .label{font-size:.78rem;color:#718078;font-weight:700}
    .value{font-size:1.8rem;font-weight:800;color:#17231d;margin:.45rem 0}
    .green{color:#16734a;font-weight:700;font-size:.8rem}
    .tag{background:#e9f5ee;color:#16734a;border-radius:30px;padding:.25rem .6rem;font-size:.75rem;font-weight:700}
    </style>""", unsafe_allow_html=True)
