
import streamlit as st
import requests
import unicodedata
import concurrent.futures
from datetime import datetime, timedelta
from itertools import groupby
from fuzzywuzzy import fuzz

st.set_page_config(page_title="MX Athlete Tracker", page_icon="🇲🇽", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0a0a0a; color: #f0f0f0; }
  .main { background-color: #0a0a0a; }
  .block-container { padding-top: 2rem; max-width: 1200px; }
  .hero { background: linear-gradient(135deg, #006847 0%, #0a0a0a 50%, #CE1126 100%); border-radius: 16px; padding: 2.5rem 3rem; margin-bottom: 2rem; position: relative; overflow: hidden; }
  .hero::before { content: "🇲🇽"; font-size: 180px; position: absolute; right: -20px; top: -20px; opacity: 0.08; }
  .hero h1 { font-family: 'Bebas Neue', sans-serif; font-size: 3.5rem; letter-spacing: 3px; margin: 0; color: #ffffff; line-height: 1; }
  .hero p { color: #aaaaaa; font-size: 1rem; margin-top: 0.5rem; font-weight: 300; }
  .hero .updated { font-size: 0.75rem; color: #666; margin-top: 1rem; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
  .badge-liv { background: #1a1a2e; color: #4fc3f7; border: 1px solid #4fc3f7; }
  .badge-pga { background: #1a2e1a; color: #66bb6a; border: 1px solid #66bb6a; }
  .badge-kft { background: #2e2a1a; color: #ffa726; border: 1px solid #ffa726; }
  .badge-pta { background: #2e1a2e; color: #ce93d8; border: 1px solid #ce93d8; }
  .badge-lpga { background: #1a1a2e; color: #f48fb1; border: 1px solid #f48fb1; }
  .badge-other { background: #1a1a1a; color: #aaaaaa; border: 1px solid #444; }
  .event-card { background: #141414; border: 1px solid #222; border-left: 4px solid #006847; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; }
  .event-card .event-name { font-size: 1rem; font-weight: 600; color: #f0f0f0; margin: 0 0 0.25rem 0; }
  .event-card .event-meta { font-size: 0.8rem; color: #888; margin: 0; }
  .event-card .event-date { font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem; color: #006847; letter-spacing: 1px; }
  .metric-box { background: #141414; border: 1px solid #222; border-radius: 10px; padding: 1rem; text-align: center; }
  .metric-box .metric-val { font-family: 'Bebas Neue', sans-serif; font-size: 2.2rem; color: #006847; line-height: 1; }
  .metric-box .metric-label { font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.25rem; }
  section[data-testid="stSidebar"] { background-color: #0f0f0f; border-right: 1px solid #1e1e1e; }
  .no-results { text-align: center; padding: 3rem; color: #444; font-size: 1rem; }
  #MainMenu, footer, header { visibility: hidden; }
  .upcoming-pill { background: #006847; color: white; border-radius: 20px; padding: 2px 8px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
  .past-pill { background: #222; color: #666; border-radius: 20px; padding: 2px 8px; font-size: 0.65rem; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

PGA_HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "x-api-key": "da2-gsrx5bibzbb4njvhl7t37wqyl4"}

DEFAULT_MEXICAN_GOLFERS = [
    "Abraham Ancer","Carlos Ortiz","Álvaro Ortiz","Rodolfo Cazaubon",
    "José de Jesús Rodríguez","Roberto Díaz","Santiago de La Fuente",
    "Emilio Gonzalez","Raul Pereda","Jose Cristobal Islas","Omar Morales",
    "Luis Carrera","Sebastian Vazquez","Julio Arronte","Yael Chahin",
    "Gaby Lopez","Isabella Fierro","Lauren Olivares","Maria Fassi",
]


LPGA_SCHEDULE_2026 = [
    {"name": "Hilton Grand Vacations Tournament of Champions", "start_date": "2026-02-01", "location": "Florida, USA",      "purse": "$2,100,000"},
    {"name": "Honda LPGA Thailand",                            "start_date": "2026-02-22", "location": "Thailand",           "purse": "$1,800,000"},
    {"name": "HSBC Women's World Championship",                "start_date": "2026-03-01", "location": "Singapore",          "purse": "$3,000,000"},
    {"name": "Blue Bay LPGA",                                  "start_date": "2026-03-08", "location": "China",              "purse": "$2,600,000"},
    {"name": "Fortinet Founders Cup",                          "start_date": "2026-03-22", "location": "California, USA",    "purse": "$3,000,000"},
    {"name": "Ford Championship",                              "start_date": "2026-03-29", "location": "Arizona, USA",       "purse": "$2,250,000"},
    {"name": "Aramco Championship",                            "start_date": "2026-04-05", "location": "Nevada, USA",        "purse": "$4,000,000"},
    {"name": "JM Eagle LA Championship",                       "start_date": "2026-04-19", "location": "California, USA",    "purse": "$3,750,000"},
    {"name": "Chevron Championship",                           "start_date": "2026-04-26", "location": "Texas, USA",         "purse": "$8,000,000"},
    {"name": "Riviera Maya Open",                              "start_date": "2026-05-03", "location": "Mexico",             "purse": "$2,500,000"},
    {"name": "Mizuho Americas Open",                           "start_date": "2026-05-10", "location": "New Jersey, USA",    "purse": "$3,250,000"},
    {"name": "Kroger Queen City Championship",                 "start_date": "2026-05-17", "location": "Ohio, USA",          "purse": "$2,000,000"},
    {"name": "ShopRite LPGA Classic",                          "start_date": "2026-05-31", "location": "New Jersey, USA",    "purse": "$2,000,000"},
    {"name": "U.S. Women Open",                                "start_date": "2026-06-07", "location": "California, USA",    "purse": "$12,000,000"},
    {"name": "Meijer LPGA Classic",                            "start_date": "2026-06-15", "location": "Michigan, USA",      "purse": "$3,000,000"},
    {"name": "Dow Championship",                               "start_date": "2026-06-21", "location": "Michigan, USA",      "purse": "$3,250,000"},
    {"name": "KPMG Women PGA Championship",                    "start_date": "2026-06-28", "location": "Minnesota, USA",     "purse": "$12,000,000"},
    {"name": "Amundi Evian Championship",                      "start_date": "2026-07-12", "location": "France",             "purse": "$8,000,000"},
    {"name": "ISPS Handa Women Scottish Open",                 "start_date": "2026-07-26", "location": "Scotland",           "purse": "$2,000,000"},
    {"name": "AIG Women Open",                                 "start_date": "2026-08-02", "location": "Wales",              "purse": "$9,750,000"},
    {"name": "Portland Classic",                               "start_date": "2026-08-16", "location": "Oregon, USA",        "purse": "$2,000,000"},
    {"name": "CPKC Women Open",                                "start_date": "2026-08-23", "location": "Canada",             "purse": "$2,750,000"},
    {"name": "FM Championship",                                "start_date": "2026-08-30", "location": "Massachusetts, USA", "purse": "$4,400,000"},
    {"name": "Walmart NW Arkansas Championship",               "start_date": "2026-09-27", "location": "Arkansas, USA",      "purse": "$3,000,000"},
    {"name": "Lotte Championship",                             "start_date": "2026-10-04", "location": "Hawaii, USA",        "purse": "$3,000,000"},
    {"name": "Buick LPGA Shanghai",                            "start_date": "2026-10-18", "location": "China",              "purse": "$3,200,000"},
    {"name": "BMW Ladies Championship",                        "start_date": "2026-10-25", "location": "South Korea",        "purse": "$2,350,000"},
    {"name": "Maybank Championship",                           "start_date": "2026-11-01", "location": "Malaysia",           "purse": "$3,000,000"},
    {"name": "Toto Japan Classic",                             "start_date": "2026-11-08", "location": "Japan",              "purse": "$2,100,000"},
    {"name": "The Annika",                                     "start_date": "2026-11-15", "location": "Florida, USA",       "purse": "$3,250,000"},
    {"name": "CME Group Tour Championship",                    "start_date": "2026-11-22", "location": "Florida, USA",       "purse": "$11,000,000"},
]

LPGA_MEXICAN_PLAYERS = [
    "Gaby Lopez",
    "Maria Fassi",
    "Isabella Fierro",
    "Lauren Olivares",
]

LPGA_BUILD_BLOCK = True  # marker

LIV_ROSTER_2026 = [
    "Joaquin Niemann","Abraham Ancer","Sebastian Munoz","Carlos Ortiz",
    "Dustin Johnson","Thomas Detry","Thomas Pieters","Anthony Kim",
    "Bryson DeChambeau","Charles Howell III","Anirban Lahiri","Sergio Garcia",
    "David Puig","Phil Mickelson","Brendan Steele","Jon Rahm","Tyrrell Hatton",
    "Cameron Smith","Marc Leishman","Talor Gooch","Jason Kokrak",
    "Louis Oosthuizen","Dean Burmester","Charl Schwartzel","Brooks Koepka","Harold Varner III",
]

LIV_SCHEDULE_2026 = [
    {"name":"LIV Golf Riyadh","start_date":"2026-02-07","location":"Riyadh, Saudi Arabia"},
    {"name":"LIV Golf Adelaide","start_date":"2026-02-15","location":"Adelaide, Australia"},
    {"name":"LIV Golf Hong Kong","start_date":"2026-03-08","location":"Hong Kong"},
    {"name":"LIV Golf Singapore","start_date":"2026-03-15","location":"Singapore"},
    {"name":"LIV Golf South Africa","start_date":"2026-03-22","location":"South Africa"},
    {"name":"LIV Golf Mexico City","start_date":"2026-04-19","location":"Mexico City, Mexico"},
    {"name":"LIV Golf Virginia","start_date":"2026-05-10","location":"Washington DC, USA"},
    {"name":"LIV Golf Korea","start_date":"2026-05-31","location":"Busan, South Korea"},
    {"name":"LIV Golf Andalucia","start_date":"2026-06-07","location":"Valderrama, Spain"},
    {"name":"LIV Golf Louisiana","start_date":"2026-06-28","location":"Louisiana, USA"},
    {"name":"LIV Golf UK","start_date":"2026-07-26","location":"Sunningdale, England"},
    {"name":"LIV Golf New York","start_date":"2026-08-09","location":"New York, USA"},
    {"name":"LIV Golf Indianapolis","start_date":"2026-08-23","location":"Indianapolis, USA"},
]

def badge(tour):
    cls = {"LIV Golf":"liv","PGA Tour":"pga","Korn Ferry Tour":"kft","PGA Tour Americas":"pta"}.get(tour,"other")
    return f'<span class="badge badge-{cls}">{tour}</span>'

def ts_to_date(ms):
    return datetime.fromtimestamp(ms/1000).strftime('%Y-%m-%d')

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn')

def fuzzy_match(name, player_list, threshold=80):
    parts = name.strip().split()
    variants = [name]
    if len(parts) >= 2:
        first = " ".join(parts[:-1])
        last = parts[-1]
        variants.append(f"{last}, {first}")
        variants.append(f"{last} {first}")
        if len(parts) >= 3:
            variants.append(f"{" ".join(parts[1:])}, {parts[0]}")
    best, best_name = 0, ""
    for p in player_list:
        for v in variants:
            score = fuzz.token_sort_ratio(strip_accents(v.lower()), strip_accents(p.lower()))
            if score > best:
                best, best_name = score, p
    return best >= threshold, best, best_name

@st.cache_data(ttl=1800)
def fetch_pga_schedule(tour_code):
    query = f"""{{ schedule(tourCode: "{tour_code}", year: "2026") {{
        upcoming {{ tournaments {{ id tournamentName startDate city state country purse }} }}
        completed {{ tournaments {{ id tournamentName startDate city state country purse }} }}
    }} }}"""
    try:
        r = requests.post("https://orchestrator.pgatour.com/graphql", headers=PGA_HEADERS, json={"query":query}, timeout=15)
        data = r.json()["data"]["schedule"]
        upcoming, completed = [], []
        for m in data.get("upcoming",[]): upcoming.extend(m["tournaments"])
        for m in data.get("completed",[]): completed.extend(m["tournaments"])
        return upcoming, completed
    except:
        return [], []

@st.cache_data(ttl=1800)
def fetch_pga_field(tournament_id):
    player_type = "FieldPlayer" if tournament_id.startswith("R") else "PlayerField"
    query = f"""{{ field(id: "{tournament_id}") {{ players {{ ... on {player_type} {{ displayName country }} }} }} }}"""
    try:
        r = requests.post("https://orchestrator.pgatour.com/graphql", headers=PGA_HEADERS, json={"query":query}, timeout=15)
        raw = r.json()["data"]["field"]["players"]
        return [p.get("displayName","") for p in raw if p.get("displayName")]
    except:
        return []

@st.cache_data(ttl=86400)
def verify_nationality_from_api(name):
    for tc in ["R","H","Y"]:
        query = f"""{{ playerDirectory(tourCode: {tc}, active: false) {{ players {{ displayName country }} }} }}"""
        try:
            r = requests.post("https://orchestrator.pgatour.com/graphql", headers=PGA_HEADERS, json={"query":query}, timeout=10)
            for p in r.json()["data"]["playerDirectory"]["players"]:
                if fuzz.token_sort_ratio(strip_accents(name.lower()), strip_accents(p["displayName"].lower())) >= 85:
                    return True, p.get("country","Unknown"), p["displayName"]
        except:
            continue
    return False, "Not in API", name

def fetch_event_and_search(t, targets, tour_name):
    field = fetch_pga_field(t["id"])
    results = []
    if not field: return results
    for name in targets:
        matched, score, matched_as = fuzzy_match(name, field)
        if matched:
            results.append({"athlete":name,"name":t["tournamentName"],
                "date":ts_to_date(t["startDate"]),
                "location":f"{t.get('city','')} {t.get('country','')}".strip(),
                "tour":tour_name,"purse":t.get("purse","")})
    return results

def build_athlete_data(mexican_golfers):
    athletes = {name:{"events":[],"tour":"Unknown"} for name in mexican_golfers}
    for name in mexican_golfers:
        matched,score,_ = fuzzy_match(name, LIV_ROSTER_2026, threshold=85)
        if matched:
            athletes[name]["tour"] = "LIV Golf"
            for e in LIV_SCHEDULE_2026:
                athletes[name]["events"].append({"name":e["name"],"date":e["start_date"],"location":e["location"],"tour":"LIV Golf","purse":"N/A"})
    for tour_code, tour_name in [("R","PGA Tour"),("H","Korn Ferry Tour"),("Y","PGA Tour Americas")]:
        upcoming, completed = fetch_pga_schedule(tour_code)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = [ex.submit(fetch_event_and_search, t, mexican_golfers, tour_name) for t in upcoming+completed]
            for f in concurrent.futures.as_completed(futures):
                for entry in f.result():
                    n = entry["athlete"]
                    if athletes[n]["tour"] == "Unknown": athletes[n]["tour"] = tour_name
                    athletes[n]["events"].append(entry)
    return athletes

with st.sidebar:
    st.markdown("### 🇲🇽 MX Athlete Tracker")
    st.markdown("---")
    st.markdown("**🏌️ Athlete List**")
    st.caption("One name per line. Mexican nationals only.")
    athlete_input = st.text_area("Athletes:", value="\n".join(DEFAULT_MEXICAN_GOLFERS), height=250, label_visibility="collapsed")
    MEXICAN_GOLFERS = [a.strip() for a in athlete_input.strip().split("\n") if a.strip()]
    st.markdown("---")
    search_query = st.text_input("🔍 Find athlete", placeholder="e.g. Ancer")
    st.markdown("---")
    st.markdown("**🏆 Filter by Tour**")
    show_liv = st.checkbox("LIV Golf", value=True)
    show_pga = st.checkbox("PGA Tour", value=True)
    show_kft = st.checkbox("Korn Ferry", value=True)
    show_pta = st.checkbox("PGA Tour Americas", value=True)
    show_lpga = st.checkbox("LPGA Tour", value=True)
    st.markdown("---")
    weeks_ahead = st.slider("📅 Weeks ahead", 1, 16, 8)
    st.markdown("---")
    verify_on = st.checkbox("✅ Nationality verification", value=False)
    st.caption("Confirms Mexican nationality via API. Slower.")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption("PGA Tour · Korn Ferry · PGA Tour Americas: live\nLIV Golf: 2026 hardcoded · Refreshes every 30min")

st.markdown("""<div class="hero"><h1>MEXICAN ATHLETE TRACKER</h1>
<p>Professional golf — worldwide competitions — live data</p>
<div class="updated">Last updated: """ + datetime.now().strftime('%B %d, %Y at %H:%M') + """</div></div>""", unsafe_allow_html=True)

with st.spinner("Fetching live tournament data across all tours..."):
    athlete_data = build_athlete_data(MEXICAN_GOLFERS)

today = datetime.now().strftime("%Y-%m-%d")
cutoff = (datetime.now()+timedelta(weeks=weeks_ahead)).strftime("%Y-%m-%d")
filtered_athletes = [a for a in MEXICAN_GOLFERS if search_query.lower() in strip_accents(a.lower())] if search_query else MEXICAN_GOLFERS
upcoming_events = sum(len([e for e in v["events"] if today<=e["date"]<=cutoff]) for v in athlete_data.values())
active_athletes = sum(1 for v in athlete_data.values() if v["events"])
tours_covered = len(set(v["tour"] for v in athlete_data.values() if v["tour"]!="Unknown"))

col1,col2,col3,col4 = st.columns(4)
for col,val,label in [(col1,len(MEXICAN_GOLFERS),"Athletes Tracked"),(col2,active_athletes,"With Events Found"),(col3,upcoming_events,f"Events Next {weeks_ahead}wks"),(col4,tours_covered,"Tours Covered")]:
    with col:
        st.markdown(f'<div class="metric-box"><div class="metric-val">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tab1,tab2,tab3 = st.tabs(["👤 By Athlete","📅 Upcoming Events","🗺️ All Schedules"])

with tab1:
    if verify_on:
        with st.expander("🌍 Nationality Verification"):
            for name in MEXICAN_GOLFERS:
                found,country,api_name = verify_nationality_from_api(name)
                if found and country=="Mexico": st.markdown(f"✅ **{name}** — confirmed Mexico")
                elif found: st.markdown(f"⚠️ **{name}** — API shows **{country}** (verify!)")
                else: st.markdown(f"❓ **{name}** — not in PGA/KFT/PTA API (may be LIV or other)")
    if not filtered_athletes:
        st.markdown('<div class="no-results">No athletes match your search.</div>', unsafe_allow_html=True)
    else:
        for name in filtered_athletes:
            data = athlete_data.get(name,{"events":[],"tour":"Unknown"})
            all_events = sorted(data["events"], key=lambda x:x["date"])
            upcoming = [e for e in all_events if today<=e["date"]<=cutoff]
            past = [e for e in all_events if e["date"]<today]
            tour = data["tour"]
            if tour=="LIV Golf" and not show_liv: continue
            if tour=="PGA Tour" and not show_pga: continue
            if tour=="Korn Ferry Tour" and not show_kft: continue
            if tour=="PGA Tour Americas" and not show_pta: continue
            with st.expander(f"{'🟢' if upcoming else '⚪'} {name}  —  {tour}", expanded=bool(upcoming)):
                ca,cb = st.columns([3,1])
                with ca:
                    st.markdown(f"**{name}**")
                    st.markdown(f"Tour: {badge(tour)}", unsafe_allow_html=True)
                with cb:
                    st.markdown(f'<div style="text-align:right"><div style="font-family:Bebas Neue,sans-serif;font-size:2rem;color:#006847">{len(upcoming)}</div><div style="font-size:0.7rem;color:#666;text-transform:uppercase">Upcoming</div></div>', unsafe_allow_html=True)
                if upcoming:
                    st.markdown("**Upcoming Events:**")
                    for e in upcoming:
                        st.markdown(f'<div class="event-card"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} <span class="upcoming-pill">upcoming</span></p><p class="event-meta">📍 {e["location"]} &nbsp;|&nbsp; {badge(e["tour"])}</p></div><div class="event-date">{e["date"]}</div></div></div>', unsafe_allow_html=True)
                else:
                    st.markdown("*No upcoming events in selected time range.*")
                if past:
                    with st.expander(f"Past events ({len(past)})"):
                        for e in past[-5:]:
                            st.markdown(f'<div class="event-card" style="opacity:0.5"><div style="display:flex;justify-content:space-between"><div><p class="event-name">{e["name"]}</p><p class="event-meta">📍 {e["location"]}</p></div><div class="event-date">{e["date"]}</div></div></div>', unsafe_allow_html=True)

with tab2:
    all_upcoming = []
    for name in MEXICAN_GOLFERS:
        for e in athlete_data.get(name,{"events":[]})["events"]:
            if today<=e["date"]<=cutoff: all_upcoming.append({**e,"athlete":name})
    all_upcoming.sort(key=lambda x:x["date"])
    if not all_upcoming:
        st.markdown('<div class="no-results">No upcoming events in range.<br><small>Fields post Tuesday of event week.</small></div>', unsafe_allow_html=True)
    else:
        for date,group in groupby(all_upcoming,key=lambda x:x["date"]):
            events=list(group)
            st.markdown(f"#### 📆 {datetime.strptime(date,'%Y-%m-%d').strftime('%B %d, %Y')}")
            for e in events:
                purse_str=f"&nbsp;|&nbsp; 💰 {e['purse']}" if e.get("purse") and e["purse"] not in ["N/A","$0",""] else ""
                st.markdown(f'<div class="event-card"><p class="event-name">{e["name"]}</p><p class="event-meta">🏌️ <strong>{e["athlete"]}</strong> &nbsp;|&nbsp; 📍 {e["location"]} &nbsp;|&nbsp; {badge(e["tour"])}{purse_str}</p></div>', unsafe_allow_html=True)

with tab3:
    st.markdown("#### Full 2026 Schedules")
    sub1,sub2,sub3,sub4,sub5 = st.tabs(["PGA Tour","Korn Ferry","PGA Tour Americas","LIV Golf","LPGA Tour"])
    for sub,code in [(sub1,"R"),(sub2,"H"),(sub3,"Y")]:
        with sub:
            up,comp = fetch_pga_schedule(code)
            for t in sorted(up+comp,key=lambda x:x["startDate"]):
                date=ts_to_date(t["startDate"])
                is_up=date>=today
                pill='<span class="upcoming-pill">upcoming</span>' if is_up else '<span class="past-pill">completed</span>'
                st.markdown(f'<div class="event-card" style="opacity:{"1" if is_up else "0.4"}"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{t["tournamentName"]} &nbsp;{pill}</p><p class="event-meta">📍 {t.get("city","")}, {t.get("country","")} &nbsp;|&nbsp; 💰 {t.get("purse","")}</p></div><div class="event-date">{date}</div></div></div>', unsafe_allow_html=True)
    with sub4:
        for e in LIV_SCHEDULE_2026:
            is_up=e["start_date"]>=today
            pill='<span class="upcoming-pill">upcoming</span>' if is_up else '<span class="past-pill">completed</span>'
            st.markdown(f'<div class="event-card" style="opacity:{"1" if is_up else "0.4"}"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} &nbsp;{pill}</p><p class="event-meta">📍 {e["location"]}</p></div><div class="event-date">{e["start_date"]}</div></div></div>', unsafe_allow_html=True)

    with sub5:
        for e in LPGA_SCHEDULE_2026:
            is_up = e["start_date"] >= today
            pill = '<span class="upcoming-pill">upcoming</span>' if is_up else '<span class="past-pill">completed</span>'
            st.markdown(f'<div class="event-card" style="opacity:{"1" if is_up else "0.4"}"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} &nbsp;{pill}</p><p class="event-meta">📍 {e["location"]} &nbsp;|&nbsp; 💰 {e["purse"]}</p></div><div class="event-date">{e["start_date"]}</div></div></div>', unsafe_allow_html=True)
