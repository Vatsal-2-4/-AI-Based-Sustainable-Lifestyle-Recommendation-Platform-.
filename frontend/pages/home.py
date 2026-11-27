"""Visual-first landing page inspired by the supplied sustainability UI reference."""
import base64
import html
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from database.repository import get_footprint_records

LANDSCAPE_PATH=Path(__file__).resolve().parents[2]/"assets"/"images"/"evergreen-landscape.svg"


def _route(page):
    return "?page="+quote(page,safe="")

def _navigate(page):
    st.session_state.page=page
    st.session_state.nav=page


def _next_step():
    profile_saved=st.session_state.get("questionnaire_saved",False)
    footprint_saved=bool(st.session_state.get("latest_footprint_record_id"))
    goals=st.session_state.get("goals",[])
    in_progress=any(g.get("progress",0)>0 and not g.get("done",False) for g in goals)
    if not profile_saved:
        return "Questionnaire","Build your profile"
    if not footprint_saved:
        return "Carbon footprint","Calculate your footprint"
    if not goals:
        return "Recommendations","Find an action"
    if not in_progress:
        return "Progress tracking","Track a goal"
    return "Dashboard","Open your dashboard"


def _hero_cards(uid):
    try:
        records=get_footprint_records(uid,limit=1)
    except Exception:
        records=[]
    goals=st.session_state.get("goals",[])
    active=sum(not goal.get("done",False) for goal in goals)
    complete=sum(goal.get("done",False) for goal in goals)
    total_goals=active+complete
    completion=round(100*complete/total_goals) if total_goals else 0

    if records:
        record=records[0]
        pairs=sorted(record["category_breakdown"].items(),key=lambda item:item[1],reverse=True)[:3]
        max_value=max((float(value) for _,value in pairs),default=1) or 1
        bars="".join(
            "<div class='impact-line'><span>"+html.escape(str(name))+"</span><div class='impact-track'><div class='impact-fill' style='width:"+str(max(3,round(100*float(value)/max_value)))+"%'></div></div><b>"+f"{float(value):,.0f}"+" kg</b></div>"
            for name,value in pairs
        )
        estimate_card=("<div class='evergreen-glass impact-glass'><div class='glass-heading'><div><h3>Footprint snapshot</h3><p>Saved "+html.escape(str(record["created_at"]))+" · partial estimate</p></div><a class='tiny-arrow' href='"+html.escape(_route("Dashboard"),quote=True)+"' aria-label='Explore dashboard'>↗</a></div>"+bars+"<div class='glass-foot'>"+f"<strong>{float(record['total_kg_co2e']):,.0f} kg CO₂e</strong>"+"<span>· factor set "+html.escape(str(record["factor_version"]))+"</span></div></div>")
    else:
        estimate_card=("<div class='evergreen-glass impact-glass'><div class='glass-heading'><div><h3>Your footprint snapshot</h3><p>Your saved estimate will appear here</p></div><a class='tiny-arrow' href='"+html.escape(_route("Carbon footprint"),quote=True)+"' aria-label='Calculate footprint'>↗</a></div><div class='empty-snapshot'><span class='snapshot-orbit' aria-hidden='true'></span><span>Start with activity you know. We will show what is included.</span></div></div>")

    quick_card=("<div class='evergreen-glass quick-glass'><div class='glass-heading'><div><h3>Your next steps</h3><p>Small, practical moves</p></div><span class='step-count'>"+str(min(total_goals,99))+" goals</span></div><div class='quick-links'>"
        "<a href='"+html.escape(_route("Questionnaire"),quote=True)+"' aria-label='Open lifestyle profile'><span>01</span><b>Profile</b></a>"
        "<a href='"+html.escape(_route("Carbon footprint"),quote=True)+"' aria-label='Open footprint calculator'><span>02</span><b>Estimate</b></a>"
        "<a href='"+html.escape(_route("Recommendations"),quote=True)+"' aria-label='Open recommendations'><span>03</span><b>Actions</b></a></div>"
        "<div class='goal-meter'><div class='goal-meter-fill' style='width:"+str(completion)+"%'></div></div><div class='glass-foot'><span>"+str(active)+" active</span><span>"+str(complete)+" completed</span></div></div>")
    return quick_card+estimate_card


