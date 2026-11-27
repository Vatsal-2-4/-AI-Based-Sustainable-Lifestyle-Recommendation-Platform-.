import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.components.common import metric
from backend.services.recommendation_service import recommend_for_profile
from database.repository import (
    get_footprint_records,
    get_recommendations,
    get_progress,
    update_progress,
)


def _navigate(page):
    st.session_state.page=page
    st.session_state.nav=page

def _render_first_steps(records, goals, saved_actions):
    steps=[
        {"title":"Build your profile","detail":"Share your commute, home, and everyday habits.","page":"Questionnaire","done":bool(st.session_state.get("questionnaire_saved",False)),"done_label":"Profile saved"},
        {"title":"Estimate your footprint","detail":"Enter activity amounts and review the factor notes.","page":"Carbon footprint","done":bool(records),"done_label":"Estimate saved"},
        {"title":"Choose a first action","detail":"Save one matched recommendation as a goal.","page":"Recommendations","done":bool(saved_actions or any(g.get("recommendation_id") or g.get("action_key") for g in goals)),"done_label":"Action saved"},
    ]
    next_step=next((step for step in steps if not step["done"]),None)
    if not next_step:
        return
    completed=sum(step["done"] for step in steps)
    with st.container(border=True):
        heading,progress_col=st.columns([2,1])
        with heading:
            st.markdown("### A simple path to your first action")
            st.caption("Three short steps turn your everyday habits into a useful next move. You can change your answers later.")
        with progress_col:
            st.progress(completed/len(steps),text=f"{completed} of {len(steps)} steps complete")
        step_cols=st.columns(3)
        for index,(col,step) in enumerate(zip(step_cols,steps),1):
            with col:
                state="Complete" if step["done"] else f"Step {index}"
                st.markdown(f"**{state}**")
                st.markdown(f"**{step['title']}**")
                st.caption(step["done_label"] if step["done"] else step["detail"])
                button_label="Review" if step["done"] else "Open step"
                st.button(button_label,key=f"onboarding_step_{index}",on_click=_navigate,args=(step["page"],),use_container_width=True)
        st.button(f"Continue · {next_step['title']} →",key="onboarding_continue",type="primary",on_click=_navigate,args=(next_step["page"],))


def _goal_by_id(goal_id):
    return next((goal for goal in st.session_state.goals if goal["db_id"]==goal_id),None)


def _save_goal_progress(goal_id):
    goal=_goal_by_id(goal_id)
    if not goal: return
    try:
        percent=st.session_state[f"dashboard_progress_{goal_id}"]
        update_progress(st.session_state.user_id,goal_id,progress_percent=percent)
        goal["progress"]=percent/100
        st.session_state["dashboard_message"]="Goal progress saved."
    except ValueError as exc:
        st.session_state["dashboard_error"]=str(exc)
    except Exception:
        st.session_state["dashboard_error"]="Could not save goal progress. Try again from Progress tracking."


def _set_goal_status(goal_id,status):
    goal=_goal_by_id(goal_id)
    if not goal: return
    try:
        if status=="completed":
            update_progress(st.session_state.user_id,goal_id,progress_percent=100,status=status)
            goal["progress"]=1.0
            goal["done"]=True
            message="Goal marked complete. Nice work following through."
        else:
            update_progress(st.session_state.user_id,goal_id,status=status)
            message="Goal resumed." if status=="active" else "Goal paused. You can resume it any time."
        goal["status"]=status
        st.session_state["dashboard_message"]=message
    except ValueError as exc:
        st.session_state["dashboard_error"]=str(exc)
    except Exception:
        st.session_state["dashboard_error"]="Could not update this goal. Try again from Progress tracking."


def _estimate_label(records,record_id):
    row=next(item for item in records if item["record_id"]==record_id)
    return f"{row['created_at']} · {row['total_kg_co2e']:,.1f} kg CO₂e · {row['factor_version']}"


