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
        st.session_state.goals = [{"db_id":row["progress_id"], "recommendation_id":row.get("recommendation_id"), "action_key":row.get("action_key"), "title":row["goal_title"], "category":row["category"], "progress":row["progress_percent"]/100, "status":row["status"], "done":row["status"]=="completed"} for row in get_progress(user_id)]
        st.session_state.db_goals_loaded = True

def load_styles():
    st.markdown("""<style>
    /* Visual direction adapted from unslop by Damir Sokolovsky, CC BY 4.0 */
    :root{--ink:#ededed;--muted:#a1a1a6;--quiet:#85858b;--lime:#a9bf8b;--green:#8ea77a;--panel:#1b1b1d;--line:rgba(237,237,237,.09);--evergreen-card:#1b1b1d;--evergreen-radius:14px;--ease:cubic-bezier(.22,1,.36,1)}
    html,body,[data-testid="stAppViewContainer"]{font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink)}
    .stApp{background:#141415;color:var(--ink)}
    [data-testid="stHeader"]{background:#141415}
    [data-testid="stSidebar"]{background:#111112;border-right:1px solid var(--line);min-width:260px;max-width:260px}
    [data-testid="stSidebar"] *{color:var(--ink)}
    [data-testid="stSidebar"] [aria-checked="true"]{background:#232522;border-radius:8px}
    [data-testid="stMainBlockContainer"]{max-width:1520px;padding:32px 32px 48px}
    [data-testid="stMainBlockContainer"] h1,[data-testid="stMainBlockContainer"] h2,[data-testid="stMainBlockContainer"] h3{color:var(--ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;font-weight:500;letter-spacing:0}
    [data-testid="stMainBlockContainer"] h1{font-size:clamp(28px,3vw,36px);line-height:1.15;margin:0 0 8px}
    [data-testid="stMainBlockContainer"] h2{font-size:24px;line-height:1.25;margin-top:24px}
    [data-testid="stMainBlockContainer"] h3{font-size:18px;line-height:1.3}
    [data-testid="stMainBlockContainer"] h4{font-size:16px;line-height:1.35;font-weight:500}
    .page-kicker{margin:0 0 8px;color:var(--muted);font-size:13px;font-weight:400;letter-spacing:0;text-transform:none}
    .page-lede{max-width:720px;margin:4px 0 24px;color:var(--muted);font-size:14px;line-height:1.5}
    p,small,.stCaption{color:var(--muted)}
    .brand{display:flex;align-items:center;gap:10px;font-size:18px;font-weight:500;letter-spacing:0;color:var(--ink)}
    .brand:before{content:"";width:8px;height:14px;border-radius:8px 2px 8px 2px;background:var(--lime);transform:rotate(28deg)}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{font-size:13px;letter-spacing:0;color:var(--muted)}
    .card{background:var(--evergreen-card);border:1px solid var(--line);border-radius:14px;padding:20px;min-height:120px}
    [data-testid="stVerticalBlockBorderWrapper"]{border:1px solid var(--line)!important;border-radius:14px!important;background:#19191b!important;box-shadow:none!important;transition:border-color .16s var(--ease)}
    [data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:rgba(237,237,237,.16)!important}
    .label{font-size:13px;color:var(--muted);font-weight:400;letter-spacing:0}
    .value{font-size:28px;font-weight:500;color:var(--ink);margin:8px 0;font-variant-numeric:tabular-nums}
    .green{color:var(--lime);font-weight:500;font-size:13px}
    .tag{background:#242623;color:#d6dfcc;border:1px solid var(--line);border-radius:6px;padding:4px 8px;font-size:12px;font-weight:400}
    [data-testid="stMetric"]{background:#19191b;border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:none}
    [data-testid="stMetricLabel"]{color:var(--muted);font-size:13px}
    [data-testid="stMetricValue"]{color:var(--ink);font-size:28px;font-weight:500;font-variant-numeric:tabular-nums}
    [data-testid="stMetricDelta"]{font-size:13px}
    .stButton>button,.stDownloadButton>button{min-height:36px;border-radius:8px;border:1px solid var(--line);background:#232325;color:var(--ink);font-weight:500;transition:background-color .16s var(--ease),border-color .16s var(--ease),color .16s var(--ease)}
    .stButton>button:hover,.stDownloadButton>button:hover{background:#2a2a2c;border-color:rgba(237,237,237,.18);color:#fff}
    .stButton>button:active,.stDownloadButton>button:active{transform:scale(.98)}
    .stButton>button[kind="primary"]{background:#ededed;border-color:#ededed;color:#171719}
    .stButton>button[kind="primary"]:hover{background:#fff;border-color:#fff;color:#111112}
    button:focus-visible,[role="radio"]:focus-visible,input:focus-visible{outline:2px solid var(--lime)!important;outline-offset:2px}
    [data-testid="stTabs"] [role="tablist"]{gap:16px;border-bottom:1px solid var(--line)}
    [data-testid="stTabs"] [role="tab"]{padding:10px 2px;border-radius:0;color:var(--muted);font-size:14px;transition:color .16s var(--ease),border-color .16s var(--ease)}
    [data-testid="stTabs"] [aria-selected="true"]{color:var(--ink);border-bottom:2px solid var(--lime);background:transparent}
    [data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"]>div>div,[data-testid="stTextArea"] textarea{background:#1b1b1d;color:var(--ink);border-color:var(--line);border-radius:8px}
    [data-testid="stExpander"]{background:#18181a;border:1px solid var(--line);border-radius:12px}
    [data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:10px;overflow:hidden}
    [data-testid="stPlotlyChart"]{max-width:100%;overflow:hidden;border:1px solid var(--line);border-radius:12px;background:#19191b;padding:8px}
    [data-testid="stProgress"]>div>div{background:#292b27;border-radius:4px}
    [data-testid="stProgress"]>div>div>div{background:var(--lime);border-radius:4px}
    .hero{background:#1b1b1d;border:1px solid var(--line);border-radius:14px;padding:32px;color:var(--ink)}
    .hero .eyebrow{font-size:13px;font-weight:400;letter-spacing:0;color:var(--muted)!important}
    .hero h1{color:var(--ink);font:400 clamp(32px,4vw,48px)/1.08 Georgia,"Times New Roman",serif;letter-spacing:-.02em}
    .hero p{max-width:420px;color:var(--muted);line-height:1.6}
    .calc-hero{padding:28px 32px;border:1px solid var(--line);border-left:3px solid var(--lime);border-radius:14px;background:#1b1b1d}
    .calc-kicker{color:var(--muted);font-size:13px;font-weight:400;letter-spacing:0;text-transform:none}
    .calc-hero h1{margin:12px 0 8px;color:var(--ink);font:400 clamp(32px,4vw,48px)/1.05 Georgia,"Times New Roman",serif;letter-spacing:-.02em}
    .calc-hero p{max-width:640px;margin:0;color:var(--muted);line-height:1.6}
    .calc-content{margin-top:24px}
    .calc-panel{padding:20px;border:1px solid var(--line);border-radius:14px;background:#19191b}
    .calc-section-label{color:var(--ink);font-size:16px;font-weight:500;letter-spacing:0}
    .calc-live{padding:20px;border:1px solid var(--line);border-radius:14px;background:#1b1b1d}
    .calc-live-label{color:var(--muted);font-size:13px;font-weight:400;letter-spacing:0;text-transform:none}
    .calc-live-value{margin:8px 0 4px;color:var(--lime);font:500 clamp(32px,4vw,44px)/1.1 Inter,system-ui,sans-serif;font-variant-numeric:tabular-nums;letter-spacing:0}
    .calc-live-note{color:var(--muted);font-size:13px}
    .calc-mini{height:100%;padding:16px;border:1px solid var(--line);border-radius:12px;background:#19191b}
    .calc-mini-label{color:var(--muted);font-size:13px;font-weight:400;letter-spacing:0;text-transform:none}
    .calc-mini-value{margin-top:8px;color:var(--ink);font-size:18px;font-weight:500;font-variant-numeric:tabular-nums}
    .evergreen-landing{position:relative;isolation:isolate;min-height:740px;overflow:hidden;border:1px solid rgba(255,255,255,.16);border-radius:16px;background-color:#718164;background-image:var(--hero-image);background-position:center 48%;background-size:cover;background-repeat:no-repeat;color:#151713}
    .evergreen-landing:before{content:"";position:absolute;inset:0;z-index:0;background:linear-gradient(180deg,rgba(244,242,229,.08) 0%,rgba(20,24,18,.04) 44%,rgba(13,18,14,.72) 100%);pointer-events:none}
    .evergreen-nav{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;gap:20px;padding:24px 28px}
    .evergreen-brand{display:inline-flex;align-items:center;gap:9px;font-size:17px;font-weight:500;letter-spacing:0;color:#151713;text-decoration:none;white-space:nowrap}
    .evergreen-brand b{display:inline-block;width:8px;height:14px;border-radius:8px 2px 8px 2px;background:#536b42;transform:rotate(28deg);font-size:0}
    .evergreen-menu{display:flex;align-items:center;gap:20px}
    .evergreen-menu a,.evergreen-start{padding:8px 0;border-radius:0;text-decoration:none;color:#23271f;font-size:14px;font-weight:400;transition:color .16s var(--ease)}
    .evergreen-menu a:hover{color:#000;text-decoration:underline;text-underline-offset:4px}
    .evergreen-menu .menu-current{color:#111;font-weight:500;text-decoration:underline;text-underline-offset:4px}
    .evergreen-start{padding:10px 16px;border-radius:8px;background:#171916;color:#f2f2ee;font-weight:500}
    .evergreen-start:hover{background:#30342d;color:#fff}
    .evergreen-copy{position:relative;z-index:2;max-width:800px;margin:52px auto 0;padding:0 24px;text-align:center}
    .evergreen-eyebrow{font-size:14px;font-weight:400;letter-spacing:0;color:#313c2a}
    .evergreen-copy h1{margin:20px 0 12px;font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(52px,7vw,80px);line-height:1;letter-spacing:-.03em;color:#10130f}
    .evergreen-copy h1 em{font-weight:400;color:#293425}
    .evergreen-copy p{max-width:540px;margin:16px auto 0;color:#263023;font-size:16px;line-height:1.6}
    .evergreen-actions{display:flex;justify-content:center;gap:12px;margin-top:24px}
    .evergreen-cta{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 18px;border-radius:8px;background:#171916;color:#f2f2ee;text-decoration:none;font-weight:500;transition:background-color .16s var(--ease),color .16s var(--ease)}
    .evergreen-cta:hover{background:#30342d;color:#fff}
    .evergreen-cta.secondary{background:rgba(245,245,237,.78);border:1px solid rgba(23,25,22,.18);color:#171916}
    .evergreen-cta.secondary:hover{background:#fff}
    .evergreen-cards{position:absolute;z-index:2;left:50%;bottom:28px;display:grid;grid-template-columns:1fr 1.18fr;gap:12px;width:min(800px,calc(100% - 48px));transform:translateX(-50%)}
    .evergreen-glass{min-height:132px;padding:20px;border:1px solid rgba(255,255,255,.1);border-radius:12px;background:rgba(24,26,23,.92);color:#ededed}
    .evergreen-glass h3{margin:0;color:#ededed;font:500 16px Inter,system-ui,sans-serif;letter-spacing:0}
    .evergreen-glass p{margin:8px 0;color:#b8b8b4;font-size:13px}
    .glass-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
    .glass-heading p{margin:4px 0 0}
    .tiny-arrow{color:#c8d4ba;font-size:13px;text-decoration:none}
    .tiny-arrow:hover{color:#fff;text-decoration:underline;text-underline-offset:3px}
    .step-count{font-size:13px;color:#b8b8b4;font-variant-numeric:tabular-nums}
    .quick-links{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:16px}
    .quick-links a{display:flex;align-items:center;gap:8px;padding:4px 0;color:#d8d8d4;text-decoration:none;font-size:13px;transition:color .16s var(--ease)}
    .quick-links a span{display:grid;place-items:center;width:24px;height:24px;flex:0 0 24px;border:1px solid rgba(255,255,255,.16);border-radius:6px;color:#c8d4ba;font-size:12px;font-weight:400;font-variant-numeric:tabular-nums}
    .quick-links a:hover{color:#fff}
    .goal-meter{height:4px;margin:12px 0 8px;border-radius:4px;background:rgba(255,255,255,.16);overflow:hidden}
    .goal-meter-fill{height:100%;border-radius:4px;background:var(--lime)}
    .empty-snapshot{display:flex;align-items:center;gap:12px;margin-top:16px;color:#c7c8c1;font-size:13px}
    .snapshot-orbit{display:block;width:8px;height:8px;flex:0 0 8px;border-radius:50%;background:var(--lime)}
    .impact-line{display:grid;grid-template-columns:88px 1fr 56px;align-items:center;gap:8px;margin:10px 0;font-size:12px;color:#c4c5bf;font-variant-numeric:tabular-nums}
    .impact-track{height:4px;border-radius:4px;background:rgba(255,255,255,.14);overflow:hidden}
    .impact-fill{height:100%;border-radius:4px;background:var(--lime)}
    .glass-foot{display:flex;justify-content:space-between;gap:8px;margin-top:12px;color:#aeb0a9;font-size:12px;font-variant-numeric:tabular-nums}
    .glass-foot strong{color:#e5e6e0;font-size:13px;font-weight:500}
    .landing-footnote{position:absolute;z-index:2;right:24px;bottom:8px;color:rgba(250,250,244,.76);font-size:12px}
    .journey-intro{max-width:720px;margin:80px auto 32px;text-align:center}
    .journey-intro>span{color:var(--muted);font-size:13px;font-weight:400;letter-spacing:0}
    .journey-intro h2{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(32px,5vw,52px);line-height:1.08;margin:16px 0}
    .journey-intro p{max-width:600px;margin:0 auto;color:var(--muted);line-height:1.6}
    .journey-card{height:100%;min-height:180px;padding:24px;border:1px solid var(--line);border-radius:12px;background:#19191b;transition:border-color .16s var(--ease),background-color .16s var(--ease)}
    .journey-card:hover{border-color:rgba(237,237,237,.18);background:#1d1d1f}
    .journey-card>span{display:block;margin-bottom:20px;color:var(--lime);font-size:13px;font-weight:400;font-variant-numeric:tabular-nums}
    .journey-card h3{margin:0 0 8px;color:var(--ink);font:500 20px Inter,system-ui,sans-serif;letter-spacing:0}
    .journey-card p{color:var(--muted);line-height:1.5;font-size:14px}
    @media(max-width:800px){.evergreen-landing{min-height:880px}.evergreen-nav{padding:20px 20px;flex-wrap:wrap}.evergreen-menu{order:3;width:100%;justify-content:center;gap:16px;overflow:auto}.evergreen-copy{margin-top:36px}.evergreen-copy h1{font-size:clamp(44px,11vw,64px)}.evergreen-cards{bottom:32px;grid-template-columns:1fr;width:calc(100% - 40px)}.evergreen-glass{min-height:104px}.journey-intro{margin-top:56px}}
    @media(max-width:420px){.evergreen-start{padding:10px 12px}.evergreen-copy{padding:0 16px}.evergreen-copy p{font-size:14px}.evergreen-actions{flex-direction:column;align-items:stretch}.evergreen-cards{bottom:24px}.quick-links{gap:4px}.quick-links a{font-size:12px}}
    @media(max-width:640px){[data-testid="stMainBlockContainer"]{padding:20px 16px 32px}[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:12px!important}[data-testid="stHorizontalBlock"]:has(>[data-testid="column"]:nth-child(4))>[data-testid="column"]{flex:1 1 calc(50% - 8px)!important;min-width:calc(50% - 8px)!important}[data-testid="stHorizontalBlock"]:not(:has(>[data-testid="column"]:nth-child(4)))>[data-testid="column"]{flex:1 1 100%!important;min-width:100%!important}.card{padding:16px;min-height:auto}.value{font-size:24px}.calc-hero{padding:24px 20px}.calc-panel{padding:16px}.stButton>button,.stDownloadButton>button{min-height:44px;white-space:normal}[data-testid="stTabs"] [role="tablist"]{overflow-x:auto;flex-wrap:nowrap!important}[data-testid="stTabs"] [role="tab"]{white-space:nowrap}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition-duration:.01ms!important}}

    /* Evergreen application palette adapted from the supplied design direction. */
    :root{--ink:#f2f5eb;--muted:#b7bda5;--quiet:#8c9781;--lime:#68ef3f;--green:#26a200;--panel:#273f2b;--line:rgba(242,245,235,.13);--evergreen-card:#1b3020;--canvas:#122314;--ease:cubic-bezier(.22,1,.36,1)}
    html,body,[data-testid="stAppViewContainer"]{color:var(--ink);background:#122314;font-family:"Aeonik","Inter",Arial,sans-serif}
    .stApp{color:var(--ink);background:#122314}
    [data-testid="stHeader"]{background:rgba(18,35,20,.96)}
    [data-testid="stMainBlockContainer"]{background:transparent}
    [data-testid="stSidebar"]{background:#0d1d11;border-right:1px solid rgba(242,245,235,.1)}
    [data-testid="stSidebar"] *{color:#f2f5eb}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#b7bda5;font-size:13px;letter-spacing:0}
    [data-testid="stSidebar"] [aria-checked="true"]{background:#273f2b;border-radius:8px}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.07);border-radius:8px}
    [data-testid="stMainBlockContainer"] h1,[data-testid="stMainBlockContainer"] h2,[data-testid="stMainBlockContainer"] h3,[data-testid="stMainBlockContainer"] h4{color:#f2f5eb}
    [data-testid="stMainBlockContainer"] h1{font-family:"Ozik","Lilita One","Arial Narrow",Impact,sans-serif;font-weight:700;text-transform:uppercase;letter-spacing:-.01em;line-height:.98}
    [data-testid="stMainBlockContainer"] h2{font-family:"Aeonik","Inter",Arial,sans-serif;font-weight:500;letter-spacing:-.012em}
    p,small,.stCaption{color:#b7bda5}
    .page-kicker,.calc-kicker{color:#68ef3f}
    .brand{color:#f2f5eb}
    .brand:before{background:#68ef3f}
    .card{background:#1b3020;border:1px solid rgba(242,245,235,.12);box-shadow:none}
    [data-testid="stVerticalBlockBorderWrapper"]{background:#1b3020!important;border-color:rgba(242,245,235,.12)!important;box-shadow:none!important;transition:transform .18s var(--ease),border-color .18s var(--ease),background-color .18s var(--ease)}
    [data-testid="stVerticalBlockBorderWrapper"]:hover{transform:translateY(-2px);background:#203724!important;border-color:rgba(104,239,63,.42)!important;box-shadow:0 10px 24px rgba(0,0,0,.16)!important}
    .metric-card{min-height:136px;border-width:1px 1px 1px 4px;border-style:solid;border-radius:12px;padding:18px 18px 16px;transition:transform .18s var(--ease),border-color .18s var(--ease)}
    .metric-card:hover{transform:translateY(-3px);border-color:rgba(104,239,63,.5)}
    .metric-card .label{color:#b7bda5;font-size:13px}
    .metric-card .value{color:#f2f5eb;font-size:28px}
    .metric-card .green{color:#68ef3f}
    .metric-card.forest{background:#1b3520;border-color:rgba(183,189,165,.12) rgba(183,189,165,.12) rgba(183,189,165,.12) #68ef3f}
    .metric-card.leaf{background:#273b22;border-color:rgba(183,189,165,.12) rgba(183,189,165,.12) rgba(183,189,165,.12) #9fcf4d}
    .metric-card.water{background:#1b3732;border-color:rgba(183,189,165,.12) rgba(183,189,165,.12) rgba(183,189,165,.12) #62c7a7}
    .metric-card.sun{background:#3b3320;border-color:rgba(183,189,165,.12) rgba(183,189,165,.12) rgba(183,189,165,.12) #e4b85b}
    [data-testid="stMetric"]{background:#1b3020;border:1px solid rgba(242,245,235,.12);border-left:3px solid #68ef3f;border-radius:12px;padding:16px;box-shadow:none}
    [data-testid="stMetricLabel"]{color:#b7bda5}
    [data-testid="stMetricValue"]{color:#f2f5eb}
    [data-testid="stMetricDelta"]{color:#b7bda5}
    .tag{background:#273f2b;color:#dce8d2;border-color:rgba(242,245,235,.14);border-radius:6px}
    .tag-transport{background:#24452b;color:#a8e7a1;border-color:#3e6844}
    .tag-energy{background:#3a4022;color:#d9eb8c;border-color:#69733a}
    .tag-water{background:#1d403a;color:#8fdbca;border-color:#356c62}
    .tag-food{background:#46351f;color:#f0c78a;border-color:#77552f}
    .tag-waste{background:#2c4227;color:#bbd99e;border-color:#4b7040}
    .tag-shopping{background:#3d2c3a;color:#dfb5d4;border-color:#694963}
    .stButton>button,.stDownloadButton>button{min-height:44px;border-radius:999px;border:1px solid rgba(242,245,235,.18);background:#273f2b;color:#f2f5eb;font-weight:500;transition:transform .16s var(--ease),background-color .16s var(--ease),border-color .16s var(--ease),box-shadow .16s var(--ease)}
    .stButton>button:hover,.stDownloadButton>button:hover{background:#3e5b43;border-color:#68ef3f;color:#fff;box-shadow:0 5px 16px rgba(0,0,0,.2)}
    .stButton>button:active,.stDownloadButton>button:active{transform:scale(.98)}
    .stButton>button[kind="primary"]{background:#68ef3f;border-color:#68ef3f;color:#122314;font-weight:600}
    .stButton>button[kind="primary"]:hover{background:#83ff60;border-color:#83ff60;color:#122314}
    button:focus-visible,[role="radio"]:focus-visible,input:focus-visible{outline:2px solid #68ef3f!important;outline-offset:2px}
    [data-testid="stTabs"] [role="tablist"]{border-color:rgba(242,245,235,.14)}
    [data-testid="stTabs"] [role="tab"]{color:#b7bda5}
    [data-testid="stTabs"] [aria-selected="true"]{color:#68ef3f;border-bottom-color:#68ef3f;background:transparent}
    [data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{background:#273f2b!important;color:#f2f5eb!important;border-color:#526b53!important;border-radius:8px}
    [data-testid="stSelectbox"] [data-baseweb="select"]>div,[data-testid="stMultiSelect"] [data-baseweb="select"]>div{background:#273f2b!important;color:#f2f5eb!important;border-color:#526b53!important;border-radius:8px}
    [data-testid="stSelectbox"] svg,[data-testid="stMultiSelect"] svg{fill:#b7bda5}
    [data-testid="stNumberInput"] button{background:#3e5b43!important;color:#f2f5eb!important;border-color:#526b53!important}
    [role="listbox"],[role="option"]{background:#273f2b!important;color:#f2f5eb!important}
    [role="option"]:hover,[role="option"][aria-selected="true"]{background:#3e5b43!important;color:#fff!important}
    input::placeholder,textarea::placeholder{color:#b7bda5!important;opacity:.76}
    input[type="checkbox"],input[type="radio"]{accent-color:#68ef3f}
    [data-testid="stSlider"] [role="slider"]{background:#68ef3f;border-color:#68ef3f}
    [data-testid="stExpander"]{background:#1b3020;border:1px solid rgba(242,245,235,.12);border-radius:12px}
    [data-testid="stDataFrame"]{border:1px solid rgba(242,245,235,.14);border-radius:10px;overflow:hidden}
    [data-testid="stPlotlyChart"]{max-width:100%;overflow:hidden;border:1px solid rgba(242,245,235,.12);border-radius:12px;background:#1b3020;padding:8px}
    [data-testid="stProgress"]>div>div{background:#3e5b43;border-radius:4px}
    [data-testid="stProgress"]>div>div>div{background:#68ef3f;border-radius:4px}
    .hero{background:#273f2b;border:1px solid rgba(242,245,235,.14);border-radius:14px;padding:32px;color:#f2f5eb}
    .hero .eyebrow{font-size:13px;font-weight:400;letter-spacing:0;color:#b7bda5!important}
    .hero h1{color:#f2f5eb;font:700 clamp(32px,4vw,48px)/.98 "Arial Narrow",Impact,sans-serif;text-transform:uppercase;letter-spacing:-.01em}
    .hero p{max-width:420px;color:#c6cfba;line-height:1.6}
    .calc-hero{padding:28px 32px;border:1px solid rgba(242,245,235,.14);border-left:4px solid #68ef3f;border-radius:14px;background:#273f2b}
    .calc-kicker{color:#b7bda5;font-size:13px;font-weight:400;letter-spacing:0;text-transform:none}
    .calc-hero h1{margin:12px 0 8px;color:#f2f5eb;font:700 clamp(32px,4vw,48px)/.98 "Arial Narrow",Impact,sans-serif;text-transform:uppercase;letter-spacing:-.01em}
    .calc-hero p{max-width:640px;margin:0;color:#c6cfba;line-height:1.6}
    .calc-section-label{color:#f2f5eb;font-size:16px;font-weight:500;letter-spacing:0}
    .calc-live{padding:20px;border:1px solid rgba(104,239,63,.42);border-radius:14px;background:#3e5b43;box-shadow:none}
    .calc-live-label,.calc-live-note{color:#d9e6d3}
    .calc-live-value{color:#68ef3f}
    .calc-mini{background:#1b3020;border-color:rgba(242,245,235,.12);box-shadow:none;transition:transform .16s var(--ease),border-color .16s var(--ease)}
    .calc-mini:hover{transform:translateY(-2px);border-color:rgba(104,239,63,.42);box-shadow:none}
    .calc-mini.transport{background:#1b3520;border-color:rgba(183,189,165,.16);border-top:3px solid #68ef3f}
    .calc-mini.energy{background:#303c20;border-color:rgba(183,189,165,.16);border-top:3px solid #c9e75c}
    .calc-mini.food{background:#40321f;border-color:rgba(183,189,165,.16);border-top:3px solid #e3ab58}
    .calc-mini-label{color:#b7bda5}
    .calc-mini-value{color:#f2f5eb}
    .journey-intro>span{color:#68ef3f}
    .journey-intro h2{color:#f2f5eb}
    .journey-card{border-color:rgba(242,245,235,.12);background:#1b3020;box-shadow:none;transition:transform .18s var(--ease),border-color .18s var(--ease),background-color .18s var(--ease)}
    .journey-card:hover{transform:translateY(-4px);border-color:rgba(104,239,63,.42);background:#203724;box-shadow:none}
    .journey-card>span{color:#68ef3f}
    .journey-card h3{color:#f2f5eb}
    .journey-card p{color:#b7bda5}
    .journey-01{background:#1b3520;border-top:3px solid #68ef3f}
    .journey-02{background:#303c20;border-top:3px solid #c9e75c}
    .journey-03{background:#1b3732;border-top:3px solid #62c7a7}
    .evergreen-landing{min-height:820px}
    .evergreen-landing .evergreen-nav a,.evergreen-landing .evergreen-cards a{color:#122314!important;text-decoration:none!important}
    .evergreen-landing .evergreen-nav .evergreen-brand{color:#122314!important;font-weight:600}
    .evergreen-landing .evergreen-nav .evergreen-menu a:hover,.evergreen-landing .evergreen-nav .evergreen-menu .menu-current{color:#122314!important;text-decoration:underline!important;text-decoration-color:#26a200!important;text-underline-offset:5px}
    .evergreen-landing .evergreen-nav .evergreen-start{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:0 20px;background:#122314!important;color:#f2f5eb!important;border-radius:999px}
    .evergreen-landing .evergreen-nav .evergreen-start:hover{background:#3e5b43!important;color:#68ef3f!important}
    .evergreen-landing .evergreen-copy{margin-top:34px;max-width:880px}
    .evergreen-landing .evergreen-copy h1{margin:14px 0 10px;font-family:"Ozik","Lilita One","Arial Narrow",Impact,sans-serif;font-weight:700;font-size:clamp(48px,5.2vw,72px);line-height:.94;letter-spacing:-.015em;text-transform:uppercase;text-wrap:balance;color:#122314!important;text-shadow:none}
    .evergreen-landing .evergreen-copy h1 em{color:#203a25!important;font-style:italic}
    .evergreen-landing .evergreen-copy p{max-width:600px;margin:14px auto 0;color:#273f2b;font-size:16px;line-height:1.5}
    .evergreen-landing .evergreen-eyebrow{color:#273f2b;font-size:14px;font-weight:500}
    .evergreen-landing .evergreen-actions{gap:14px;margin-top:18px}
    .evergreen-landing .evergreen-cta{min-height:46px;padding:0 20px;border-radius:999px;background:#68ef3f!important;color:#122314!important;font-weight:600}
    .evergreen-landing .evergreen-cta:hover{background:#83ff60!important;color:#122314!important;transform:translateY(-1px)}
    .evergreen-landing .evergreen-cta.secondary{background:rgba(242,245,235,.9)!important;border:1px solid rgba(18,35,20,.24);color:#122314!important}
    .evergreen-landing .evergreen-cta.secondary:hover{background:#fff!important}
    .evergreen-landing .evergreen-cards{bottom:30px;width:min(840px,calc(100% - 48px));gap:14px}
    .evergreen-landing .evergreen-glass{min-height:0;padding:16px;border-radius:12px;background:rgba(13,29,17,.95)}
    .evergreen-landing .quick-links{margin-top:12px}
    .evergreen-landing .goal-meter{margin:10px 0 7px}
    .evergreen-landing .evergreen-cards .tiny-arrow{color:#68ef3f!important}
    .evergreen-landing .quick-links a{color:#f2f5eb!important}
    .evergreen-landing .quick-links a span{color:#68ef3f!important}
    .evergreen-landing .landing-footnote{color:#f2f5eb;font-size:11px}
    @media(max-width:800px){.evergreen-landing{min-height:1010px}.evergreen-landing .evergreen-copy{margin-top:26px}.evergreen-landing .evergreen-copy h1{font-size:clamp(42px,9vw,64px)}.evergreen-landing .evergreen-cards{bottom:24px;width:calc(100% - 40px);grid-template-columns:1fr}.evergreen-landing .evergreen-glass{padding:15px}}
    @media(max-width:480px){.evergreen-landing{min-height:1080px}.evergreen-landing .evergreen-nav{gap:12px;padding:16px}.evergreen-landing .evergreen-menu{justify-content:flex-start;gap:14px}.evergreen-landing .evergreen-menu a{font-size:12px}.evergreen-landing .evergreen-copy{margin-top:22px;padding:0 16px}.evergreen-landing .evergreen-copy h1{font-size:clamp(38px,11vw,52px)}.evergreen-landing .evergreen-copy p{font-size:14px}.evergreen-landing .evergreen-actions{flex-direction:column;align-items:stretch}.evergreen-landing .evergreen-cards{width:calc(100% - 28px);bottom:20px}.evergreen-landing .quick-links{grid-template-columns:repeat(3,minmax(0,1fr))}.evergreen-landing .quick-links a{font-size:11px;gap:5px}.evergreen-landing .quick-links a span{width:22px;height:22px;flex-basis:22px}}
    @media(max-width:640px){.metric-card{min-height:120px;padding:15px}.calc-live{padding:18px}}
    @media(prefers-reduced-motion:reduce){[data-testid="stVerticalBlockBorderWrapper"],.metric-card,.calc-mini,.journey-card,.stButton>button,.stDownloadButton>button{transition:none!important}.metric-card:hover,.calc-mini:hover,.journey-card:hover,[data-testid="stVerticalBlockBorderWrapper"]:hover{transform:none}}
    </style>""", unsafe_allow_html=True)
