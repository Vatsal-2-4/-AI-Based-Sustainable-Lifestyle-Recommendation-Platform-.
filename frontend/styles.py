import streamlit as st
from database.repository import get_or_create_user, get_user, get_progress, get_latest_lifestyle_response, get_footprint_records

DEFAULT_PROFILE = {"name":"Demo User", "city":"Bengaluru", "commute":"Petrol / diesel car", "commute_km":18, "commute_days":5, "diet":"Mixed diet", "housing":"Rented apartment", "budget":1000, "electricity":240, "ac":"Some days", "segregation":"Sometimes", "water_usage":"Moderate", "food_waste":"Sometimes", "shopping_habit":"Monthly", "public_transport_available":True, "shops_in_person":True, "composting_possible":False}

def initialize_state():
    st.session_state.setdefault("user_email", "demo@example.local")
    st.session_state.setdefault("profile", DEFAULT_PROFILE.copy())
    st.session_state.setdefault("goals", [])
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("page", "Home")
    user_id = get_or_create_user(st.session_state.user_email, st.session_state.profile["name"])
    st.session_state.user_id = user_id
    user = get_user(user_id)
    if user:
        st.session_state.profile["name"] = user["display_name"]
    if not st.session_state.get("db_profile_loaded", False):
        response=get_latest_lifestyle_response(user_id)
        if response:
            st.session_state.latest_response_id=response["response_id"]
            st.session_state.profile.update({
                "city":response["city"],"commute":response["commute_mode"],"commute_km":response["commute_km_day"],
                "commute_days":response["commute_days_week"],"diet":response["diet_pattern"],"housing":response["housing_type"],
                "budget":response["monthly_budget_inr"],"electricity":response["electricity_kwh_month"],"ac":response["ac_usage"],
                "segregation":response["waste_segregation"],**response["preferences"]})
            st.session_state.questionnaire_saved=True
        st.session_state.db_profile_loaded=True
    if not st.session_state.get("db_latest_footprint_loaded", False):
        records=get_footprint_records(user_id,limit=1)
        if records:
            st.session_state.latest_footprint_record_id=records[0]["record_id"]
        else:
            st.session_state.pop("latest_footprint_record_id",None)
        st.session_state.db_latest_footprint_loaded=True
    if not st.session_state.get("db_goals_loaded", False):
        st.session_state.goals = [{"db_id":row["progress_id"], "title":row["goal_title"], "category":row["category"], "progress":row["progress_percent"]/100, "status":row["status"], "done":row["status"]=="completed"} for row in get_progress(user_id)]
        st.session_state.db_goals_loaded = True

