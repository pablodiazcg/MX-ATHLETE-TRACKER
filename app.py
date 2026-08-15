"""
Mexican Athlete Tracker — Streamlit App
Run with: streamlit run app.py
"""

import streamlit as st
import requests
import json
import unicodedata
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MX Athlete Tracker",
    page_icon="🇲🇽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0a;
    color: #f0f0f0;
  }

  .main { background-color: #0a0a0a; }
  .block-container { padding-top: 2rem; max-width: 1200px; }

  .hero {
    background: linear-gradient(135deg, #006847 0%, #0a0a0a 50%, #CE1126 100%);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: "🇲🇽";
    font-size: 180px;
    position: absolute;
    right: -20px;
    top: -20px;
    opacity: 0.08;
  }
  .hero h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    letter-spacing: 3px;
    margin: 0;
    color: #ffffff;
    line-height: 1;
  }
  .hero p { color: #aaaaaa; font-size: 1rem; margin-top: 0.5rem; font-weight: 300; }
  .hero .updated { font-size: 0.75rem; color: #666; margin-top: 1rem; }

  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  .badge-liv   { background: #1a1a2e; color: #4fc3f7; border: 1px solid #4fc3f7; }
  .badge-pga   { background: #1a2e1a; color: #66bb6a; border: 1px solid #66bb6a; }
  .badge-kft   { background: #2e2a1a; color: #ffa726; border: 1px solid #ffa726; }
  .badge-other { background: #1a1a1a; color: #aaaaaa; border: 1px solid #444; }

  .verified-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    background: #006847;
    color: white;
    margin-left: 6px;
  }
  .unverified-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.65rem;
    letter-spacing: 1px;
    background: #2a1a00;
    color: #ffa726;
    border: 1px solid #ffa726;
    margin-left: 6px;
  }

  .event-card {
    background: #141414;
    border: 1px solid #222;
    border-left: 4px solid #006847;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
  }
  .event-card:hover { border-left-color: #CE1126; }
  .event-card .event-name { font-size: 1rem; font-weight: 600; color: #f0f0f0; margin: 0 0 0.25rem 0; }
  .event-card .event-meta { font-size: 0.8rem; color: #888; margin: 0; }
  .event-card .event-date { font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem; color: #006847; letter-spacing: 1px; }

  .metric-box { background: #141414; border: 1px solid #222; border-radius: 10px; padding: 1rem; text-align: center; }
  .metric-box .metric-val { font-family: 'Bebas Neue', sans-serif; font-size: 2.2rem; color: #006847; line-height: 1; }
  .metric-box .metric-label { font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.25rem; }

  section[data-testid="stSidebar"] { background-color: #0f0f0f; border-right: 1px solid #1e1e1e; }

  .no-results { text-align: center; padding: 3rem; color: #444; font-size: 1rem; }

  hr { border-color: #1e1e1e; margin: 1.5rem 0; }

  #MainMenu, footer, header { visibility: hidden; }

  .upcoming-pill {
    background: #006847; color: white; border-radius: 20px;
    padding: 2px 8px; font-size: 0.65rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px;
  }
  .past-pill {
    background: #222; color: #666; border-radius: 20px;
    padding: 2px 8px; font-size: 0.65rem; letter-spacing: 1px;
  }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
PGA_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "x-api-key": "da2-gsrx5bibzbb4njvhl7t37wqyl4",
}

# ── Manually curated Mexican golfer list ─────────────────────────────────────
# Edit this list to add/remove athletes. These are verified Mexican nationals.
DEFAULT_MEXICAN_GOLFERS = [
    "Abraham Ancer",
    "Carlos Ortiz",
    "Álvaro Ortiz",
    "Rodolfo Cazaubon",
    "José de Jesús Rodríguez",
    "Roberto Díaz",
    "Santiago de La Fuente",
]

LIV_ROSTER_2026 = [
    "Joaquin Niemann", "Abraham Ancer", "Sebastian Munoz", "Carlos Ortiz",
    "Dustin Johnson", "Thomas Detry", "Thomas Pieters", "Anthony Kim",
    "Bryson DeChambeau", "Charles Howell III", "Anirban Lahiri",
    "Sergio Garcia", "David Puig", "Phil Mickelson", "Brendan Steele",
    "Jon Rahm", "Tyrrell Hatton", "Cameron Smith", "Marc Leishman",
    "Talor Gooch", "Jason Kokrak", "Louis Oosthuizen", "Dean Burmester",
    "Charl Schwartzel", "Brooks Koepka", "Harold Varner III",
]

LIV_SCHEDULE_2026 = [
    {"name": "LIV Golf Riyadh",       "start_date": "2026-02-07", "location": "Riyadh, Saudi Arabia"},
    {"name": "LIV Golf Adelaide",     "start_date": "2026-02-15", "location": "Adelaide, Australia"},
    {"name": "LIV Golf Hong Kong",    "start_date": "2026-03-08", "location": "Hong Kong"},
    {"name": "LIV Golf Singapore",    "start_date": "2026-03-15", "location": "Singapore"},
    {"name": "LIV Golf South Africa", "start_date": "2026-03-22", "location": "South Africa"},
    {"name": "LIV Golf Mexico City",  "start_date": "2026-04-19", "location": "Mexico City, Mexico"},
    {"name": "LIV Golf Virginia",     "start_date": "2026-05-10", "location": "Washington DC, USA"},
    {"name": "LIV Golf Korea",        "start_date": "2026-05-31", "location": "Busan, South Korea"},
    {"name": "LIV Golf Andalucia",    "start_date": "2026-06-07", "location": "Valderrama, Spain"},
    {"name": "LIV Golf Louisiana",    "start_date": "2026-06-28", "location": "Louisiana, USA"},
    {"name": "LIV Golf UK",           "start_date": "2026-07-26", "location": "Sunningdale, England"},
    {"name": "LIV Golf New York",     "start_date": "2026-08-09", "location": "New York, USA"},
    {"name": "LIV Golf Indianapolis", "start_date": "2026-08-23", "location": "Indianapolis, USA"},
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def badge(tour):
    cls = {"LIV Golf": "liv", "PGA Tour": "pga", "Korn Ferry Tour": "kft"}.get(tour, "other")
    return f'<span class="badge badge-{cls}">{tour}</span>'

def ts_to_date(ms):
    return datetime.fromtimestamp(ms / 1000).strftime('%Y-%m-%d')

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def fuzzy_match(name, player_list, threshold=70):
    best, best_name = 0, ""
    for p in player_list:
        score = fuzz.token_sort_ratio(
            strip_accents(name.lower()),
            strip_accents(p.lower())
        )
        if score > best:
            best, best_name = score, p
    return best >= threshold, best, best_name

# ── Nationality verification via PGA Tour API ─────────────────────────────────
@st.cache_data(ttl=86400)  # cache 24hrs — nationality doesn't change
def verify_nationality_from_api(name):
    """
    Try to find the player in PGA Tour API and confirm country = Mexico.
    Returns: (verified: bool, country: str, api_name: str)
    """
    for tour_code in ["R", "S"]:
        query = f"""
        {{
          playerDirectory(tourCode: {tour_code}, active: false) {{
            players {{ id firstName lastName displayName country }}
          }}
        }}
        """
        try:
            r = requests.post("https://orchestrator.pgatour.com/graphql",
                              headers=PGA_HEADERS, json={"query": query}, timeout=10)
            players = r.json()["data"]["playerDirectory"]["players"]
            for p in players:
                score = fuzz.token_sort_ratio(
                    strip_accents(name.lower()),
                    strip_accents(p["displayName"].lower())
                )
                if score >= 85:
                    return True, p.get("country", "Unknown"), p["displayName"]
        except:
            continue
    return False, "Not in API", name

# ── Data fetching (cached) ────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_pga_schedule(tour_code):
    query = f"""
    {{
      schedule(tourCode: "{tour_code}", year: "2026") {{
        upcoming {{ tournaments {{
          id tournamentName startDate city state country purse
        }} }}
        completed {{ tournaments {{
          id tournamentName startDate city state country purse
        }} }}
      }}
    }}
    """
    try:
        r = requests.post("https://orchestrator.pgatour.com/graphql",
                          headers=PGA_HEADERS, json={"query": query}, timeout=15)
        data = r.json()["data"]["schedule"]
        upcoming, completed = [], []
        for m in data.get("upcoming", []):
            upcoming.extend(m["tournaments"])
        for m in data.get("completed", []):
            completed.extend(m["tournaments"])
        return upcoming, completed
    except:
        return [], []

@st.cache_data(ttl=1800)
def fetch_pga_field(tournament_id):
    query = f"""
    {{
      field(id: "{tournament_id}") {{
        players {{
          ... on FieldPlayer {{ displayName country }}
        }}
      }}
    }}
    """
    try:
        r = requests.post("https://orchestrator.pgatour.com/graphql",
                          headers=PGA_HEADERS, json={"query": query}, timeout=15)
        raw = r.json()["data"]["field"]["players"]
        return [p.get("displayName", "") for p in raw if p.get("displayName")]
    except:
        return []

def build_athlete_data(mexican_golfers):
    athletes = {}
    for name in mexican_golfers:
        athletes[name] = {"events": [], "tour": "Unknown", "verified": False, "api_country": ""}

    # LIV Golf — hardcoded roster
    for name in mexican_golfers:
        matched, score, _ = fuzzy_match(name, LIV_ROSTER_2026, threshold=85)
        if matched:
            athletes[name]["tour"] = "LIV Golf"
            athletes[name]["verified"] = True
            athletes[name]["api_country"] = "Mexico (LIV)"
            for e in LIV_SCHEDULE_2026:
                athletes[name]["events"].append({
                    "name": e["name"],
                    "date": e["start_date"],
                    "location": e["location"],
                    "tour": "LIV Golf",
                    "purse": "N/A"
                })

    # PGA Tour + Korn Ferry — live API
    for tour_code, tour_name in [("R", "PGA Tour"), ("S", "Korn Ferry Tour")]:
        upcoming, completed = fetch_pga_schedule(tour_code)
        all_events = upcoming + completed
        for t in all_events:
            field = fetch_pga_field(t["id"])
            if not field:
                continue
            for name in mexican_golfers:
                matched, score, matched_name = fuzzy_match(name, field, threshold=70)
                if matched:
                    if athletes[name]["tour"] == "Unknown":
                        athletes[name]["tour"] = tour_name
                    athletes[name]["events"].append({
                        "name": t["tournamentName"],
                        "date": ts_to_date(t["startDate"]),
                        "location": f"{t['city']}, {t['country']}",
                        "tour": tour_name,
                        "purse": t.get("purse", "")
                    })

    return athletes

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🇲🇽 MX Athlete Tracker")
    st.markdown("---")

    st.markdown("**🏌️ Athlete List** *(manually curated — Mexican nationals only)*")
    st.caption("Add or remove athletes below. One name per line.")

    athlete_input = st.text_area(
        "Athletes:",
        value="\n".join(DEFAULT_MEXICAN_GOLFERS),
        height=220,
        label_visibility="collapsed"
    )
    MEXICAN_GOLFERS = [a.strip() for a in athlete_input.strip().split("\n") if a.strip()]

    st.markdown("---")
    st.markdown("**🔍 Search**")
    search_query = st.text_input("Find athlete", placeholder="e.g. Ancer")

    st.markdown("---")
    st.markdown("**🏆 Filter by Tour**")
    show_liv = st.checkbox("LIV Golf", value=True)
    show_pga = st.checkbox("PGA Tour", value=True)
    show_kft = st.checkbox("Korn Ferry", value=True)

    st.markdown("---")
    st.markdown("**📅 Time Range**")
    weeks_ahead = st.slider("Weeks ahead", 1, 16, 8)

    st.markdown("---")
    verify_on = st.checkbox("✅ Show nationality verification", value=False)
    st.caption("Checks PGA Tour API to confirm each athlete is Mexican. Slower to load.")

    refresh = st.button("🔄 Refresh Data", use_container_width=True)
    if refresh:
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("PGA Tour: live API · LIV Golf: 2026 hardcoded · Data refreshes every 30 min")

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>MEXICAN ATHLETE TRACKER</h1>
  <p>Professional golf — worldwide competitions — live data</p>
  <div class="updated">Last updated: """ + datetime.now().strftime('%B %d, %Y at %H:%M') + """</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("Fetching live tournament data..."):
    athlete_data = build_athlete_data(MEXICAN_GOLFERS)

today = datetime.now().strftime("%Y-%m-%d")
cutoff = (datetime.now() + timedelta(weeks=weeks_ahead)).strftime("%Y-%m-%d")

filtered_athletes = MEXICAN_GOLFERS
if search_query:
    filtered_athletes = [a for a in MEXICAN_GOLFERS
                         if search_query.lower() in strip_accents(a.lower())]

# Metrics
upcoming_events = sum(
    len([e for e in v["events"] if today <= e["date"] <= cutoff])
    for v in athlete_data.values()
)
active_athletes = sum(1 for v in athlete_data.values() if v["events"])
tours_covered = len(set(v["tour"] for v in athlete_data.values() if v["tour"] != "Unknown"))

col1, col2, col3, col4 = st.columns(4)
for col, val, label in [
    (col1, len(MEXICAN_GOLFERS), "Athletes Tracked"),
    (col2, active_athletes, "With Events Found"),
    (col3, upcoming_events, f"Events Next {weeks_ahead}wks"),
    (col4, tours_covered, "Tours Covered"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-val">{val}</div>
          <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["👤 By Athlete", "📅 Upcoming Events", "🗺️ All Schedules"])

# TAB 1 — By Athlete
with tab1:

    # Optional nationality verification panel
    if verify_on:
        with st.expander("🌍 Nationality Verification", expanded=False):
            st.caption("Checking each athlete against PGA Tour API to confirm Mexican nationality.")
            for name in MEXICAN_GOLFERS:
                found, country, api_name = verify_nationality_from_api(name)
                if found and country == "Mexico":
                    st.markdown(f"✅ **{name}** — confirmed Mexico ({api_name})")
                elif found:
                    st.markdown(f"⚠️ **{name}** — found in API but country = **{country}** (check this!)")
                else:
                    st.markdown(f"❓ **{name}** — not found in PGA/Korn Ferry API (may be on LIV or another tour)")

    if not filtered_athletes:
        st.markdown('<div class="no-results">No athletes match your search.</div>',
                    unsafe_allow_html=True)
    else:
        for name in filtered_athletes:
            data = athlete_data.get(name, {"events": [], "tour": "Unknown"})
            all_events = sorted(data["events"], key=lambda x: x["date"])
            upcoming = [e for e in all_events if today <= e["date"] <= cutoff]
            past = [e for e in all_events if e["date"] < today]

            tour = data["tour"]
            if tour == "LIV Golf" and not show_liv: continue
            if tour == "PGA Tour" and not show_pga: continue
            if tour == "Korn Ferry Tour" and not show_kft: continue

            status_icon = "🟢" if upcoming else "⚪"
            with st.expander(f"{status_icon} {name}  —  {tour}", expanded=bool(upcoming)):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{name}**")
                    st.markdown(f"Tour: {badge(tour)}", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"""
                    <div style="text-align:right">
                      <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;color:#006847">{len(upcoming)}</div>
                      <div style="font-size:0.7rem;color:#666;text-transform:uppercase">Upcoming</div>
                    </div>""", unsafe_allow_html=True)

                if upcoming:
                    st.markdown("**Upcoming Events:**")
                    for e in upcoming:
                        st.markdown(f"""
                        <div class="event-card">
                          <div style="display:flex;justify-content:space-between;align-items:center">
                            <div>
                              <p class="event-name">{e['name']} <span class="upcoming-pill">upcoming</span></p>
                              <p class="event-meta">📍 {e['location']} &nbsp;|&nbsp; {badge(e['tour'])}</p>
                            </div>
                            <div class="event-date">{e['date']}</div>
                          </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("*No upcoming events in selected time range.*")

                if past:
                    with st.expander(f"Past events ({len(past)})"):
                        for e in past[-5:]:
                            st.markdown(f"""
                            <div class="event-card" style="opacity:0.5">
                              <div style="display:flex;justify-content:space-between">
                                <div>
                                  <p class="event-name">{e['name']}</p>
                                  <p class="event-meta">📍 {e['location']}</p>
                                </div>
                                <div class="event-date">{e['date']}</div>
                              </div>
                            </div>""", unsafe_allow_html=True)

# TAB 2 — Upcoming Events
with tab2:
    all_upcoming = []
    for name in MEXICAN_GOLFERS:
        data = athlete_data.get(name, {"events": []})
        for e in data["events"]:
            if today <= e["date"] <= cutoff:
                all_upcoming.append({**e, "athlete": name})
    all_upcoming.sort(key=lambda x: x["date"])

    if not all_upcoming:
        st.markdown("""
        <div class="no-results">
          No upcoming events found in selected time range.<br>
          <small>PGA Tour fields are posted Tuesday of event week. Try extending weeks ahead.</small>
        </div>""", unsafe_allow_html=True)
    else:
        from itertools import groupby
        for date, group in groupby(all_upcoming, key=lambda x: x["date"]):
            events = list(group)
            st.markdown(f"#### 📆 {datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')}")
            for e in events:
                purse_str = f"&nbsp;|&nbsp; 💰 {e['purse']}" if e.get("purse") and e["purse"] not in ["N/A", "$0", ""] else ""
                st.markdown(f"""
                <div class="event-card">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                      <p class="event-name">{e['name']}</p>
                      <p class="event-meta">
                        🏌️ <strong>{e['athlete']}</strong> &nbsp;|&nbsp;
                        📍 {e['location']} &nbsp;|&nbsp;
                        {badge(e['tour'])}{purse_str}
                      </p>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

# TAB 3 — All Schedules
with tab3:
    st.markdown("#### Full 2026 Schedules")
    sub1, sub2, sub3 = st.tabs(["PGA Tour", "Korn Ferry Tour", "LIV Golf"])

    with sub1:
        upcoming_pga, completed_pga = fetch_pga_schedule("R")
        for t in sorted(upcoming_pga + completed_pga, key=lambda x: x["startDate"]):
            date = ts_to_date(t["startDate"])
            is_up = date >= today
            pill = '<span class="upcoming-pill">upcoming</span>' if is_up else '<span class="past-pill">completed</span>'
            st.markdown(f"""
            <div class="event-card" style="opacity:{'1' if is_up else '0.4'}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <p class="event-name">{t['tournamentName']} &nbsp;{pill}</p>
                  <p class="event-meta">📍 {t['city']}, {t['country']} &nbsp;|&nbsp; 💰 {t.get('purse','')}</p>
                </div>
                <div class="event-date">{date}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    with sub2:
        upcoming_kft, completed_kft = fetch_pga_schedule("S")
        for t in sorted(upcoming_kft + completed_kft, key=lambda x: x["startDate"]):
            date = ts_to_date(t["startDate"])
            is_up = date >= today
            pill = '<span class="upcoming-pill">upcoming</span>' if is_up else '<span class="past-pill">completed</span>'
            st.markdown(f"""
            <div class="event-card" style="opacity:{'1' if is_up else '0.4'}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <p class="event-name">{t['tournamentName']} &nbsp;{pill}</p>
                  <p class="event-meta">📍 {t['city']}, {t['country']}</p>
                </div>
                <div class="event-date">{date}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    with sub3:
        for e in LIV_SCHEDULE_2026:
            is_up = e["start_date"] >= today
            pill = '<span class="upcoming-pill">upcoming</span>' if is_up else '<span class="past-pill">completed</span>'
            st.markdown(f"""
            <div class="event-card" style="opacity:{'1' if is_up else '0.4'}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <p class="event-name">{e['name']} &nbsp;{pill}</p>
                  <p class="event-meta">📍 {e['location']}</p>
                </div>
                <div class="event-date">{e['start_date']}</div>
              </div>
            </div>""", unsafe_allow_html=True)