def render():
    destination,cta_label=_next_step()
    try:
        svg_b64=base64.b64encode(LANDSCAPE_PATH.read_bytes()).decode("ascii")
    except OSError:
        svg_b64=""
    hero_image=("data:image/svg+xml;base64,"+svg_b64) if svg_b64 else ""
    cards=_hero_cards(st.session_state.user_id)
    hero=(
        "<section class='evergreen-landing' style='--hero-image:url(\""+hero_image+"\")'>"
        "<header class='evergreen-nav'><a class='evergreen-brand' href='"+html.escape(_route("Home"),quote=True)+"'><b aria-hidden='true'></b>evergreen</a>"
        "<nav class='evergreen-menu' aria-label='Main navigation'>"
        "<a class='menu-current' href='"+html.escape(_route("Home"),quote=True)+"'>Home</a>"
        "<a href='#journey'>About</a>"
        "<a href='"+html.escape(_route("Dashboard"),quote=True)+"'>Dashboard</a>"
        "<a href='"+html.escape(_route("Recommendations"),quote=True)+"'>Actions</a>"
        "<a href='"+html.escape(_route("Profile"),quote=True)+"'>Profile</a>"
        "<a href='"+html.escape(_route("Login / Register"),quote=True)+"'>Account</a></nav>"
        "<a class='evergreen-start' href='"+html.escape(_route("Login / Register"),quote=True)+"'>Start now <span>↗</span></a></header>"
        "<div class='evergreen-copy'><div class='evergreen-eyebrow'>Understand your impact · Choose what comes next</div>"
        "<h1>Live lighter,<br><em>leave more green.</em></h1>"
        "<p>A clearer picture of your everyday footprint, with practical actions shaped around your routine.</p>"
        "<div class='evergreen-actions'><a class='evergreen-cta' href='"+html.escape(_route(destination),quote=True)+"'>"+html.escape(cta_label)+" <span>↗</span></a>"
        "<a class='evergreen-cta secondary' href='"+html.escape(_route("Dashboard"),quote=True)+"'>Explore dashboard</a></div></div>"
        "<div class='evergreen-cards'>"+cards+"</div>"
        "<div class='landing-footnote'>Estimates are partial and based on the activity you enter.</div>"
        "</section>"
    )
    st.markdown(hero,unsafe_allow_html=True)
    st.markdown("<div id='journey' class='journey-intro'><span>A clear, practical approach</span><h2>From everyday habits<br>to a next step that fits.</h2><p>Explore the profile, estimate, and action tools. Each is designed to be transparent about what it can—and cannot—tell you.</p></div>",unsafe_allow_html=True)
    a,b,c=st.columns(3)
    cards=[("01","Know your footprint","Review selected emissions categories with their factors and assumptions.","Open calculator","Carbon footprint"),
           ("02","Find your next step","Explore actions ranked against the habits and constraints you shared.","Explore actions","Recommendations"),
           ("03","Build a lasting habit","Save an action as a goal and record your progress over time.","View progress","Progress tracking")]
    for col,(number,title,description,label,page) in zip((a,b,c),cards):
        with col:
            st.markdown(f"<div class='journey-card journey-{number}'><span>{number}</span><h3>{title}</h3><p>{description}</p></div>",unsafe_allow_html=True)
            st.button(label,key=f"landing_{page}",icon="↗",use_container_width=True,on_click=_navigate,args=(page,))
    st.caption("Academic prototype · Local SQLite storage · No verified action-savings or sustainability score is claimed.")
