import streamlit as st
import plotly.express as px
from database.repository import save_recommendation, update_recommendation_status, create_progress

def render():
    st.title("Recommendations")
    st.caption("Ideas ranked for your impact, budget, and routine.")
    actions=[{"title":"Replace 3 weekly car commutes with metro","category":"Transport","saving":600,"cost":"Save ~₹20,000/year","effort":"Moderate","fit":"Metro access near your commute","score":.92},{"title":"Add two plant-based dinners each week","category":"Food","saving":180,"cost":"Save ~₹2,400/year","effort":"Easy","fit":"Flexible option for a mixed diet","score":.84},{"title":"Set AC to 25°C","category":"Home energy","saving":140,"cost":"No upfront cost","effort":"Easy","fit":"A simple cooling habit","score":.78},{"title":"Segregate kitchen waste","category":"Waste","saving":90,"cost":"Low cost","effort":"Easy","fit":"Check local collection availability","score":.62}]
    st.markdown("#### Recommended for you")
    for i,item in enumerate(actions,1):
        with st.container(border=True):
            a,b=st.columns([4,1])
            with a:
                st.markdown(f'<span class="tag">#{i} · {item["category"]}</span>',unsafe_allow_html=True)
                st.subheader(item['title']); st.caption(item['fit'])
                st.write(f"**~{item['saving']} kg CO₂e/year**  ·  {item['cost']}  ·  {item['effort']}")
                st.progress(item['score'],text=f"Profile fit · {int(item['score']*100)}%")
            with b:
                if st.button("Add goal",key=f"goal_{i}",use_container_width=True):
                    try:
                        record_id=st.session_state.get("latest_footprint_record_id")
                        recommendation_id=save_recommendation(st.session_state.user_id, {
                            "action_key":f"demo-{i}", "category":item["category"], "title":item["title"],
                            "explanation":item["fit"], "estimated_saving_kg_co2e":item["saving"],
                            "difficulty":1 if item["effort"]=="Easy" else 2,
                            "relevance_score":item["score"], "rank_position":i,
                        }, record_id=record_id)
                        update_recommendation_status(st.session_state.user_id,recommendation_id,"saved")
                        if not any(g['title']==item['title'] for g in st.session_state.goals):
                            progress_id=create_progress(st.session_state.user_id,item['title'],item['category'],recommendation_id)
                            st.session_state.goals.append({"db_id":progress_id,"title":item['title'],"category":item['category'],"progress":0.0,"done":False})
                        st.success("Recommendation and goal saved to SQLite.")
                    except Exception as exc:
                        st.error(f"Could not save this recommendation: {exc}")
    st.caption("Impact numbers are sample UI data pending verified emission factors.")
