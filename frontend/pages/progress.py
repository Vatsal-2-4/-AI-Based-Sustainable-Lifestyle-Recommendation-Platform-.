import streamlit as st
import plotly.express as px
import pandas as pd
from database.repository import update_progress, delete_progress, get_footprint_records


def _save_slider(goal_index):
    goal=st.session_state.goals[goal_index]
    try:
        percent=st.session_state[f"progress_{goal['db_id']}"]
        update_progress(st.session_state.user_id,goal["db_id"],progress_percent=percent)
        goal["progress"]=percent/100
    except ValueError as exc:
        st.session_state["progress_error"]=str(exc)
    except Exception:
        st.session_state["progress_error"]="Could not save progress. Check the local database and try again."


def _set_goal_status(goal_index,status):
    goal=st.session_state.goals[goal_index]
    try:
        if status=="completed":
            update_progress(st.session_state.user_id,goal["db_id"],progress_percent=100,status=status)
        else:
            update_progress(st.session_state.user_id,goal["db_id"],status=status)
        goal["status"]=status
        if status=="completed":
            goal["done"]=True
            goal["progress"]=1.0
    except ValueError as exc:
        st.session_state["progress_error"]=str(exc)
    except Exception:
        st.session_state["progress_error"]="Could not update this goal. Please retry."


def _request_remove(progress_id):
    st.session_state["confirm_remove_goal_id"]=progress_id


def _cancel_remove():
    st.session_state.pop("confirm_remove_goal_id",None)


def _confirm_remove(goal_index):
    goal=st.session_state.goals[goal_index]
    try:
        delete_progress(st.session_state.user_id,goal["db_id"])
        st.session_state.goals.pop(goal_index)
        st.session_state.pop("confirm_remove_goal_id",None)
        st.session_state["progress_success"]="Goal removed."
    except ValueError as exc:
        st.session_state["progress_error"]=str(exc)
    except Exception:
        st.session_state["progress_error"]="Could not remove this goal. Please retry."


def render():
    st.title("Progress tracking")
    st.caption("Build steady habits, one action at a time.")
    goals=st.session_state.goals
    active=sum(g.get("status","completed" if g["done"] else "active")=="active" for g in goals)
    complete=sum(g["done"] for g in goals)
    in_progress=sum(g["progress"]>0 and not g["done"] for g in goals)
    paused=sum(g.get("status")=="paused" for g in goals)
    a,b,c,d=st.columns(4)
    a.metric("Active goals",active); b.metric("Paused goals",paused); c.metric("Completed goals",complete); d.metric("Goals in progress",in_progress)
    st.subheader("Your goals")
    if st.session_state.get("progress_error"):
        st.error(st.session_state.pop("progress_error"))
    if st.session_state.get("progress_success"):
        st.success(st.session_state.pop("progress_success"))
    if not goals:
        st.info("No goals yet. Visit Recommendations and add an action to get started.")
    for i,goal in enumerate(goals):
        status=goal.get("status","completed" if goal["done"] else "active")
        with st.container(border=True):
            st.markdown(f"**{goal['title']}** · {goal['category']}")
            if status=="completed":
                st.success("Completed")
            elif status=="paused":
                st.warning("Paused · Resume when you are ready")
            else:
                goal["progress"]=st.slider("Progress",0,100,int(goal["progress"]*100),key=f"progress_{goal['db_id']}",on_change=_save_slider,args=(i,))/100
                st.progress(goal["progress"])
            action_cols=st.columns([1,1,1])
            if status!="completed":
                target="active" if status=="paused" else "paused"
                action_cols[0].button("Resume" if status=="paused" else "Pause",key=f"status_{goal['db_id']}",on_click=_set_goal_status,args=(i,target),use_container_width=True)
                action_cols[1].button("Mark complete",key=f"complete_{goal['db_id']}",on_click=_set_goal_status,args=(i,"completed"),use_container_width=True)
            action_cols[2].button("Remove",key=f"remove_{goal['db_id']}",on_click=_request_remove,args=(goal["db_id"],),use_container_width=True)
            if st.session_state.get("confirm_remove_goal_id")==goal["db_id"]:
                st.warning("Remove this goal and its saved progress?")
                confirm_cols=st.columns(2)
                confirm_cols[0].button("Confirm removal",key=f"confirm_remove_{goal['db_id']}",on_click=_confirm_remove,args=(i,),type="primary",use_container_width=True)
                confirm_cols[1].button("Keep goal",key=f"cancel_remove_{goal['db_id']}",on_click=_cancel_remove,use_container_width=True)
    st.subheader("Saved footprint estimates")
    records=get_footprint_records(st.session_state.user_id,limit=20)
    if records:
        current_version=records[0]["factor_version"]
        comparable=[r for r in reversed(records) if r["factor_version"]==current_version and r["input_snapshot"].get("schema_version")==1]
    else:
        current_version=None; comparable=[]
    if len(comparable)<2:
        if any(r["factor_version"]!=current_version or r["input_snapshot"].get("schema_version")!=1 for r in records):
            st.info("A trend needs at least two estimates with the same factor set and saved input format. Older or differently versioned estimates remain available on Carbon footprint.")
        else:
            st.info("Save at least two estimates with the same factor set to see a trend. Estimates use the activity fields shown on Carbon footprint.")
    else:
        history=pd.DataFrame([{"Saved":f"{r['created_at']} · #{r['record_id']}","Estimated kg CO₂e/year":r["total_kg_co2e"]} for r in comparable])
        fig=px.line(history,x="Saved",y="Estimated kg CO₂e/year",markers=True,color_discrete_sequence=["#278253"])
        fig.update_layout(margin=dict(t=15,b=0,l=0,r=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=300)
        st.plotly_chart(fig,use_container_width=True)
        if len(comparable)<len(records): st.caption(f"Showing {len(comparable)} compatible estimates using factor set {current_version}; other records use different or unavailable input metadata.")
