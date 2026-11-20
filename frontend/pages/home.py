import streamlit as st

def _navigate(page):
    st.session_state.page = page
    st.session_state.nav = page

def render():
    st.markdown('<div class="hero"><div class="eyebrow" style="color:#c7ebd2">A MORE THOUGHTFUL WAY TO LIVE</div><h1>Make everyday choices count.</h1><p>Understand your lifestyle footprint and find practical, personalized ways to live a little lighter on the planet.</p></div>',unsafe_allow_html=True)
    st.write("")
    a,b=st.columns(2)
    with a: st.button("Explore my dashboard →",type="primary",use_container_width=True,on_click=_navigate,args=("Dashboard",))
    with b: st.button("Build my lifestyle profile",use_container_width=True,on_click=_navigate,args=("Questionnaire",))
    st.subheader("A clearer path to sustainable habits")
    st.caption("Personal insights, grounded recommendations, and progress you can see.")
    cols=st.columns(3)
    for c,icon,title,desc in zip(cols,["◉","✦","↗"],["Know your footprint","Find your next step","Build lasting habits"],["See which parts of your lifestyle shape your annual impact.","Get ideas that fit your budget, home, and routine.","Set simple goals and see your progress over time."]):
        with c: st.markdown(f'<div class="card"><div style="font-size:1.6rem;color:#278253">{icon}</div><h3>{title}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    st.info("Academic prototype. Footprint calculations are estimates with documented factors and stated limitations, not audited emissions measurements.")
