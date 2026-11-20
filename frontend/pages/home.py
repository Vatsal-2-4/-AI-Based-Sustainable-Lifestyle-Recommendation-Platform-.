import streamlit as st

def _navigate(page):
    st.session_state.page = page
    st.session_state.nav = page

def render():
    st.markdown('<div class="hero"><div class="eyebrow" style="color:#c7ebd2">A MORE THOUGHTFUL WAY TO LIVE</div><h1>Make everyday choices count.</h1><p>Understand your lifestyle footprint and find practical, personalized ways to live a little lighter on the planet.</p></div>',unsafe_allow_html=True)
    st.write("")
    profile_saved=st.session_state.get("questionnaire_saved",False)
    footprint_saved=bool(st.session_state.get("latest_footprint_record_id"))
    goals=st.session_state.get("goals",[])
    in_progress=any(g.get("progress",0)>0 and not g.get("done",False) for g in goals)
    if not profile_saved:
        progress=.0; next_page="Questionnaire"; next_label="Build my lifestyle profile →"; prompt="Start with a short lifestyle profile. Skip details you do not know and edit your answers later."
    elif not footprint_saved:
        progress=.25; next_page="Carbon footprint"; next_label="Calculate my footprint →"; prompt="Your profile is saved. Next, enter the activity amounts used by the calculator."
    elif not goals:
        progress=.5; next_page="Recommendations"; next_label="Find an action that fits →"; prompt="Your estimate is saved. Explore actions matched to your profile and choose one to try."
    elif not in_progress:
        progress=.75; next_page="Progress tracking"; next_label="Track a goal →"; prompt="You have a saved goal. Update its progress when you take a step."
    else:
        progress=1.0; next_page="Dashboard"; next_label="Explore my dashboard →"; prompt="Your profile, estimate, and goal activity are saved."
    st.progress(progress,text=f"Getting started · {round(progress*4)}/4 steps")
    st.info(prompt)
    a,b=st.columns(2)
    with a: st.button(next_label,type="primary",use_container_width=True,on_click=_navigate,args=(next_page,))
    with b: st.button("Explore my dashboard",use_container_width=True,on_click=_navigate,args=("Dashboard",))
    st.subheader("A clearer path to sustainable habits")
    st.caption("Personal insights, grounded recommendations, and progress you can see.")
    cols=st.columns(3)
    for c,icon,title,desc in zip(cols,["◉","✦","↗"],["Know your footprint","Find your next step","Build lasting habits"],["See which parts of your lifestyle shape your annual impact.","Get ideas that fit your budget, home, and routine.","Set simple goals and see your progress over time."]):
        with c: st.markdown(f'<div class="card"><div style="font-size:1.6rem;color:#278253">{icon}</div><h3>{title}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    st.info("Academic prototype. Footprint calculations are estimates with documented factors and stated limitations, not audited emissions measurements.")
