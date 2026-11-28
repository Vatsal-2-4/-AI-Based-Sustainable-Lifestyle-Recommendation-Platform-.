import streamlit as st
import plotly.express as px
import pandas as pd
from database.repository import update_progress, delete_progress, get_footprint_records


EMISSION_INPUT_LABELS={"Transportation":"Transport fuel","Electricity":"Electricity","Food":"Food quantities"}

def _input_coverage(record):
    """Return emission categories with a reported, non-zero amount in a saved snapshot."""
    snapshot=record.get("input_snapshot") or {}
    transport=snapshot.get("transport") or {}
    food=snapshot.get("food_kg_week") or {}
    coverage=[]
    try:
        if float(transport.get("petrol_l_month",0) or 0)+float(transport.get("diesel_l_month",0) or 0)>0:
            coverage.append("Transportation")
        if float(snapshot.get("electricity_kwh_month",0) or 0)>0:
            coverage.append("Electricity")
        if sum(float(amount or 0) for amount in food.values())>0:
            coverage.append("Food")
    except (AttributeError,TypeError,ValueError):
        return None
    return tuple(coverage)


def _incompatibility_reason(record, reference):
    reasons=[]
    if record.get("factor_version")!=reference.get("factor_version"):
        reasons.append(f"factor set differs ({record.get('factor_version')} vs {reference.get('factor_version')})")
    record_snapshot=record.get("input_snapshot") or {}
    ref_snapshot=reference.get("input_snapshot") or {}
    if record_snapshot.get("schema_version")!=1 or ref_snapshot.get("schema_version")!=1:
        reasons.append("saved input details are missing or use an older format")
    else:
        record_coverage=_input_coverage(record)
        ref_coverage=_input_coverage(reference)
        if record_coverage is None or ref_coverage is None:
            reasons.append("saved input details could not be read")
        elif record_coverage!=ref_coverage:
            before=", ".join(EMISSION_INPUT_LABELS[name] for name in record_coverage) or "no emissions categories reported"
            after=", ".join(EMISSION_INPUT_LABELS[name] for name in ref_coverage) or "no emissions categories reported"
            reasons.append(f"included categories differ ({before} vs {after})")
    return "; ".join(reasons)


def _navigate(page):
    st.session_state.page=page
    st.session_state.nav=page


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
    st.markdown("<div class='page-kicker'>Your journey</div>",unsafe_allow_html=True)
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
    if not records:
        st.info("Your saved footprint trend will appear here after you save an estimate.")
        st.button("Create your first estimate →",key="progress_first_estimate",type="primary",on_click=_navigate,args=("Carbon footprint",))
    else:
        reference=records[0]
        comparable=[r for r in records if not _incompatibility_reason(r,reference)]
        comparable=list(reversed(comparable))
        if len(comparable)>=2:
            st.markdown("#### Trend in compatible annualized estimates")
            st.caption(f"All points use factor set **{reference['factor_version']}**, the same saved-input format, and the same reported emissions categories. Values are annual estimates calculated from monthly fuel/electricity and weekly food inputs; dates show when each estimate was saved, not emissions measured during that calendar period.")
            history=pd.DataFrame([{"Saved":pd.to_datetime(r["created_at"]),"Estimate ID":r["record_id"],"Estimated kg CO₂e/year":r["total_kg_co2e"]} for r in comparable])
            fig=px.line(history,x="Saved",y="Estimated kg CO₂e/year",markers=True,hover_data={"Estimate ID":True,"Estimated kg CO₂e/year":":,.1f"},color_discrete_sequence=["#68ef3f"])
            fig.update_layout(template="plotly_dark",font_color="#d7dfd0",margin=dict(t=15,b=0,l=0,r=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=330,
                              xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor="rgba(242,245,235,.12)"))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

            options=[r["record_id"] for r in comparable]
            labels={r["record_id"]:f"{r['created_at']} · #{r['record_id']} · {r['total_kg_co2e']:,.1f} kg" for r in comparable}
            earlier_col,later_col=st.columns(2)
            earlier_id=earlier_col.selectbox("Earlier estimate",options,index=len(options)-2,format_func=lambda value:labels[value],key=f"progress_compare_earlier_{st.session_state.user_id}")
            later_id=later_col.selectbox("Later estimate",options,index=len(options)-1,format_func=lambda value:labels[value],key=f"progress_compare_later_{st.session_state.user_id}")
            older=next(record for record in comparable if record["record_id"]==earlier_id)
            newer=next(record for record in comparable if record["record_id"]==later_id)
            if older["record_id"]==newer["record_id"]:
                st.warning("Choose two different saved estimates to compare.")
            else:
                difference=float(newer["total_kg_co2e"])-float(older["total_kg_co2e"])
                delta=f"{difference:+,.1f} kg CO₂e/year"
                if float(older["total_kg_co2e"])>0:
                    delta+=f" · {difference/float(older['total_kg_co2e']):+.1%}"
                st.metric("Later estimate",f"{newer['total_kg_co2e']:,.1f} kg CO₂e/year",delta=delta,delta_color="off")
                st.caption(f"From {older['created_at']} to {newer['created_at']}. This is a change between estimates, not proof that emissions changed by the same amount in real life.")
                category_names=sorted(set(older["category_breakdown"])|set(newer["category_breakdown"]))
                category_changes=pd.DataFrame([{"Category":name,"Earlier kg CO₂e/year":older["category_breakdown"].get(name,0),"Later kg CO₂e/year":newer["category_breakdown"].get(name,0),"Change kg CO₂e/year":newer["category_breakdown"].get(name,0)-older["category_breakdown"].get(name,0)} for name in category_names])
                st.dataframe(category_changes,hide_index=True,use_container_width=True)
        elif len(comparable)==1:
            st.info("There is one estimate in the current comparison group. Save another estimate with the same factor set and reported categories to create a trend.")
        else:
            st.info("No two estimates share the latest estimate’s factor set, input format, and reported emissions categories, so a reliable trend cannot be shown yet.")

        st.markdown("#### Estimate compatibility")
        st.caption("Comparisons use the latest saved estimate as the reference. A record is comparable only when its emission factors, input format, and reported categories match.")
        compatibility=[]
        for record in records:
            reason=_incompatibility_reason(record,reference)
            if record["record_id"]==reference["record_id"]:
                status="Reference estimate"
            elif not reason:
                status="Comparable"
            else:
                status="Not compared: "+reason
            coverage=_input_coverage(record)
            scope=", ".join(EMISSION_INPUT_LABELS[name] for name in coverage) if coverage else "No emissions categories reported"
            compatibility.append({"Saved":record["created_at"],"Estimate ID":record["record_id"],"Total kg CO₂e/year":record["total_kg_co2e"],"Factor set":record["factor_version"],"Reported categories":scope,"Comparison":status})
        st.dataframe(compatibility,hide_index=True,use_container_width=True)

        incompatible=[record for record in records if record["record_id"]!=reference["record_id"] and _incompatibility_reason(record,reference)]
        if incompatible:
            with st.expander(f"Why {len(incompatible)} estimate(s) were excluded"):
                for record in incompatible:
                    st.markdown(f"- **{record['created_at']} · #{record['record_id']}** — {_incompatibility_reason(record,reference)}.")
                st.caption("Different factor versions may use different emission values or boundaries. Different reported categories change what the total covers. Older records without saved input details cannot be checked.")
        st.caption("Water and waste are resource indicators and remain outside the CO₂e total. A lower estimate is not, by itself, proof of a verified emissions reduction.")
