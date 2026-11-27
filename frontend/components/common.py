import streamlit as st

def metric(label, value, foot, variant="forest"):
    variants={"forest","leaf","water","sun"}
    color=variant if variant in variants else "forest"
    st.markdown(f'<div class="card metric-card {color}"><div class="label">{label}</div><div class="value">{value}</div><div class="green">{foot}</div></div>', unsafe_allow_html=True)

def page_header(title, subtitle):
    st.title(title)
    st.caption(subtitle)
