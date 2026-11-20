import streamlit as st
import pandas as pd
from frontend.components.common import metric

def render():
    st.markdown('<div style="background:linear-gradient(120deg,#123c2c,#238052);padding:2.5rem;border-radius:22px;color:white"><h1 style="color:white">Make everyday choices count.</h1><p>Understand your lifestyle footprint and find practical ways to live a little lighter.</p></div>', unsafe_allow_html=True)
    st.write("")
    cols=st.columns(4)
    for c, args in zip(cols, [("ANNUAL FOOTPRINT","4.8 t","↓ 8% since last check-in"),("SUSTAINABILITY SCORE","72 / 100","↑ 6 points this month"),("ACTIVE GOALS","3 goals","1 completed this month"),("POTENTIAL SAVINGS","1.2 t","Across your top actions")]):
        with c: metric(*args)
    left,right=st.columns([1.5,1])
    with left:
        st.subheader("Your footprint breakdown")
        st.bar_chart(pd.DataFrame({"Annual footprint (t CO₂e)":[2.1,1.2,.9,.4,.2]},index=["Transport","Home energy","Food","Shopping","Waste"]),color="#278253")
    with right:
        st.subheader("Your sustainability score")
        st.markdown('<div class="card" style="text-align:center"><div class="value" style="font-size:3rem;color:#16734a">72</div><span class="tag">GOOD MOMENTUM</span><p>Build meaningful habits with a few focused changes.</p></div>',unsafe_allow_html=True)
    st.subheader("Your next best steps")
    for c,(title,impact) in zip(st.columns(3),[("Take metro twice a week","~320 kg CO₂e saved/year"),("Try plant-based dinners","~180 kg CO₂e saved/year"),("Set AC to 25°C","~140 kg CO₂e saved/year")]):
        with c: st.markdown(f'<div class="card"><span class="tag">PERSONALIZED ACTION</span><h3>{title}</h3><b>{impact}</b></div>',unsafe_allow_html=True)
