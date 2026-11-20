import streamlit as st


def _navigate(page):
    st.session_state.page=page
    st.session_state.nav=page


def _next_step():
    profile_saved=st.session_state.get("questionnaire_saved",False)
    footprint_saved=bool(st.session_state.get("latest_footprint_record_id"))
    goals=st.session_state.get("goals",[])
    in_progress=any(g.get("progress",0)>0 and not g.get("done",False) for g in goals)
    if not profile_saved:
        return 0.0,"Questionnaire","Build my lifestyle profile →","Start with a short profile. Skip details you do not know and edit your answers later."
    if not footprint_saved:
        return .25,"Carbon footprint","Calculate my footprint →","Your profile is saved. Next, enter the activity amounts used by the calculator."
    if not goals:
        return .5,"Recommendations","Find an action that fits →","Your estimate is saved. Explore actions matched to your profile and choose one to try."
    if not in_progress:
        return .75,"Progress tracking","Track a goal →","You have a saved goal. Update its progress when you take a step."
    return 1.0,"Dashboard","Explore my dashboard →","Your profile, estimate, and goal activity are saved."


def render():
    st.markdown('<div class="hero"><div class="eyebrow" style="color:#c7ebd2">A MORE THOUGHTFUL WAY TO LIVE</div><h1>Make everyday choices count.</h1><p>Understand your lifestyle footprint and find practical, personalized ways to live a little lighter on the planet.</p></div>',unsafe_allow_html=True)
    st.write("")
    start,how,privacy=st.tabs(["Get started","How it works","Data and privacy"])
    with start:
        progress,page,label,prompt=_next_step()
        st.progress(progress,text=f"Your journey · {round(progress*4)}/4 steps")
        st.info(prompt)
        st.button(label,type="primary",use_container_width=True,on_click=_navigate,args=(page,))
        st.subheader("Jump to a page")
        a,b,c=st.columns(3)
        a.button("Calculate footprint",key="home_calculator",use_container_width=True,on_click=_navigate,args=("Carbon footprint",))
        b.button("Find recommendations",key="home_recommendations",use_container_width=True,on_click=_navigate,args=("Recommendations",))
        c.button("Track goals",key="home_progress",use_container_width=True,on_click=_navigate,args=("Progress tracking",))
    with how:
        st.subheader("A clear path from habits to action")
        columns=st.columns(3)
        steps=[("01 · Tell us about your routine","Add the habits and constraints that help personalize actions.","Build profile","Questionnaire"),
               ("02 · Estimate selected impacts","Enter activity amounts and review documented factors and exclusions.","Open calculator","Carbon footprint"),
               ("03 · Choose a next step","Explore matched actions, save a goal, and track what you try.","Explore actions","Recommendations")]
        for col,(title,description,label,page) in zip(columns,steps):
            with col:
                st.markdown(f"<div class='card'><div class='label'>{title.split(' · ')[0]}</div><h3>{title.split(' · ',1)[1]}</h3><p>{description}</p></div>",unsafe_allow_html=True)
                st.button(label,key=f"home_step_{page}",use_container_width=True,on_click=_navigate,args=(page,))
        st.caption("The calculator estimates selected categories from your inputs; it is not a complete or audited emissions inventory.")
    with privacy:
        st.subheader("Your data stays in the local project database")
        st.write("Questionnaire responses, estimates, recommendations, and goals are stored in a SQLite file on the computer running this app. Use the Profile page to download a JSON copy or delete the account and its saved records.")
        if not st.session_state.get("authenticated",False):
            st.info("You can explore the demo profile without registering. Create an account to keep a separate saved profile.")
        st.caption("This academic prototype does not include password recovery or production-grade login protections. Footprint results are estimates with documented factors and stated limitations.")
