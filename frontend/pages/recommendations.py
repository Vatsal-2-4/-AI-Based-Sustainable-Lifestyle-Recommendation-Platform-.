import streamlit as st
import plotly.express as px

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
                    if not any(g['title']==item['title'] for g in st.session_state.goals): st.session_state.goals.append({"title":item['title'],"category":item['category'],"progress":0.0,"done":False})
                    st.success("Added")
    st.caption("Impact numbers are sample UI data pending verified emission factors.")
