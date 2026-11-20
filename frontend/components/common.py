import streamlit as st

def metric(label, value, foot):
    st.markdown(f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div><div class="green">{foot}</div></div>', unsafe_allow_html=True)

def page_header(title, subtitle):
    st.title(title)
    st.caption(subtitle)
