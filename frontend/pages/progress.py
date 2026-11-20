import streamlit as st
import plotly.express as px
import pandas as pd

def render():
    st.title("Progress tracking")
    st.caption("Build steady habits, one action at a time.")
    goals=st.session_state.goals
    active=sum(not g['done'] for g in goals); complete=sum(g['done'] for g in goals)
    a,b,c=st.columns(3)
    a.metric("Active goals",active); b.metric("Completed goals",complete); c.metric("Estimated savings started",f"{sum(600 if g['category']=='Transport' else 150 for g in goals if g['progress']>0):,} kg")
    st.subheader("Your goals")
    if not goals: st.info("No goals yet. Visit Recommendations and add an action to get started.")
    for i,goal in enumerate(goals):
        with st.container(border=True):
            a,b=st.columns([5,1])
            with a:
                st.markdown(f"**{goal['title']}** · {goal['category']}")
                if goal['done']: st.success("Completed")
                else:
                    goal['progress']=st.slider("Progress",0,100,int(goal['progress']*100),key=f"progress_{i}")/100
                    st.progress(goal['progress'])
            with b:
                if not goal['done'] and st.button("Complete",key=f"complete_{i}"): goal['done']=True; goal['progress']=1.0; st.rerun()
    st.subheader("Footprint trend")
    df=pd.DataFrame({"Estimated footprint (t CO₂e)":[5.5,5.3,5.15,4.95,4.8]},index=["Jun","Jul","Aug","Sep","Oct"])
    fig=px.area(df,y="Estimated footprint (t CO₂e)",markers=True,color_discrete_sequence=["#278253"])
    fig.update_layout(margin=dict(t=15,b=0,l=0,r=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=300)
    st.plotly_chart(fig,use_container_width=True)
