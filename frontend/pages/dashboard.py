import streamlit as st
import pandas as pd
from frontend.components.common import metric
from database.repository import get_footprint_records, get_recommendations

def render():
    st.markdown('<div style="background:linear-gradient(120deg,#123c2c,#238052);padding:2.5rem;border-radius:22px;color:white"><h1 style="color:white">Make everyday choices count.</h1><p>Understand your lifestyle footprint and find practical ways to live a little lighter.</p></div>', unsafe_allow_html=True)
    st.write("")
    uid=st.session_state.user_id
    goals=st.session_state.get("goals",[])
    records=get_footprint_records(uid,limit=1)
    recommendations=get_recommendations(uid,limit=3)
    cols=st.columns(4)
    latest=records[0] if records else None
    values=[("LATEST ESTIMATE",f"{latest['total_kg_co2e']:,.0f} kg" if latest else "Not calculated", "Partial annual CO₂e estimate" if latest else "Use Carbon footprint to start"),
            ("ACTIVE GOALS",str(sum(not g['done'] for g in goals)),"Saved actions in progress"),
            ("COMPLETED GOALS",str(sum(g['done'] for g in goals)),"Actions marked complete"),
            ("SAVED ACTIONS",str(len(recommendations)),"Personalized recommendations")]
    for col,args in zip(cols,values):
        with col: metric(*args)
    left,right=st.columns([1.5,1])
    with left:
        st.subheader("Your footprint breakdown")
        if latest:
            breakdown=latest["category_breakdown"]
            st.bar_chart(pd.DataFrame({"Estimated kg CO₂e/year":list(breakdown.values())},index=list(breakdown.keys())),color="#278253")
            st.caption(f"Saved {latest['created_at']} · factor set {latest['factor_version']}. This is a partial estimate.")
        else:
            st.info("No saved footprint estimate yet. Open Carbon footprint to calculate and save one.")
    with right:
        st.subheader("Your next best steps")
        if recommendations:
            for row in recommendations:
                st.markdown(f"**{row['title']}** · {row['category']}")
        else:
            st.info("Complete your lifestyle questionnaire, then open Recommendations to find actions matched to your profile.")
        st.caption("No emissions savings or sustainability score are shown because the project does not yet calculate those reliably.")
