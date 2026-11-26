import streamlit as st
from backend.services.recommendation_service import recommend_for_profile
from database.repository import save_recommendation, update_recommendation_status, create_progress, update_progress

def _open_progress():
    st.session_state.page="Progress tracking"
    st.session_state.nav="Progress tracking"

def _complete_goal(progress_id):
    goal=next((g for g in st.session_state.goals if g.get("db_id")==progress_id),None)
    if not goal: return
    try:
        update_progress(st.session_state.user_id,progress_id,progress_percent=100,status="completed")
        goal.update(progress=1.0,status="completed",done=True)
        st.session_state["goal_saved_message"]=f"Completed '{goal['title']}'."
    except ValueError as exc:
        st.session_state["goal_save_error"]=str(exc)
    except Exception:
        st.session_state["goal_save_error"]="Could not complete this goal. Check the local database and try again."

def _add_goal(action, rank):
    try:
        profile=st.session_state.profile
        recommendation_id=save_recommendation(st.session_state.user_id,{
            "action_key":action["action_id"], "category":action["category"],
            "title":action["title"], "explanation":action["reason"],
            "estimated_saving_kg_co2e":0, "difficulty":max(1,min(5,int(action["difficulty"]))),
            "relevance_score":action["relevance_score"], "rank_position":rank,
        },record_id=st.session_state.get("latest_footprint_record_id"))
        update_recommendation_status(st.session_state.user_id,recommendation_id,"saved")
        existing=next((g for g in st.session_state.goals if g.get("action_key")==action["action_id"] or g["title"]==action["title"]),None)
        if not existing:
            progress_id=create_progress(st.session_state.user_id,action["title"],action["category"],recommendation_id)
            st.session_state.goals.append({"db_id":progress_id,"recommendation_id":recommendation_id,"action_key":action["action_id"],"title":action["title"],"category":action["category"],"progress":0.0,"status":"active","done":False})
        st.session_state["goal_saved_message"]=f"Saved '{action['title']}' to your goals."
    except ValueError as exc:
        st.session_state["goal_save_error"]=str(exc)
    except Exception:
        st.session_state["goal_save_error"]="Could not save this action. Check the local database and try again."

def render():
    st.markdown("<div class='page-kicker'>EVERGREEN · PERSONALIZED ACTIONS</div>",unsafe_allow_html=True)
    st.title("Personalized recommendations")
    st.caption("Actions are matched to the habits and constraints in your lifestyle profile.")
    if st.session_state.get("goal_saved_message"):
        st.success(st.session_state.pop("goal_saved_message"))
    if st.session_state.get("goal_save_error"):
        st.error(f"Could not save goal: {st.session_state.pop('goal_save_error')}")
    with st.expander("How recommendations are selected"):
        st.write("The engine converts your profile and each catalogue action into text features with TF-IDF, then compares them using cosine similarity. Eligibility rules filter unavailable options. A small, documented reranking uses match category, effort, qualitative impact tier, and cost tier. The relevance score describes profile fit; it is not a confidence score or an emissions-savings estimate.")
    profile=st.session_state.profile.copy()
    if not st.session_state.get("questionnaire_saved",False):
        st.info("Using the demo profile. Complete the lifestyle questionnaire for recommendations based on your habits.")
    try:
        actions=recommend_for_profile(profile,top_n=8)
    except Exception:
        st.error("Recommendations are temporarily unavailable. Check the action catalogue and try again.")
        return
    st.markdown(f"**{len(actions)} actions matched** · Content-based ranking with TF-IDF and cosine similarity")
    if not actions:
        st.warning("No action matched these profile constraints. Review your questionnaire or relax an availability constraint.")
        return
    for index,action in enumerate(actions,1):
        with st.container(border=True):
            saved_goal=next((g for g in st.session_state.goals if g.get("action_key")==action["action_id"] or g["title"]==action["title"]),None)
            already_added=saved_goal is not None
            left,right=st.columns([5,1])
            with left:
                st.markdown(f"<span class='tag'>#{index} · {action['category']} · {action['impact_tier'].title()} impact tier</span>",unsafe_allow_html=True)
                st.subheader(action["title"])
                st.write(action["description"])
                st.caption("Why it matched: " + "; ".join(action["matched_habits"]))
                st.progress(action["relevance_score"],text=f"Profile relevance · {action['relevance_score']:.0%} (not confidence or impact)")
                st.caption(f"Effort: {action['difficulty']}/5 · Cost tier: {action['cost_tier'].title()}")
                with st.expander("Why this matched · model details and source"):
                    st.markdown("**Profile details used for this category**")
                    for habit in action["matched_habits"]: st.markdown(f"- {habit}")
                    st.caption(f"Catalogue text similarity: {action['similarity']:.0%} · Category fit: {action['category_fit']:.0%}. Profile relevance also includes effort, impact tier, and cost tier. These are matching signals, not confidence or savings.")
                    eligibility=action.get("eligibility","general")
                    eligibility_text={"public_transport_available":"The questionnaire says public transport is practical for your commute.","short_trip_suitable":"This action is for short trips where walking or cycling is suitable.","uses_private_vehicle":"This action applies to a private vehicle commute.","has_non_plant_based_meals":"This action is shown for profiles that include non-plant-based meals.","food_waste_reported":"This action is shown when some food waste is reported.","composting_possible":"This action requires access to composting.","shops_in_person":"This action applies to in-person shopping."}.get(eligibility,"This action passed the catalogue's applicability checks for your profile.")
                    st.write(eligibility_text+" Review the action and decide whether it fits your circumstances.")
                    st.caption("The catalogue does not provide validated, user-specific emissions savings for this action.")
                    st.markdown(f"Source: [{action['source_name']}]({action['source_url']})")
            with right:
                if not already_added:
                    st.button("Add goal",key=f"add_goal_{action['action_id']}",use_container_width=True,on_click=_add_goal,args=(action,index))
                else:
                    st.success("Goal saved")
                    if saved_goal.get("status")=="completed":
                        st.caption("Completed ✓")
                    elif saved_goal.get("status")=="paused":
                        st.caption("Paused")
                    else:
                        st.progress(saved_goal.get("progress",0),text=f"Progress · {saved_goal.get('progress',0):.0%}")
                        st.button("Mark complete",key=f"complete_recommendation_{saved_goal['db_id']}",use_container_width=True,on_click=_complete_goal,args=(saved_goal["db_id"],))
                    st.button("Track progress →",key=f"track_recommendation_{saved_goal['db_id']}",use_container_width=True,on_click=_open_progress)
    st.caption("No kg CO₂e savings are displayed because the catalogue does not yet contain validated, user-specific savings calculations.")
