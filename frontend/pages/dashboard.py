import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.components.common import metric
from database.repository import get_footprint_records, get_recommendations, update_progress


def _navigate(page):
    st.session_state.page=page
    st.session_state.nav=page


def _save_goal_progress(goal_id):
    key=f"dashboard_progress_{goal_id}"
    goal=next((item for item in st.session_state.goals if item["db_id"]==goal_id),None)
    if not goal: return
    percent=st.session_state[key]
    try:
        update_progress(st.session_state.user_id,goal_id,progress_percent=percent)
        goal["progress"]=percent/100
    except ValueError as exc:
        st.session_state["dashboard_error"]=str(exc)
    except Exception:
        st.session_state["dashboard_error"]="Could not save goal progress. Try again from Progress tracking."


def _complete_goal(goal_id):
    goal=next((item for item in st.session_state.goals if item["db_id"]==goal_id),None)
    if not goal: return
    try:
        update_progress(st.session_state.user_id,goal_id,progress_percent=100,status="completed")
        goal["progress"]=1.0
        goal["status"]="completed"
        goal["done"]=True
        st.session_state["dashboard_message"]="Goal marked complete. Nice work following through."
    except ValueError as exc:
        st.session_state["dashboard_error"]=str(exc)
    except Exception:
        st.session_state["dashboard_error"]="Could not complete this goal. Try again from Progress tracking."


def _estimate_label(records, record_id):
    row=next(item for item in records if item["record_id"]==record_id)
    return f"{row['created_at']} · {row['total_kg_co2e']:,.1f} kg CO₂e · {row['factor_version']}"