def load_styles():
    st.markdown("""<style>
    :root{--ink:#f2f4ee;--muted:#b4baae;--lime:#d6ff4f;--green:#729d42;--panel:#222720;--line:rgba(235,243,219,.12)}
    .stApp{background:#171a17;color:var(--ink)}
    [data-testid="stHeader"]{background:rgba(23,26,23,.92)}
    [data-testid="stSidebar"]{background:#1b1f1b;border-right:1px solid var(--line)}
    [data-testid="stSidebar"] *{color:var(--ink)}
    [data-testid="stSidebar"] [aria-checked="true"]{background:rgba(214,255,79,.12);border-radius:10px}
    [data-testid="stMainBlockContainer"]{max-width:1440px;padding-top:2rem;padding-bottom:3rem}
    h1,h2,h3{color:#f5f6f0;letter-spacing:-.035em}
    h1,h2{font-family:Georgia,'Times New Roman',serif;font-weight:400}
    p,small,.stCaption{color:var(--muted)}
    .card{background:linear-gradient(145deg,rgba(255,255,255,.075),rgba(255,255,255,.025));border:1px solid var(--line);border-radius:18px;padding:1.2rem;min-height:120px;backdrop-filter:blur(12px)}
    .label{font-size:.78rem;color:#b6c2a8;font-weight:700;letter-spacing:.06em}
    .value{font-size:1.8rem;font-weight:800;color:#f4f5ef;margin:.45rem 0}
    .green{color:var(--lime);font-weight:700;font-size:.8rem}
    .tag{background:rgba(214,255,79,.14);color:var(--lime);border:1px solid rgba(214,255,79,.2);border-radius:30px;padding:.25rem .6rem;font-size:.75rem;font-weight:700}
    [data-testid="stMetric"]{background:linear-gradient(145deg,#242a22,#1d211d);border:1px solid var(--line);border-radius:16px;padding:1rem;transition:transform .25s ease,border-color .25s ease}
    [data-testid="stMetric"]:hover{transform:translateY(-3px);border-color:rgba(214,255,79,.45)}
    .stButton>button,.stDownloadButton>button{border-radius:999px;border:1px solid rgba(214,255,79,.28);background:#242a22;color:var(--ink);transition:transform .2s ease,background .2s ease,border-color .2s ease}
    .stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-2px);background:#30392a;border-color:var(--lime);color:#fff}
    .stButton>button[kind="primary"]{background:var(--lime);border-color:var(--lime);color:#151910;font-weight:700}
    .stButton>button[kind="primary"]:hover{background:#e3ff83;border-color:#e3ff83;color:#151910}
    button:focus-visible,[role="radio"]:focus-visible,input:focus-visible{outline:3px solid var(--lime)!important;outline-offset:2px}
    [data-testid="stTabs"] [role="tab"]{color:var(--muted);border-radius:999px}
    [data-testid="stTabs"] [aria-selected="true"]{color:var(--lime);background:rgba(214,255,79,.1)}
    [data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"]>div>div,[data-testid="stTextArea"] textarea{background:#20251f;color:var(--ink);border-color:var(--line);border-radius:12px}
    [data-testid="stExpander"]{background:rgba(255,255,255,.025);border:1px solid var(--line);border-radius:14px}
    [data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden}
    .hero{background:linear-gradient(145deg,#252c21,#1c211b);border:1px solid var(--line);border-radius:22px;padding:2rem;color:var(--ink)}
    .hero h1{color:var(--lime)}
    .calc-hero{position:relative;overflow:hidden;padding:30px 34px;border:1px solid rgba(214,255,79,.22);border-radius:26px;background:radial-gradient(ellipse at 88% 0%,rgba(214,255,79,.22),transparent 35%),linear-gradient(125deg,#29372a,#19221a 65%,#253322);box-shadow:0 20px 54px rgba(0,0,0,.18);animation:revealUp .55s ease both}
    .calc-hero:after{content:'✳';position:absolute;right:35px;top:5px;color:rgba(214,255,79,.16);font-size:8rem;line-height:1;transform:rotate(-12deg);pointer-events:none}
    .calc-kicker{color:var(--lime);font-size:.7rem;font-weight:800;letter-spacing:.17em;text-transform:uppercase}
    .calc-hero h1{position:relative;z-index:1;margin:10px 0 8px;color:#f5f6f0;font:400 clamp(2.5rem,5vw,4.2rem)/.98 Georgia,'Times New Roman',serif;letter-spacing:-.055em}
    .calc-hero p{position:relative;z-index:1;max-width:640px;margin:0;color:#c4cdbd;line-height:1.6}
    .calc-content{margin-top:25px}
    .calc-panel{padding:20px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(145deg,rgba(255,255,255,.055),rgba(255,255,255,.018));box-shadow:0 18px 42px rgba(0,0,0,.12)}
    .calc-section-label{display:flex;align-items:center;gap:10px;color:#e9efdf;font-size:.88rem;font-weight:750;letter-spacing:.01em}
    .calc-section-label span{display:grid;place-items:center;width:34px;height:34px;border:1px solid rgba(214,255,79,.28);border-radius:12px;background:rgba(214,255,79,.1);color:var(--lime);font-size:1rem}
    .calc-live{padding:22px;border:1px solid rgba(214,255,79,.27);border-radius:23px;background:radial-gradient(ellipse at 100% 0%,rgba(214,255,79,.17),transparent 44%),linear-gradient(150deg,#293427,#1a211a);box-shadow:0 16px 42px rgba(0,0,0,.22);transition:transform .25s ease,border-color .25s ease}
    .calc-live:hover{transform:translateY(-3px);border-color:rgba(214,255,79,.5)}
    .calc-live-label{color:#c3ceb8;font-size:.75rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase}
    .calc-live-value{margin:8px 0 3px;color:var(--lime);font:400 clamp(2.35rem,4vw,3.6rem)/1 Georgia,'Times New Roman',serif;letter-spacing:-.055em}
    .calc-live-note{color:#aebaa6;font-size:.78rem}
    .calc-mini{height:100%;padding:15px 16px;border:1px solid var(--line);border-radius:17px;background:rgba(255,255,255,.035);transition:transform .2s ease,border-color .2s ease}
    .calc-mini:hover{transform:translateY(-3px);border-color:rgba(214,255,79,.35)}
    .calc-mini-label{color:#abb7a4;font-size:.73rem}
    .calc-mini-value{margin-top:7px;color:#f1f4ec;font-size:1.13rem;font-weight:750}
    [data-testid="stTabs"] [role="tablist"]{gap:6px;border-bottom:1px solid var(--line)}
    [data-testid="stTabs"] [role="tab"]{padding:.55rem .9rem;border:1px solid transparent;transition:all .2s ease}
    [data-testid="stTabs"] [role="tab"]:hover{background:rgba(214,255,79,.08);color:var(--lime)}
    [data-testid="stPlotlyChart"]{padding:8px;border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.025)}
    @media(max-width:720px){.calc-hero{padding:24px 20px}.calc-hero:after{right:8px;top:12px;font-size:5rem}.calc-panel{padding:15px}}
    @keyframes revealUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
    @keyframes softGlow{0%,100%{opacity:.22;transform:scale(.96)}50%{opacity:.45;transform:scale(1.04)}}
    .evergreen-landing{position:relative;isolation:isolate;min-height:740px;overflow:hidden;border:1px solid rgba(239,247,218,.16);border-radius:28px;background:#a5bd83 var(--hero-image) center 48%/cover no-repeat;color:#121710;box-shadow:0 28px 90px rgba(0,0,0,.35);animation:revealUp .7s ease both}
    .evergreen-landing:before{content:"";position:absolute;inset:0;z-index:0;background:linear-gradient(180deg,rgba(214,255,79,.12) 0%,rgba(238,245,204,.04) 37%,rgba(10,24,15,.58) 100%);pointer-events:none}
    .evergreen-landing:after{content:"";position:absolute;z-index:0;width:420px;height:420px;right:10%;top:8%;border-radius:50%;background:rgba(244,255,174,.35);filter:blur(90px);animation:softGlow 8s ease-in-out infinite;pointer-events:none}
    .evergreen-nav{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;gap:20px;padding:22px 30px}
    .evergreen-brand{font-size:1rem;font-weight:800;letter-spacing:-.04em;color:#11150f;text-decoration:none;white-space:nowrap}
    .evergreen-brand b{color:#182315;font-size:1.35rem;margin-right:8px}
    .evergreen-menu{display:flex;gap:5px;padding:5px;border-radius:999px;background:rgba(237,255,166,.36);backdrop-filter:blur(18px)}
    .evergreen-menu a,.evergreen-start{padding:10px 16px;border-radius:999px;text-decoration:none;color:#22281d;font-size:.82rem;transition:background .2s ease,color .2s ease,transform .2s ease}
    .evergreen-menu a:hover{background:rgba(255,255,255,.55);transform:translateY(-1px)}
    .evergreen-start{background:#141712;color:#eaff9b;font-weight:700;white-space:nowrap}
    .evergreen-start:hover{background:#293321;color:#f4ffd0;transform:translateY(-2px)}
    .evergreen-copy{position:relative;z-index:2;max-width:860px;margin:35px auto 0;padding:0 24px;text-align:center;animation:revealUp .9s .08s ease both}
    .evergreen-eyebrow{font-size:.72rem;font-weight:800;letter-spacing:.19em;text-transform:uppercase;color:#39492a}
    .evergreen-copy h1{margin:18px 0 12px;font-family:Georgia,'Times New Roman',serif;font-weight:400;font-size:clamp(3.6rem,8.5vw,7.4rem);line-height:.88;letter-spacing:-.075em;color:#10140f;text-shadow:0 2px 22px rgba(245,255,220,.18)}
    .evergreen-copy h1 em{font-weight:400;color:#293b20}
    .evergreen-copy p{max-width:540px;margin:18px auto 0;color:#26351f;font-size:1.02rem;line-height:1.6}
    .evergreen-actions{display:flex;justify-content:center;gap:12px;margin-top:24px}
    .evergreen-cta{display:inline-flex;align-items:center;justify-content:center;padding:13px 22px;border-radius:999px;background:#171b14;color:#eaff99;text-decoration:none;font-weight:750;transition:transform .2s ease,box-shadow .2s ease}
    .evergreen-cta:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(12,24,12,.24);color:#f4ffd1}
    .evergreen-cta.secondary{background:rgba(245,250,224,.44);border:1px solid rgba(26,39,21,.22);color:#172013;backdrop-filter:blur(14px)}
    .evergreen-cards{position:absolute;z-index:2;left:50%;bottom:34px;display:grid;grid-template-columns:1fr 1.18fr;gap:14px;width:min(760px,calc(100% - 48px));transform:translateX(-50%)}
    .evergreen-glass{min-height:132px;padding:17px 19px;border:1px solid rgba(255,255,255,.36);border-radius:22px;background:rgba(227,237,205,.52);backdrop-filter:blur(20px);box-shadow:0 15px 40px rgba(14,35,16,.16);animation:revealUp .8s .35s ease both;transition:transform .25s ease,background .25s ease}
    .evergreen-glass:hover{transform:translateY(-5px);background:rgba(242,248,223,.67)}
    .evergreen-glass h3{margin:0;color:#263321;font:600 .82rem system-ui;letter-spacing:0}
    .evergreen-glass p{margin:8px 0;color:#3e4b38;font-size:.78rem}
    .glass-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
    .glass-heading p{margin:5px 0 0}
    .tiny-arrow{display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:rgba(20,27,17,.88);color:#edffac;text-decoration:none}
    .step-count{font-size:.72rem;color:#34412e}
    .quick-links{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}
    .quick-links a{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:14px;color:#263321;text-decoration:none;font-size:.72rem;transition:transform .22s ease,background .22s ease}
    .quick-links a span{display:grid;place-items:center;width:34px;height:34px;flex:0 0 34px;border-radius:50%;background:#151a13;color:#efffb3;font-size:.67rem;font-weight:800}
    .quick-links a:nth-child(2) span{background:var(--lime);color:#182012}
    .quick-links a:hover{transform:translateY(-3px);background:rgba(255,255,255,.25)}
    .goal-meter{height:6px;margin:12px 0 5px;border-radius:99px;background:rgba(30,45,24,.16);overflow:hidden}
    .goal-meter-fill{height:100%;border-radius:inherit;background:#20281c;transition:width .6s ease}
    .empty-snapshot{display:flex;align-items:center;gap:12px;margin-top:17px;color:#34412e;font-size:.79rem}
    .snapshot-orbit{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:#d6ff4f;color:#25321d;font-size:1.2rem;animation:softGlow 5s ease-in-out infinite}
    .impact-line{display:grid;grid-template-columns:82px 1fr 56px;align-items:center;gap:8px;margin:8px 0;font-size:.72rem;color:#34412e}
    .impact-track{height:8px;border-radius:99px;background:rgba(30,45,24,.14);overflow:hidden}
    .impact-fill{height:100%;border-radius:inherit;background:#1b2118;transform-origin:left;animation:barGrow .9s .5s ease both}
    @keyframes barGrow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
    .landing-footnote{position:absolute;z-index:2;right:28px;bottom:13px;color:rgba(250,255,234,.82);font-size:.68rem;text-shadow:0 1px 5px rgba(0,0,0,.4)}
    .journey-intro{max-width:720px;margin:82px auto 30px;text-align:center}
    .journey-intro>span{color:var(--lime);font-size:.7rem;font-weight:800;letter-spacing:.18em}
    .journey-intro h2{font-size:clamp(2.4rem,5vw,4rem);line-height:.98;margin:15px 0}
    .journey-intro p{max-width:600px;margin:0 auto;color:var(--muted);line-height:1.65}
    .journey-card{height:100%;min-height:190px;padding:24px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(145deg,#252c22,#1d211d);transition:transform .24s ease,border-color .24s ease,background .24s ease}
    .journey-card:hover{transform:translateY(-6px);border-color:rgba(214,255,79,.4);background:linear-gradient(145deg,#2b3425,#1f251e)}
    .journey-card>span{color:var(--lime);font-size:.72rem;font-weight:800;letter-spacing:.1em}
    .journey-card h3{margin:16px 0 8px;font:400 1.45rem Georgia,'Times New Roman',serif;letter-spacing:-.03em}
    .journey-card p{color:var(--muted);line-height:1.5;font-size:.9rem}
    @media (max-width:800px){.evergreen-landing{min-height:850px}.evergreen-nav{padding:18px 16px;flex-wrap:wrap}.evergreen-menu{order:3;width:100%;justify-content:center;overflow:auto}.evergreen-menu a{padding:9px 12px}.evergreen-copy{margin-top:34px}.evergreen-copy h1{font-size:clamp(3.3rem,13vw,6rem)}.evergreen-cards{bottom:36px;grid-template-columns:1fr;width:calc(100% - 32px)}.evergreen-glass{min-height:108px}.journey-intro{margin-top:56px}}
    @media (max-width:420px){.evergreen-start{padding:9px 12px}.evergreen-copy{padding:0 16px}.evergreen-copy p{font-size:.92rem}.evergreen-actions{flex-direction:column;align-items:stretch}.evergreen-cards{bottom:28px}}
    @media (prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important}}
    @media (max-width: 720px){[data-testid="stMainBlockContainer"]{padding:1rem .85rem 2rem}.card{padding:1rem;min-height:auto}.value{font-size:1.5rem}}
    </style>""", unsafe_allow_html=True)