def _compatible_history(records,version=None):
    if not records: return []
    selected_version=version or records[0]["factor_version"]
    return [record for record in reversed(records)
            if record["factor_version"]==selected_version
            and record.get("input_snapshot",{}).get("schema_version")==1]


def _previous_compatible(records,selected):
    older=[record for record in _compatible_history(records,selected["factor_version"])
           if record["record_id"]<selected["record_id"]]
    return older[-1] if older else None


def _recent_activity(records,progress_rows,recommendations):
    events=[]
    for row in records[:4]:
        events.append((row["created_at"],"Footprint estimate saved",f"{row['total_kg_co2e']:,.1f} kg CO₂e · {row['factor_version']}"))
    for row in progress_rows[:5]:
        events.append((row["updated_at"],"Goal "+row["status"],row["goal_title"]))
    for row in recommendations:
        if row["status"]=="saved":
            events.append((row["created_at"],"Action saved",row["title"]))
    return sorted(events,key=lambda event:event[0],reverse=True)[:6]


def _category_chart(breakdown,selected_category):
    values=breakdown if selected_category=="All categories" else {selected_category:breakdown[selected_category]}
    total=sum(breakdown.values())
    frame=pd.DataFrame([
        {"Category":category,"Estimated kg CO₂e/year":value,"Share of included total":value/total if total else 0}
        for category,value in values.items()
    ])
    fig=px.bar(frame,x="Estimated kg CO₂e/year",y="Category",orientation="h",color="Category",
               color_discrete_map={"Transportation":"#397b4e","Electricity":"#9aa83f","Food":"#c58245"},
               hover_data={"Share of included total":":.1%","Estimated kg CO₂e/year":":,.1f"})
    fig.update_layout(showlegend=False,template="plotly_white",paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=12,b=8,l=0,r=12),height=300,
                      font_color="#56645a",xaxis_title="Estimated kg CO₂e per year",yaxis_title="",
                      xaxis=dict(showgrid=True,gridcolor="#e3e9e1",zerolinecolor="#d4ddd2"),yaxis=dict(showgrid=False))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})


def _estimate_insights(records,selected):
    breakdown=selected["category_breakdown"]
    top_category,top_value=max(breakdown.items(),key=lambda item:item[1]) if breakdown and any(breakdown.values()) else ("No activity entered",0)
    total=selected["total_kg_co2e"]
    share=(top_value/total) if total else 0
    previous=_previous_compatible(records,selected)
    a,b,c=st.columns(3)
    a.metric("Largest included category",top_category,f"{share:.0%} of included estimate" if total else "No emissions entered")
    b.metric("Daily average",f"{total/365:,.2f} kg","Included categories only")
    if previous:
        difference=total-previous["total_kg_co2e"]
        c.metric("Change vs previous comparable",f"{difference:+,.1f} kg",f"Since {previous['created_at']}",delta_color="off")
    else:
        c.metric("Estimate saved",selected["created_at"],"No compatible earlier estimate")


