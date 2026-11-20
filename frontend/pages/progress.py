import streamlit as st
import plotly.express as px
import pandas as pd
from database.repository import update_progress, delete_progress, get_footprint_records

def _save_slider(goal_index):
    goal=st.session_state.goals[goal_index]
    try:
        percent=st.session_state[f"progress_{goal_index}"]
        update_progress(st.session_state.user_id,goal["db_id"],progress_percent=percent)
        goal["progress"]=percent/100
    except Exception as exc:
        st.session_state["progress_error"]=str(exc)

def render():
    st.title("Progress tracking")
    st.caption("Build steady habits, one action at a time.")
    goals=st.session_state.goals
    active=sum(not g['done'] for g in goals); complete=sum(g['done'] for g in goals)
    a,b,c=st.columns(3)
    a.metric("Active goals",active); b.metric("Completed goals",complete); c.metric("Goals in progress",sum(g['progress']>0 and not g['done'] for g in goals))
    st.subheader("Your goals")
    if st.session_state.get("progress_error"):
        st.error(f"Progress could not be saved: {st.session_state.pop('progress_error')}")
    if not goals: st.info("No goals yet. Visit Recommendations and add an action to get started.")
    for i,goal in enumerate(goals):
        with st.container(border=True):
            a,b=st.columns([5,1])
            with a:
                st.markdown(f"**{goal['title']}** · {goal['category']}")
                if goal['done']: st.success("Completed")
                else:
                    goal['progress']=st.slider("Progress",0,100,int(goal['progress']*100),key=f"progress_{i}",on_change=_save_slider,args=(i,))/100
                    st.progress(goal['progress'])
            with b:
                if not goal['done'] and st.button("Complete",key=f"complete_{i}"):
                    try:
                        update_progress(st.session_state.user_id,goal["db_id"],progress_percent=100,status="completed")
                        goal['done']=True; goal['progress']=1.0; st.rerun()
                    except Exception as exc: st.error(f"Could not update goal: {exc}")
                if st.button("Remove",key=f"remove_{i}"):
                    try:
                        delete_progress(st.session_state.user_id,goal["db_id"])
                        st.session_state.goals.pop(i); st.rerun()
                    except Exception as exc: st.error(f"Could not remove goal: {exc}")
    st.subheader("Saved footprint estimates")
    records=get_footprint_records(st.session_state.user_id,limit=20)
    if len(records)<2:
        st.info("Save at least two footprint estimates to see a trend. Estimates use the factor set displayed on the Carbon footprint page.")
    else:
        history=pd.DataFrame([{"Saved":r["created_at"],"Estimated kg CO₂e/year":r["total_kg_co2e"]} for r in reversed(records)])
        fig=px.line(history,x="Saved",y="Estimated kg CO₂e/year",markers=True,color_discrete_sequence=["#278253"])
        fig.update_layout(margin=dict(t=15,b=0,l=0,r=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=300)
        st.plotly_chart(fig,use_container_width=True)
