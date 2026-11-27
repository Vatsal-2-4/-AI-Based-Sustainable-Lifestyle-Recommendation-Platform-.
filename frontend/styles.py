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

    /* Brighter application surfaces carry the landscape palette into the tools. */
    :root{--ink:#20372a;--muted:#68796c;--quiet:#839087;--lime:#a7c65f;--green:#32774a;--panel:#fffefa;--line:#dce6d9;--evergreen-card:#fffefa;--canvas:#f3f6ef}
    html,body,[data-testid="stAppViewContainer"]{color:var(--ink);background:var(--canvas)}
    .stApp{color:var(--ink);background:#f3f6ef}
    [data-testid="stHeader"]{background:rgba(243,246,239,.94)}
    [data-testid="stSidebar"]{background:#173d2b;border-right:1px solid #28563a}
    [data-testid="stSidebar"] *{color:#edf3e9}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#b9cbb9;font-size:13px;letter-spacing:0}
    [data-testid="stSidebar"] [aria-checked="true"]{background:#2b6042;border-radius:8px}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.07);border-radius:8px}
    [data-testid="stMainBlockContainer"] h1,[data-testid="stMainBlockContainer"] h2,[data-testid="stMainBlockContainer"] h3,[data-testid="stMainBlockContainer"] h4{color:var(--ink)}
    p,small,.stCaption{color:var(--muted)}
    .page-kicker,.calc-kicker{color:#567a55}
    .brand{color:#f2f5ed}
    .brand:before{background:#bfdc70}
    .card{background:#fffefa;border:1px solid #dce6d9;box-shadow:0 5px 18px rgba(38,75,48,.045)}
    [data-testid="stVerticalBlockBorderWrapper"]{background:#fffefa!important;border-color:#dce6d9!important;box-shadow:0 5px 18px rgba(38,75,48,.045)!important;transition:transform .18s var(--ease),box-shadow .18s var(--ease),border-color .18s var(--ease)}
    [data-testid="stVerticalBlockBorderWrapper"]:hover{transform:translateY(-2px);border-color:#a7c194!important;box-shadow:0 10px 24px rgba(38,75,48,.09)!important}
    .metric-card{min-height:136px;border-width:1px 1px 1px 4px;border-style:solid;border-radius:12px;padding:18px 18px 16px;transition:transform .18s var(--ease),box-shadow .18s var(--ease)}
    .metric-card:hover{transform:translateY(-3px);box-shadow:0 12px 24px rgba(38,75,48,.1)}
    .metric-card .label{color:#617264;font-size:13px}
    .metric-card .value{color:#20372a;font-size:28px}
    .metric-card .green{color:#557a4b}
    .metric-card.forest{background:#e8f1e6;border-color:#cbdcc6 #cbdcc6 #cbdcc6 #397b4e}
    .metric-card.leaf{background:#f0f4dc;border-color:#e0e7bc #e0e7bc #e0e7bc #9aa83f}
    .metric-card.water{background:#e6f1ef;border-color:#cce2dc #cce2dc #cce2dc #5b9a95}
    .metric-card.sun{background:#f8eee0;border-color:#eedfc8 #eedfc8 #eedfc8 #c58245}
    [data-testid="stMetric"]{background:#fffefa;border:1px solid #dce6d9;border-left:4px solid #7ba46a;border-radius:12px;padding:16px;box-shadow:0 4px 14px rgba(38,75,48,.045)}
    [data-testid="stMetricLabel"]{color:#68796c}
    [data-testid="stMetricValue"]{color:#20372a}
    .tag{background:#edf4e8;color:#3b6d43;border-color:#d8e6d0;border-radius:6px}
    .tag-transport{background:#e6f1e7;color:#2f7144;border-color:#cde1d0}
    .tag-energy{background:#f1f4dc;color:#6e7d2f;border-color:#e1e7b8}
    .tag-water{background:#e5f1ef;color:#367b76;border-color:#cde4e0}
    .tag-food{background:#f7eddf;color:#95602f;border-color:#ecdcc4}
    .tag-waste{background:#e8f0e4;color:#557b45;border-color:#d5e3cc}
    .tag-shopping{background:#f3eaf0;color:#865d78;border-color:#e7d8e1}
    .stButton>button,.stDownloadButton>button{background:#fffefa;color:#24432e;border-color:#bfd0bb;transition:transform .16s var(--ease),background-color .16s var(--ease),border-color .16s var(--ease),box-shadow .16s var(--ease)}
    .stButton>button:hover,.stDownloadButton>button:hover{background:#edf4e8;border-color:#6d9b62;color:#173d2b;box-shadow:0 4px 12px rgba(38,75,48,.1)}
    .stButton>button[kind="primary"]{background:#286a40;border-color:#286a40;color:#fff}
    .stButton>button[kind="primary"]:hover{background:#1f5835;border-color:#1f5835;color:#fff}
    button:focus-visible,[role="radio"]:focus-visible,input:focus-visible{outline:2px solid #4f8a57!important;outline-offset:2px}
    [data-testid="stTabs"] [role="tablist"]{border-color:#dce6d9}
    [data-testid="stTabs"] [role="tab"]{color:#68796c}
    [data-testid="stTabs"] [aria-selected="true"]{color:#286a40;border-bottom-color:#75a94f}
    [data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"]>div>div,[data-testid="stTextArea"] textarea{background:#fffefa;color:#20372a;border-color:#ccd9cb}
    [data-testid="stExpander"]{background:#fffefa;border-color:#dce6d9}
    [data-testid="stDataFrame"]{border-color:#dce6d9}
    [data-testid="stPlotlyChart"]{background:#fffefa;border-color:#dce6d9;box-shadow:0 5px 16px rgba(38,75,48,.04)}
    [data-testid="stProgress"]>div>div{background:#e2eadf}
    [data-testid="stProgress"]>div>div>div{background:#6b9e4f}
    .hero{background:#e7f0df;border-color:#d3e2cb;color:#20372a}
    .hero .eyebrow{color:#58734e!important}
    .hero h1{color:#20372a}
    .hero p{color:#5d705f}
    .calc-hero{background:#e7f0df;border-color:#d3e2cb;border-left-color:#568846}
    .calc-kicker{color:#567a55}
    .calc-hero h1{color:#20372a}
    .calc-hero p{color:#5d705f}
    .calc-section-label{color:#294630}
    .calc-live{background:#205d38;border-color:#205d38;box-shadow:0 10px 24px rgba(32,93,56,.15)}
    .calc-live-label,.calc-live-note{color:#d2e2cd}
    .calc-live-value{color:#cce47d}
    .calc-mini{background:#fffefa;border-color:#dce6d9;box-shadow:0 4px 14px rgba(38,75,48,.045);transition:transform .16s var(--ease),box-shadow .16s var(--ease)}
    .calc-mini:hover{transform:translateY(-2px);box-shadow:0 9px 18px rgba(38,75,48,.09)}
    .calc-mini.transport{background:#e8f1e6;border-color:#cbdcc6;border-top:3px solid #397b4e}
    .calc-mini.energy{background:#f0f4dc;border-color:#e0e7bc;border-top:3px solid #9aa83f}
    .calc-mini.food{background:#f8eee0;border-color:#eedfc8;border-top:3px solid #c58245}
    .calc-mini-label{color:#68796c}
    .calc-mini-value{color:#20372a}
    .journey-intro>span{color:#57784e}
    .journey-intro h2{color:#24402e}
    .journey-card{border-color:#dce6d9;background:#fffefa;box-shadow:0 5px 16px rgba(38,75,48,.045);transition:transform .18s var(--ease),box-shadow .18s var(--ease),border-color .18s var(--ease)}
    .journey-card:hover{transform:translateY(-4px);border-color:#b8cca9;background:#fffefa;box-shadow:0 13px 24px rgba(38,75,48,.1)}
    .journey-card>span{color:#397b4e}
    .journey-card h3{color:#243d2c}
    .journey-card p{color:#68796c}
    .journey-01{background:#e9f2e6;border-top:3px solid #397b4e}
    .journey-02{background:#f1f4dc;border-top:3px solid #9aa83f}
    .journey-03{background:#e7f1ef;border-top:3px solid #5b9a95}
    @media(max-width:640px){.metric-card{min-height:120px;padding:15px}.calc-live{padding:18px}}
    @media(prefers-reduced-motion:reduce){[data-testid="stVerticalBlockBorderWrapper"],.metric-card,.calc-mini,.journey-card,.stButton>button,.stDownloadButton>button{transition:none!important}.metric-card:hover,.calc-mini:hover,.journey-card:hover,[data-testid="stVerticalBlockBorderWrapper"]:hover{transform:none}}
    </style>""", unsafe_allow_html=True)
