import streamlit as st
from backend.services.recommendation_service import recommend_for_profile
from database.repository import save_recommendation, update_recommendation_status, create_progress

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
        if not any(g["title"]==action["title"] for g in st.session_state.goals):
            progress_id=create_progress(st.session_state.user_id,action["title"],action["category"],recommendation_id)
            st.session_state.goals.append({"db_id":progress_id,"title":action["title"],"category":action["category"],"progress":0.0,"done":False})
        st.session_state["goal_saved_message"]=f"Saved '{action['title']}' to your goals."
    except Exception as exc:
        st.session_state["goal_save_error"]=str(exc)

def render():
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
    except Exception as exc:
        st.error(f"Recommendation engine could not load the action catalogue: {exc}")
        return
    st.markdown(f"**{len(actions)} actions matched** · Content-based ranking with TF-IDF and cosine similarity")
    if not actions:
        st.warning("No action matched these profile constraints. Review your questionnaire or relax an availability constraint.")
        return
    for index,action in enumerate(actions,1):
        with st.container(border=True):
            left,right=st.columns([5,1])
            with left:
                st.markdown(f"<span class='tag'>#{index} · {action['category']} · {action['impact_tier'].title()} impact tier</span>",unsafe_allow_html=True)
                st.subheader(action["title"])
                st.write(action["description"])
                st.caption(f"Why this matched: {action['reason']}")
                st.progress(action["relevance_score"],text=f"Profile match · {action['relevance_score']:.0%}")
                st.caption(f"Effort: {action['difficulty']}/5 · Cost tier: {action['cost_tier'].title()} · Source: {action['source_name']}")
                st.markdown(f"[View action source]({action['source_url']})")
            with right:
                st.button("Add goal",key=f"add_goal_{action['action_id']}",use_container_width=True,on_click=_add_goal,args=(action,index))
    st.caption("No kg CO₂e savings are displayed because the catalogue does not yet contain validated, user-specific savings calculations.")