def render():
    st.title(f"Welcome back, {st.session_state.profile['name']}")
    st.caption("Explore your saved estimates, goals, and next steps.")
    if st.session_state.get("dashboard_error"):
        st.error(st.session_state.pop("dashboard_error"))
    if st.session_state.get("dashboard_message"):
        st.success(st.session_state.pop("dashboard_message"))
    uid=st.session_state.user_id
    goals=st.session_state.get("goals",[])
    try:
        records=get_footprint_records(uid,limit=50)
        recommendations=get_recommendations(uid,limit=50)
    except Exception:
        st.error("We could not load your saved dashboard data. Check the local database and reload this page.")
        return
    saved_actions=[row for row in recommendations if row["status"]=="saved"]
    active=sum(g.get("status","completed" if g["done"] else "active")=="active" for g in goals)
    complete=sum(g["done"] for g in goals)
    summary=st.columns(4)
    summary_data=[("LATEST ESTIMATE",f"{records[0]['total_kg_co2e']:,.0f} kg" if records else "Not calculated","Partial annual estimate" if records else "Calculate your first estimate"),
                  ("ACTIVE GOALS",str(active),"Actions in progress"),
                  ("COMPLETED GOALS",str(complete),"Actions you have finished"),
                  ("SAVED ACTIONS",str(len(saved_actions)),"From your recommendations")]
    for col,args in zip(summary,summary_data):
        with col: metric(*args)

    overview,goal_tab,history_tab=st.tabs(["Overview","My goals","Estimate history"])
    with overview:
        if not records:
            st.info("Your dashboard will show saved results here. Start by entering activity amounts in the footprint calculator.")
            st.button("Open carbon footprint calculator →",type="primary",on_click=_navigate,args=("Carbon footprint",))
        else:
            selected_id=st.selectbox("Choose a saved estimate",[r["record_id"] for r in records],format_func=lambda rid:_estimate_label(records,rid),key=f"dashboard_estimate_{uid}")
            selected=next(r for r in records if r["record_id"]==selected_id)
            breakdown=selected["category_breakdown"]
            categories=["All categories",*breakdown.keys()]
            category=st.selectbox("Explore a category",categories,key=f"dashboard_category_{uid}_{selected_id}")
            shown={category:breakdown[category]} if category!="All categories" else breakdown
            left,right=st.columns([1.5,1])
            with left:
                chart=pd.DataFrame({"Estimated kg CO₂e/year":list(shown.values())},index=list(shown.keys()))
                st.bar_chart(chart,color="#278253",height=340)
                st.caption(f"Estimate saved {selected['created_at']} · factor set {selected['factor_version']} · partial scope")
            with right:
                if category=="All categories":
                    st.metric("Included emissions",f"{selected['total_kg_co2e']:,.1f} kg CO₂e/year")
                    st.write("Choose a category to inspect its contribution and scope note.")
                else:
                    value=breakdown[category]
                    share=value/selected["total_kg_co2e"] if selected["total_kg_co2e"] else 0
                    st.metric(f"{category} estimate",f"{value:,.1f} kg CO₂e/year",f"{share:.1%} of included total")
                    explanations={"Transportation":"Direct petrol/diesel combustion only. Public transit, vehicle manufacture, fuel production, and non-CO₂ gases are excluded.","Electricity":"India grid-average estimate. The user's state and time-of-day electricity mix may differ.","Food":"Global product life-cycle averages; local source and production methods may differ."}
                    st.info(explanations.get(category,"This estimate includes only the activity inputs and factors shown on Carbon footprint."))
            snapshot=selected.get("input_snapshot",{})
            if snapshot.get("schema_version")==1:
                resource_a,resource_b=st.columns(2)
                water=snapshot.get("water_l_person_day",0)*365
                waste=sum(snapshot.get("waste_kg_week",{}).values())*52
                resource_a.metric("Water entered",f"{water:,.0f} L/person/year")
                resource_b.metric("Waste entered",f"{waste:,.1f} kg/year")
                st.caption("Water and waste are separate resource indicators; they are not included in the CO₂e total.")
            else:
                st.caption("This older estimate does not contain the activity inputs needed to show water and waste indicators here.")
            st.button("Review or update activity inputs →",on_click=_navigate,args=("Carbon footprint",))

    with goal_tab:
        st.subheader("Your active goals")
        active_goals=[g for g in goals if not g["done"]]
        if not active_goals:
            st.info("No active goals yet. Choose an action that fits your routine.")
            st.button("Explore recommendations →",type="primary",on_click=_navigate,args=("Recommendations",))
        else:
            for goal in active_goals[:5]:
                with st.container(border=True):
                    st.markdown(f"**{goal['title']}** · {goal['category']}")
                    if goal.get("status")=="paused":
                        st.caption("This goal is paused. Resume it from Progress tracking when ready.")
                    else:
                        key=f"dashboard_progress_{goal['db_id']}"
                        st.slider("Progress",0,100,int(goal["progress"]*100),key=key,on_change=_save_goal_progress,args=(goal["db_id"],))
                    if st.button("Mark complete",key=f"dashboard_complete_{goal['db_id']}",on_click=_complete_goal,args=(goal["db_id"],)):
                        pass
            st.button("Manage all goals →",on_click=_navigate,args=("Progress tracking",))
        if len(active_goals)>5: st.caption(f"Showing 5 of {len(active_goals)} active goals.")

    with history_tab:
        st.subheader("Estimate history")
        if not records:
            st.info("Saved estimates will appear here after you calculate and save one.")
        else:
            version=records[0]["factor_version"]
            compatible=[r for r in reversed(records) if r["factor_version"]==version and r["input_snapshot"].get("schema_version")==1]
            if len(compatible)>=2:
                frame=pd.DataFrame([{"Saved":f"{r['created_at']} · #{r['record_id']}","Estimated kg CO₂e/year":r["total_kg_co2e"]} for r in compatible])
                fig=px.line(frame,x="Saved",y="Estimated kg CO₂e/year",markers=True,color_discrete_sequence=["#278253"],hover_data={"Estimated kg CO₂e/year":":,.1f"})
                fig.update_layout(margin=dict(t=15,b=0,l=0,r=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=320)
                st.plotly_chart(fig,use_container_width=True)
                if len(compatible)<len(records): st.caption(f"Showing estimates compatible with factor set {version}. Other records use different factors or do not have saved input details.")
            else:
                st.info("Save two estimates with the same factor set and input format to compare a trend.")
            st.dataframe([{"Saved":r["created_at"],"Total kg CO₂e/year":r["total_kg_co2e"],"Factor set":r["factor_version"],"Inputs":"Available" if r["input_snapshot"].get("schema_version")==1 else "Older record"} for r in records],hide_index=True,use_container_width=True)
            st.button("Calculate another estimate →",on_click=_navigate,args=("Carbon footprint",))
    st.caption("No sustainability score or action savings are displayed because the app does not calculate those reliably yet.")