def render():
    st.markdown("<div class='page-kicker'>Your overview</div>",unsafe_allow_html=True)
    st.title("Your sustainability dashboard")
    st.caption("A clear view of your saved estimates, habits, and next steps.")
    if st.session_state.get("dashboard_error"):
        st.error(st.session_state.pop("dashboard_error"))
    if st.session_state.get("dashboard_message"):
        st.success(st.session_state.pop("dashboard_message"))
    uid=st.session_state.user_id
    goals=st.session_state.get("goals",[])
    try:
        records=get_footprint_records(uid,limit=50)
        recommendations=get_recommendations(uid,limit=50)
        progress_rows=get_progress(uid)
    except Exception:
        st.error("We could not load your saved dashboard data. Check the local database and reload this page.")
        return
    try:
        suggested_actions=recommend_for_profile(st.session_state.profile,top_n=3)
    except Exception:
        suggested_actions=[]

    saved_actions=[row for row in recommendations if row["status"]=="saved"]
    _render_first_steps(records,goals,saved_actions)
    active=sum(g.get("status","completed" if g["done"] else "active")=="active" for g in goals)
    paused=sum(g.get("status")=="paused" for g in goals)
    completed=sum(g["done"] for g in goals)
    done_ratio=(completed/len(goals)) if goals else 0
    summary=st.columns(4)
    summary_data=[("Latest estimate",f"{records[0]['total_kg_co2e']:,.0f} kg" if records else "Not calculated","Partial annual estimate" if records else "Start with activity you know"),
                  ("Active goals",str(active),"Actions in progress"),
                  ("Paused goals",str(paused),"Ready when you are"),
                  ("Goal completion",f"{done_ratio:.0%}" if goals else "—",f"{completed} of {len(goals)} goals completed" if goals else "Save an action to begin")]
    variants=("forest","leaf","water","sun")
    for col,args,variant in zip(summary,summary_data,variants):
        with col: metric(*args,variant=variant)

    quick_cols=st.columns(3)
    quick_cols[0].button("Update my profile",key="dash_profile",on_click=_navigate,args=("Questionnaire",),use_container_width=True)
    quick_cols[1].button("Calculate footprint",key="dash_calculator",on_click=_navigate,args=("Carbon footprint",),use_container_width=True)
    quick_cols[2].button("Explore actions",key="dash_recommendations",on_click=_navigate,args=("Recommendations",),use_container_width=True)

    overview,goal_tab,history_tab=st.tabs(["Overview","Goals and habits","Estimate history"])
    with overview:
        if not records:
            left,right=st.columns([1.2,1])
            with left:
                st.subheader("Your footprint story starts here")
                st.write("Enter activity amounts you know to see an estimate by category. You can save multiple estimates and compare compatible records over time.")
                st.button("Create your first estimate →",key="dash_empty_calculator",type="primary",on_click=_navigate,args=("Carbon footprint",))
            with right:
                st.markdown("""
                <div class="card dashboard-empty-card"><span class="tag">A simple first step</span>
                <h3>Start with the details you have</h3>
                <p>Fuel, electricity, and food are included when supported factors are available. Water and waste stay as separate resource indicators.</p></div>
                """,unsafe_allow_html=True)
        else:
            selected_id=st.selectbox("Choose an estimate to explore",[r["record_id"] for r in records],
                                     format_func=lambda rid:_estimate_label(records,rid),key=f"dashboard_estimate_{uid}")
            selected=next(record for record in records if record["record_id"]==selected_id)
            breakdown=selected["category_breakdown"]
            category=st.selectbox("Focus on a category",["All categories",*breakdown.keys()],
                                  key=f"dashboard_category_{uid}_{selected_id}")
            chart_col,insights_col=st.columns([1.35,1],gap="large")
            with chart_col:
                st.subheader("Where your included estimate comes from")
                _category_chart(breakdown,category)
                st.caption(f"Saved {selected['created_at']} · factor set {selected['factor_version']} · partial estimate")
            with insights_col:
                st.subheader("At a glance")
                _estimate_insights(records,selected)
                st.info("A difference between estimates is a change in the calculation result, not proof of an emissions reduction. Compare similar inputs and factor sets.")

            snapshot=selected.get("input_snapshot",{})
            if snapshot.get("schema_version")==1:
                water=snapshot.get("water_l_person_day",0)*365
                waste=sum(snapshot.get("waste_kg_week",{}).values())*52
                resource_a,resource_b=st.columns([1,1])
                resource_a.metric("Water entered",f"{water:,.0f} L/person/year")
                resource_b.metric("Waste entered",f"{waste:,.1f} kg/year")
                st.caption("Water and waste are resource indicators. They are not included in the CO₂e total.")
            else:
                st.caption("This older estimate does not contain saved activity inputs for the separate water and waste indicators.")

            previous=_previous_compatible(records,selected)
            if previous:
                previous_breakdown=previous["category_breakdown"]
                common_categories=[key for key in breakdown if key in previous_breakdown]
                if common_categories:
                    st.subheader("Category changes vs your previous comparable estimate")
                    st.caption("Positive values mean this estimate is higher; negative values mean it is lower. This comparison alone does not prove savings.")
                    deltas=pd.DataFrame([{"Category":key,"Change in estimated kg CO₂e/year":breakdown[key]-previous_breakdown[key]} for key in common_categories])
                    if category!="All categories": deltas=deltas[deltas["Category"]==category]
                    delta_fig=px.bar(deltas,x="Change in estimated kg CO₂e/year",y="Category",orientation="h",color="Category",
                                     color_discrete_map={"Transportation":"#397b4e","Electricity":"#9aa83f","Food":"#c58245"})
                    delta_fig.update_layout(showlegend=False,template="plotly_white",paper_bgcolor="rgba(0,0,0,0)",
                                            plot_bgcolor="rgba(0,0,0,0)",font_color="#56645a",margin=dict(t=8,b=8,l=0,r=10),height=220,
                                            xaxis=dict(showgrid=True,gridcolor="#e3e9e1"),yaxis=dict(showgrid=False))
                    st.plotly_chart(delta_fig,use_container_width=True,config={"displayModeBar":False})

        st.divider()
        lower_left,lower_right=st.columns([1.2,1],gap="large")
        with lower_left:
            st.subheader("Recommended next steps")
            if suggested_actions:
                for action in suggested_actions:
                    with st.container(border=True):
                        st.markdown(f"**{action['title']}** · {action['category']}")
                        st.write(action["description"])
                        st.progress(action["relevance_score"],text=f"Profile fit · {action['relevance_score']:.0%}")
                        st.caption(f"{action['reason']} · Effort {action['difficulty']}/5 · {action['cost_tier'].title()} cost tier")
                st.button("Explore all recommendations →",key="dash_all_actions",on_click=_navigate,args=("Recommendations",))
            else:
                st.info("Recommendations are temporarily unavailable. Browse the complete action list instead.")
                st.button("Browse actions →",key="dash_find_action",on_click=_navigate,args=("Recommendations",))
            if saved_actions:
                with st.expander(f"Actions in your goals ({len(saved_actions)})"):
                    for action in saved_actions:
                        st.markdown(f"• **{action['title']}** · {action['category']}")
        with lower_right:
            st.subheader("Recent activity")
            events=_recent_activity(records,progress_rows,recommendations)
            if events:
                for when,title,detail in events[:4]:
                    st.markdown(f"**{title}**  \n{detail}")
                    st.caption(when)
            else:
                st.info("Your saved estimates and goals will show here as you use the app.")
            with st.expander("Your lifestyle profile"):
                profile=st.session_state.profile
                profile_cols=st.columns(2)
                profile_cols[0].metric("City",profile.get("city","Not set"))
                profile_cols[1].metric("Commute",profile.get("commute","Not set"))
                profile_cols[0].metric("Diet",profile.get("diet","Not set"))
                profile_cols[1].metric("Electricity",f"{profile.get('electricity',0):,.0f} kWh/month")
                st.button("Edit lifestyle profile →",key="dash_edit_profile",on_click=_navigate,args=("Questionnaire",))

    with goal_tab:
        st.subheader("Your goals and habits")
        if not goals:
            st.info("You have not saved a goal yet. Choose one practical action to start tracking.")
            st.button("Explore personalized actions →",key="dash_goal_empty",type="primary",on_click=_navigate,args=("Recommendations",))
        else:
            counts={"Active":active,"Paused":paused,"Completed":completed}
            goal_summary=pd.DataFrame([{"Status":status,"Goals":count} for status,count in counts.items() if count])
            stat_col,chart_col=st.columns([1,1.2])
            with stat_col:
                open_goals=[goal for goal in goals if not goal["done"]]
                if open_goals:
                    progress_mean=sum(goal["progress"] for goal in open_goals)/len(open_goals)
                    st.metric("Average progress on open goals",f"{progress_mean:.0%}")
                    st.caption("Average of your active and paused goals; completed goals are not included.")
                else:
                    st.metric("Open goals","None","All saved goals are complete")
            with chart_col:
                if not goal_summary.empty:
                    fig=px.pie(goal_summary,names="Status",values="Goals",hole=.62,
                               color="Status",color_discrete_map={"Active":"#397b4e","Paused":"#d39a48","Completed":"#5b9a95"})
                    fig.update_layout(template="plotly_white",paper_bgcolor="rgba(0,0,0,0)",font_color="#56645a",
                                      margin=dict(t=5,b=5,l=5,r=5),height=260,legend_title_text="")
                    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            st.subheader("Update a goal")
            for goal in [g for g in goals if not g["done"]][:5]:
                with st.container(border=True):
                    st.markdown(f"**{goal['title']}** · {goal['category']}")
                    status=goal.get("status","active")
                    if status=="paused":
                        st.caption("Paused")
                    else:
                        st.slider("Progress",0,100,int(goal["progress"]*100),key=f"dashboard_progress_{goal['db_id']}",
                                  on_change=_save_goal_progress,args=(goal["db_id"],))
                    action_cols=st.columns(3)
                    target="active" if status=="paused" else "paused"
                    action_cols[0].button("Resume" if status=="paused" else "Pause",key=f"dashboard_status_{goal['db_id']}",
                                          on_click=_set_goal_status,args=(goal["db_id"],target),use_container_width=True)
                    action_cols[1].button("Complete",key=f"dashboard_complete_{goal['db_id']}",
                                          on_click=_set_goal_status,args=(goal["db_id"],"completed"),use_container_width=True)
                    action_cols[2].button("Manage goals",key=f"dashboard_manage_{goal['db_id']}",
                                          on_click=_navigate,args=("Progress tracking",),use_container_width=True)
            if len([g for g in goals if not g["done"]])>5:
                st.caption("Showing your first five open goals.")
            if completed:
                st.success(f"You have completed {completed} goal{'s' if completed!=1 else ''}. Every completed goal is a habit you chose to practice.")

    with history_tab:
        st.subheader("Estimate history")
        if not records:
            st.info("Saved estimates will appear here after you calculate and save one.")
        else:
            versions=list(dict.fromkeys(record["factor_version"] for record in records))
            version=st.selectbox("Factor set",versions,key=f"dashboard_history_version_{uid}")
            matching=[record for record in records if record["factor_version"]==version]
            compatible=_compatible_history(matching,version)
            view_count=st.select_slider("Estimates to show",options=[5,10,20,50],value=10,key=f"dashboard_history_count_{uid}")
            compatible=compatible[-view_count:]
            if len(compatible)>=2:
                frame=pd.DataFrame([{"Saved":f"{r['created_at']} · #{r['record_id']}","Estimated kg CO₂e/year":r["total_kg_co2e"]} for r in compatible])
                fig=px.line(frame,x="Saved",y="Estimated kg CO₂e/year",markers=True,color_discrete_sequence=["#397b4e"],
                            hover_data={"Estimated kg CO₂e/year":":,.1f"})
                fig.update_layout(template="plotly_white",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                  font_color="#56645a",margin=dict(t=15,b=0,l=0,r=0),height=340,
                                  xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor="#e3e9e1"))
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                if len(compatible)<len(matching):
                    st.caption("Only estimates with saved input details are charted. Older records remain listed below.")
            else:
                st.info("Save two estimates with this factor set and the current input format to compare them.")
            st.dataframe([{"Saved":r["created_at"],"Total kg CO₂e/year":r["total_kg_co2e"],
                           "Factor set":r["factor_version"],"Input details":"Available" if r.get("input_snapshot",{}).get("schema_version")==1 else "Older record"}
                          for r in matching],hide_index=True,use_container_width=True)
            st.button("Calculate another estimate →",key="dash_new_estimate",on_click=_navigate,args=("Carbon footprint",))
    st.caption("These are partial estimates from the activity amounts entered. The app does not calculate a sustainability score or verified action savings.")
