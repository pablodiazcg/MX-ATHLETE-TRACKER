
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
  .badge-asian { background: #1a2e2e; color: #80cbc4; border: 1px solid #80cbc4; }
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

  .profile-section { background: #141414; border: 1px solid #222; border-radius: 12px; padding: 1.25rem; margin-top: 1rem; }
  .profile-stat { display: inline-block; margin-right: 1.5rem; margin-bottom: 0.5rem; }
  .profile-stat .stat-val { font-family: 'Bebas Neue', sans-serif; font-size: 1.4rem; color: #f0f0f0; }
  .profile-stat .stat-label { font-size: 0.65rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }
  .sponsor-chip { display: inline-block; background: #1a1a1a; border: 1px solid #333; border-radius: 20px; padding: 4px 12px; margin: 3px; font-size: 0.75rem; color: #ccc; }
  .sponsor-chip .cat { color: #666; font-size: 0.65rem; }
  .highlight-item { padding: 4px 0; border-bottom: 1px solid #1a1a1a; font-size: 0.85rem; color: #ccc; }
  .highlight-item:last-child { border-bottom: none; }

</style>
""", unsafe_allow_html=True)

PGA_HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "x-api-key": "da2-gsrx5bibzbb4njvhl7t37wqyl4"}

DEFAULT_MEXICAN_GOLFERS = [
    "Abraham Ancer","Carlos Ortiz","Álvaro Ortiz","Rodolfo Cazaubon",
    "José de Jesús Rodríguez","Roberto Díaz","Santiago de La Fuente",
    "Emilio Gonzalez","Raul Pereda","Jose Cristobal Islas","Omar Morales",
    "Luis Carrera","Sebastian Vazquez","Julio Arronte","Yael Chahin",
    "Gaby Lopez","Isabella Fierro","Lauren Olivares","Maria Fassi",
    "Marcelo Garza",
    "Jose Cristobal Islas",
    "José de Jesús Rodríguez",
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


# 2026 Asian Tour + International Series Schedule
ASIAN_TOUR_SCHEDULE_2026 = [
    {"name": "Philippine Golf Championship",  "start_date": "2026-02-08", "location": "Philippines",     "purse": "$500,000",   "series": "Asian Tour"},
    {"name": "New Zealand Open",              "start_date": "2026-03-01", "location": "New Zealand",      "purse": "$2,000,000", "series": "Asian Tour"},
    {"name": "International Series Japan",    "start_date": "2026-04-05", "location": "Japan",            "purse": "$2,000,000", "series": "International Series"},
    {"name": "Singapore Open",               "start_date": "2026-04-26", "location": "Singapore",        "purse": "$2,000,000", "series": "International Series"},
    {"name": "GS Caltex Maekyung Open",      "start_date": "2026-05-03", "location": "South Korea",      "purse": "$1,300,000", "series": "Asian Tour"},
    {"name": "Taiwan Glass Taifong Open",    "start_date": "2026-05-10", "location": "Taiwan",           "purse": "$500,000",   "series": "Asian Tour"},
    {"name": "Kolon Korea Open",             "start_date": "2026-05-24", "location": "South Korea",      "purse": "$1,400,000", "series": "Asian Tour"},
    {"name": "International Series Morocco", "start_date": "2026-06-14", "location": "Morocco",          "purse": "$2,000,000", "series": "International Series"},
    {"name": "Yeangder Taiwan Open",         "start_date": "2026-09-20", "location": "Taiwan",           "purse": "$1,200,000", "series": "Asian Tour"},
    {"name": "Mercuries Taiwan Masters",     "start_date": "2026-09-27", "location": "Taiwan",           "purse": "$1,200,000", "series": "Asian Tour"},
    {"name": "International Series India",   "start_date": "2026-10-11", "location": "India",            "purse": "$2,000,000", "series": "International Series"},
    {"name": "SJM Macao Open",              "start_date": "2026-10-18", "location": "Macau",            "purse": "$1,000,000", "series": "Asian Tour"},
    {"name": "Link Hong Kong Open",          "start_date": "2026-10-25", "location": "Hong Kong",        "purse": "$2,000,000", "series": "International Series"},
    {"name": "International Series China",   "start_date": "2026-11-08", "location": "China",            "purse": "$2,000,000", "series": "International Series"},
    {"name": "Philippine Open",             "start_date": "2026-11-15", "location": "Philippines",      "purse": "$2,000,000", "series": "International Series"},
    {"name": "PIF Saudi International",      "start_date": "2026-11-21", "location": "Saudi Arabia",     "purse": "$5,000,000", "series": "International Series"},
]

# Mexican players on Asian Tour / International Series
ASIAN_TOUR_MEXICAN_PLAYERS = [
    "Santiago de La Fuente",
    "Carlos Ortiz",  # plays International Series events alongside LIV
]


# Tour membership — determines which events show as "possible"
TOUR_MEMBERSHIP = {
    "Álvaro Ortiz":           "H",   # Korn Ferry
    "Omar Morales":           "Y",   # PGA Tour Americas
    "Raul Pereda":            "Y",   # PGA Tour Americas
    "Emilio Gonzalez":        "R",   # PGA Tour
    "Rodolfo Cazaubon":       "Y",   # PGA Tour Americas
    "Jose Cristobal Islas":   "Y",   # PGA Tour Americas
    "Luis Carrera":           "Y",   # PGA Tour Americas
    "Sebastian Vazquez":      "Y",   # PGA Tour Americas
    "Julio Arronte":          "Y",   # PGA Tour Americas
    "Marcelo Garza":          "Y",   # PGA Tour Americas
    "Jose Cristobal Islas":   "Y",   # PGA Tour Americas
}


# ── Athlete Database ──────────────────────────────────────────────────────────
# Personal info and sponsors — update manually as needed
ATHLETE_DB = {
    "Abraham Ancer": {
        "full_name": "Abraham Ancer Sagastegui",
        "born": "February 27, 1991",
        "birthplace": "McAllen, Texas (raised in Reynosa, Mexico)",
        "age": 35,
        "height": "5'7\"",
        "turned_pro": 2013,
        "college": "University of Oklahoma",
        "wins": 6,
        "current_ranking": 197,
        "best_ranking": 11,
        "highlights": [
            "2021 WGC-FedEx St. Jude Invitational (PGA Tour win)",
            "2018 Emirates Australian Open",
            "2024 LIV Golf Hong Kong",
            "2023 Pan American Games Gold Medal",
            "2019 Presidents Cup International Team",
        ],
        "sponsors": [
            {"name": "Miura Golf", "category": "Equipment"},
            {"name": "Black Quail", "category": "Apparel"},
            {"name": "Flecha Azul Tequila", "category": "Lifestyle (co-founder)"},
        ],
        "social": {"instagram": "abraham_ancer", "twitter": "Abraham_Ancer"},
        "bio": "Mexican-American golfer born in McAllen, Texas and raised in Reynosa, Mexico. Co-founded Flecha Azul premium tequila brand. Lost his father in 2014, dedicating his career to his memory.",
    },
    "Carlos Ortiz": {
        "full_name": "Carlos Ortiz Becerra",
        "born": "April 24, 1991",
        "birthplace": "Guadalajara, Jalisco, Mexico",
        "age": 35,
        "height": "6'1\"",
        "turned_pro": 2012,
        "college": "University of North Texas",
        "wins": 10,
        "current_ranking": 161,
        "best_ranking": 44,
        "highlights": [
            "2020 Houston Open (PGA Tour win)",
            "2025 International Series Macau",
            "T4 at 2025 US Open",
            "2014 Web.com Tour Player of the Year",
            "LIV Golf Torque GC team member",
        ],
        "sponsors": [
            {"name": "Callaway", "category": "Equipment"},
            {"name": "Adidas Golf", "category": "Apparel"},
        ],
        "social": {"instagram": "carlosortizgolf", "twitter": "CarlosOrtizGolf"},
        "bio": "Professional golfer from Guadalajara with 10 professional wins. Won Mexico's first PGA Tour title in 16 years at the 2020 Houston Open. Finished T4 at the 2025 US Open. Now competing on LIV Golf.",
    },
    "Álvaro Ortiz": {
        "full_name": "Álvaro Ortiz Ruiz",
        "born": "October 3, 1994",
        "birthplace": "Guadalajara, Jalisco, Mexico",
        "age": 31,
        "height": "6'0\"",
        "turned_pro": 2017,
        "college": "University of Arkansas",
        "wins": 2,
        "current_ranking": 180,
        "best_ranking": 180,
        "highlights": [
            "2026 UNC Health Championship (Korn Ferry)",
            "Brother of Carlos Ortiz",
            "Multiple Korn Ferry top-10 finishes in 2026",
        ],
        "sponsors": [
            {"name": "Titleist", "category": "Equipment"},
        ],
        "social": {"instagram": "alvaroortizgolf"},
        "bio": "Younger brother of Carlos Ortiz, also a professional golfer. Playing on the Korn Ferry Tour with an impressive 2026 season including his first professional win.",
    },
    "Gaby Lopez": {
        "full_name": "Maria Gabriela López Butron",
        "born": "November 9, 1993",
        "birthplace": "Mexico City, Mexico",
        "age": 32,
        "height": "5'6\"",
        "turned_pro": 2015,
        "college": "University of Arkansas",
        "wins": 3,
        "current_ranking": 36,
        "best_ranking": 36,
        "highlights": [
            "2022 Dana Open (LPGA win)",
            "2020 Diamond Resorts Tournament of Champions",
            "2018 Blue Bay LPGA",
            "T2 at 2026 US Women's Open",
            "Mexico flag bearer at Tokyo 2020 Olympics",
            "Three-time Olympian (Rio, Tokyo, Paris)",
        ],
        "sponsors": [
            {"name": "Titleist", "category": "Equipment"},
            {"name": "Telcel", "category": "Telecom"},
            {"name": "AeroMexico", "category": "Aviation"},
            {"name": "Punta Mita", "category": "Resort"},
            {"name": "Ponyflo", "category": "Apparel (founder)"},
        ],
        "social": {"instagram": "gabylopezgolf", "twitter": "GabyLopezGolf"},
        "bio": "Mexico City native and three-time LPGA winner. Carried Mexico's flag at the Tokyo Olympics. Founder of Ponyflo, a women's cap brand. Considered the successor to Lorena Ochoa's legacy in Mexican golf.",
    },
    "Maria Fassi": {
        "full_name": "Maria Fassi",
        "born": "November 22, 1997",
        "birthplace": "Mexico City, Mexico",
        "age": 28,
        "height": "5'9\"",
        "turned_pro": 2019,
        "college": "University of Arkansas",
        "wins": 0,
        "current_ranking": 77,
        "best_ranking": 77,
        "highlights": [
            "2019 Augusta National Women's Amateur champion",
            "2019 LPGA Tour Rookie of the Year",
            "2020 Tokyo Olympics representative",
            "Known for exceptional power off the tee",
        ],
        "sponsors": [
            {"name": "Titleist", "category": "Equipment"},
            {"name": "FootJoy", "category": "Footwear"},
        ],
        "social": {"instagram": "mariafassi_golf"},
        "bio": "Power hitter from Mexico City who won the inaugural Augusta National Women's Amateur in 2019. Won LPGA Rookie of the Year that same season.",
    },
    "Isabella Fierro": {
        "full_name": "Isabella Fierro",
        "born": "November 1, 2001",
        "birthplace": "Monterrey, Mexico",
        "age": 24,
        "height": "5'7\"",
        "turned_pro": 2023,
        "college": "University of Arizona",
        "wins": 0,
        "current_ranking": 120,
        "best_ranking": 120,
        "highlights": [
            "2022 NCAA Individual Championship",
            "LPGA Tour member since 2024",
        ],
        "sponsors": [
            {"name": "Titleist", "category": "Equipment"},
        ],
        "social": {"instagram": "isabellafierrogolf"},
        "bio": "Young Mexican professional from Monterrey, NCAA champion who transitioned to the LPGA Tour. One of Mexico's brightest young talents in women's golf.",
    },
    "Santiago de La Fuente": {
        "full_name": "Santiago de La Fuente",
        "born": "June 14, 2000",
        "birthplace": "Ocotlán, Jalisco, Mexico",
        "age": 26,
        "height": "5'11\"",
        "turned_pro": 2022,
        "college": "University of Houston",
        "wins": 1,
        "current_ranking": 200,
        "best_ranking": 200,
        "highlights": [
            "2024 PGA Tour Americas win",
            "Asian Tour / International Series regular",
            "NCAA standout at University of Florida",
        ],
        "sponsors": [
            {"name": "Titleist", "category": "Equipment"},
        ],
        "social": {"instagram": "santiagodlf_golf"},
        "bio": "Young Mexican professional from Ocotlán, Jalisco playing the Asian Tour and International Series. Attended University of Houston. One of Mexico's top emerging talents in men's professional golf.",
    },
    "Rodolfo Cazaubon": {
        "full_name": "Rodolfo Cazaubon",
        "born": "August 15, 1996",
        "birthplace": "Mexico City, Mexico",
        "age": 29,
        "height": "5'10\"",
        "turned_pro": 2019,
        "college": "University of Houston",
        "wins": 0,
        "best_ranking": 350,
        "highlights": [
            "PGA Tour Americas competitor",
            "Multiple professional wins in Mexico",
        ],
        "sponsors": [],
        "social": {"instagram": "rcazaubon"},
        "bio": "Mexican professional competing on PGA Tour Americas and developmental tours.",
    },
    "Omar Morales": {
        "full_name": "Omar Morales",
        "born": "January 10, 1995",
        "birthplace": "Puebla, Mexico",
        "age": 31,
        "height": "5'11\"",
        "turned_pro": 2017,
        "college": "UCLA",
        "wins": 0,
        "best_ranking": 400,
        "highlights": [
            "Active PGA Tour Americas competitor 2026",
            "Multiple top-10 finishes in 2026",
        ],
        "sponsors": [],
        "social": {},
        "bio": "Mexican professional from Puebla who attended UCLA. Competing regularly on PGA Tour Americas with strong results in 2026.",
    },
        "Marcelo Garza": {
        "full_name": "Marcelo Garza",
        "born": "2003",
        "birthplace": "Mexico",
        "age": 22,
        "height": "—",
        "turned_pro": 2024,
        "college": "N/A",
        "wins": 0,
        "current_ranking": 112,
        "best_ranking": 112,
        "highlights": [
            "Turned professional August 2024",
            "One of Mexico\'s youngest active professionals",
            "Active PGA Tour Americas competitor 2026",
        ],
        "sponsors": [],
        "social": {},
        "bio": "Young Mexican professional and one of the newest additions to PGA Tour Americas. Turned professional in August 2024 at age 22.",
    },
    "Jose Cristobal Islas": {
        "full_name": "José Cristóbal Islas",
        "born": "2002",
        "birthplace": "Pachuca, Hidalgo, Mexico",
        "age": 23,
        "height": "—",
        "turned_pro": 2024,
        "college": "University of Oregon",
        "wins": 0,
        "current_ranking": 400,
        "best_ranking": 400,
        "highlights": [
            "From Pachuca, Hidalgo, Mexico",
            "University of Oregon standout",
            "Active PGA Tour Americas competitor",
        ],
        "sponsors": [],
        "social": {},
        "bio": "Young Mexican professional from Pachuca, Hidalgo. Attended University of Oregon before turning professional. Competing on PGA Tour Americas.",
    },
    "José de Jesús Rodríguez": {
        "full_name": "José de Jesús Rodríguez Martínez",
        "born": "January 22, 1981",
        "birthplace": "Irapuato, Guanajuato, Mexico",
        "age": 45,
        "height": "5\'10\"",
        "turned_pro": 2007,
        "college": "N/A",
        "wins": 38,
        "current_ranking": 500,
        "best_ranking": 250,
        "highlights": [
            "38 professional wins across multiple tours",
            "2017 PGA Tour Latinoamérica Order of Merit winner",
            "2019-20 & 2023-24 Gira Profesional Mexicana Order of Merit winner",
            "2011 Canadian Tour Order of Merit winner",
            "Central American Games Silver Medal 2014 & 2023",
            "Nicknamed \'Camarón\' (Shrimp)",
            "Grew up in poverty in Irapuato — inspirational story",
        ],
        "sponsors": [],
        "social": {},
        "bio": "One of Mexico\'s most decorated professional golfers with 38 wins. Grew up in poverty in Irapuato, sleeping on a dirt floor with six siblings. Nicknamed \'Camarón\' (Shrimp). Multiple tour Order of Merit winner and a true Mexican golf legend.",
    },

    "Lauren Olivares": {
        "full_name": "Lauren Olivares",
        "born": "2000",
        "birthplace": "Mexico",
        "age": 25,
        "height": "5'6\"",
        "turned_pro": 2022,
        "college": "N/A",
        "wins": 0,
        "best_ranking": 200,
        "highlights": [
            "Epson Tour competitor",
            "Earned 2027 LPGA Tour card",
        ],
        "sponsors": [],
        "social": {},
        "bio": "Young Mexican professional who earned her 2027 LPGA Tour card after competing on the Epson Tour.",
    },
}


# Player IDs for results lookup
PLAYER_IDS = {
    "Omar Morales":             "64690",
    "Emilio Gonzalez":          "59567",
    "Rodolfo Cazaubon":         "45702",
    "Sebastian Vazquez":        "35469",
    "Carlos Ortiz":             "33667",
    "Abraham Ancer":            "45526",
    "Marcelo Garza":            "65558",
    "Jose Cristobal Islas":     "66282",
    "José de Jesús Rodríguez":  "32058",
}

# Tour code for results lookup per player
PLAYER_TOUR_CODE = {
    "Omar Morales":             "Y",
    "Emilio Gonzalez":          "R",
    "Rodolfo Cazaubon":         "H",
    "Sebastian Vazquez":        "H",
    "Carlos Ortiz":             "R",
    "Abraham Ancer":            "R",
    "Marcelo Garza":            "Y",
    "Jose Cristobal Islas":     "Y",
    "José de Jesús Rodríguez":  "Y",
}

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



@st.cache_data(ttl=3600)
def fetch_player_results(player_id, tour_code):
    """Fetch all tournament results for a player including earnings."""
    query = f"""
    {{
      playerProfileTournamentResults(playerId: "{player_id}", tourCode: {tour_code}) {{
        tournaments {{
          tournamentOverview {{
            tournamentId
            tournamentName
            courseCity
            courseCountry
          }}
          overviewInfo {{
            wins
            top10
            cutsMade
            cutsMissed
            money
          }}
        }}
      }}
    }}
    """
    try:
        r = requests.post("https://orchestrator.pgatour.com/graphql",
                          headers=PGA_HEADERS, json={"query": query}, timeout=15)
        return r.json()["data"]["playerProfileTournamentResults"]["tournaments"]
    except:
        return []

@st.cache_data(ttl=3600)
def fetch_finish_position(tournament_id, player_id):
    """Get finish position from leaderboard for a specific player."""
    query = f"""
    {{
      leaderboardV2(id: "{tournament_id}") {{
        players {{
          ... on PlayerRowV2 {{
            position
            score
            total
            player {{ id }}
          }}
        }}
      }}
    }}
    """
    try:
        r = requests.post("https://orchestrator.pgatour.com/graphql",
                          headers=PGA_HEADERS, json={"query": query}, timeout=15)
        players = r.json()["data"]["leaderboardV2"]["players"]
        for p in players:
            if p.get("player") and p["player"].get("id") == player_id:
                return p.get("position", "—"), p.get("score", "—")
    except:
        pass
    return None, None

def get_results_for_athlete(name):
    """Get full results history for an athlete if we have their ID."""
    player_id = PLAYER_IDS.get(name)
    tour_code = PLAYER_TOUR_CODE.get(name)
    if not player_id or not tour_code:
        return []

    tournaments = fetch_player_results(player_id, tour_code)
    results = []
    for t in tournaments:
        ov = t.get("tournamentOverview")
        info = t.get("overviewInfo")
        if not ov or not info:
            continue

        cut_missed = info.get("cutsMissed", 0) > 0
        earnings = info.get("money", 0)
        wins = info.get("wins", 0)
        top10 = info.get("top10", 0)
        tid = ov.get("tournamentId", "")
        tname = ov.get("tournamentName", "")

        # Get position from leaderboard if made cut
        position, score = None, None
        if not cut_missed and tid:
            position, score = fetch_finish_position(tid, player_id)

        results.append({
            "tournament_id": tid,
            "name": tname,
            "name_lower": tname.lower(),
            "location": ov.get("courseCity", ""),
            "cut_missed": cut_missed,
            "earnings": earnings,
            "wins": wins,
            "top10": top10,
            "position": position or ("CUT" if cut_missed else "—"),
            "score": score or "—",
        })

    return results

def get_possible_events(name, upcoming_by_tour, manual_exemptions):
    """Get events player could possibly enter based on tour membership + manual exemptions."""
    possible = []

    # Tour membership based possible events
    tour_code = TOUR_MEMBERSHIP.get(name)
    if tour_code and tour_code in upcoming_by_tour:
        tour_names = {"R": "PGA Tour", "H": "Korn Ferry Tour", "Y": "PGA Tour Americas"}
        for t in upcoming_by_tour[tour_code]:
            possible.append({
                "name": t["tournamentName"],
                "date": ts_to_date(t["startDate"]),
                "location": f"{t.get('city','')} {t.get('country','')}".strip(),
                "tour": tour_names[tour_code],
                "purse": t.get("purse", ""),
                "status": "possible"
            })

    # Manual exemptions — look up date from known schedules
    exemptions = manual_exemptions.get(name, [])
    all_known_events = (
        [(t["tournamentName"], ts_to_date(t["startDate"]), t.get("city","") + " " + t.get("country",""), t.get("purse",""), "PGA Tour") for t in upcoming_by_tour.get("R", [])] +
        [(t["tournamentName"], ts_to_date(t["startDate"]), t.get("city","") + " " + t.get("country",""), t.get("purse",""), "Korn Ferry Tour") for t in upcoming_by_tour.get("H", [])] +
        [(t["tournamentName"], ts_to_date(t["startDate"]), t.get("city","") + " " + t.get("country",""), t.get("purse",""), "PGA Tour Americas") for t in upcoming_by_tour.get("Y", [])] +
        [(e["name"], e["start_date"], e["location"], e["purse"], "LPGA Tour") for e in LPGA_SCHEDULE_2026] +
        [(e["name"], e["start_date"], e["location"], e["purse"], "Asian Tour") for e in ASIAN_TOUR_SCHEDULE_2026]
    )
    for event_name in exemptions:
        # Try to find the event in known schedules
        matched_date, matched_loc, matched_purse, matched_tour = "TBD", "", "", "Exempt Entry"
        for known_name, known_date, known_loc, known_purse, known_tour in all_known_events:
            if fuzz.token_sort_ratio(event_name.lower(), known_name.lower()) >= 75:
                matched_date = known_date
                matched_loc = known_loc
                matched_purse = known_purse
                matched_tour = known_tour
                break
        possible.append({
            "name": event_name,
            "date": matched_date,
            "location": matched_loc.strip(),
            "tour": matched_tour,
            "purse": matched_purse,
            "status": "possible"
        })

    return possible

def build_athlete_data(mexican_golfers, manual_exemptions={}):
    athletes = {name:{"events":[],"tour":"Unknown","possible":[]} for name in mexican_golfers}

    # Pre-fetch upcoming events for each tour for possible events
    upcoming_by_tour = {}
    for code in ["R", "H", "Y"]:
        up, _ = fetch_pga_schedule(code)
        upcoming_by_tour[code] = up
    for name in mexican_golfers:
        matched,score,_ = fuzzy_match(name, LIV_ROSTER_2026, threshold=85)
        if matched:
            athletes[name]["tour"] = "LIV Golf"
            for e in LIV_SCHEDULE_2026:
                athletes[name]["events"].append({"name":e["name"],"date":e["start_date"],"location":e["location"],"tour":"LIV Golf","purse":"N/A"})

    # Asian Tour / International Series
    for name in mexican_golfers:
        if name in ASIAN_TOUR_MEXICAN_PLAYERS:
            if athletes[name]["tour"] == "Unknown":
                athletes[name]["tour"] = "Asian Tour"
            for e in ASIAN_TOUR_SCHEDULE_2026:
                # Carlos Ortiz only plays International Series, not all Asian Tour events
                if name == "Carlos Ortiz" and e["series"] != "International Series":
                    continue
                # Santiago skips Hong Kong Open — conflicts with Mexico Open
                if name == "Santiago de La Fuente" and e["name"] == "Link Hong Kong Open":
                    continue
                athletes[name]["events"].append({
                    "name": e["name"],
                    "date": e["start_date"],
                    "location": e["location"],
                    "tour": f"Asian Tour — {e['series']}",
                    "purse": e["purse"]
                })

    # LPGA Tour
    for name in mexican_golfers:
        if name in LPGA_MEXICAN_PLAYERS:
            athletes[name]["tour"] = "LPGA Tour"
            for e in LPGA_SCHEDULE_2026:
                athletes[name]["events"].append({
                    "name": e["name"],
                    "date": e["start_date"],
                    "location": e["location"],
                    "tour": "LPGA Tour",
                    "purse": e["purse"]
                })

    for tour_code, tour_name in [("R","PGA Tour"),("H","Korn Ferry Tour"),("Y","PGA Tour Americas")]:
        upcoming, completed = fetch_pga_schedule(tour_code)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = [ex.submit(fetch_event_and_search, t, mexican_golfers, tour_name) for t in upcoming+completed]
            for f in concurrent.futures.as_completed(futures):
                for entry in f.result():
                    n = entry["athlete"]
                    if athletes[n]["tour"] == "Unknown": athletes[n]["tour"] = tour_name
                    athletes[n]["events"].append(entry)
    # Add possible events for tour members and exempt entries
    for name in mexican_golfers:
        possible = get_possible_events(name, upcoming_by_tour, manual_exemptions)
        # Only add as possible if not already confirmed in that event
        confirmed_names = [e["name"].lower() for e in athletes[name]["events"]]
        for p in possible:
            if not any(fuzz.token_sort_ratio(p["name"].lower(), c) >= 80 for c in confirmed_names):
                athletes[name]["possible"].append(p)

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
    show_asian = st.checkbox("Asian Tour", value=True)
    st.markdown("---")
    weeks_ahead = st.slider("📅 Weeks ahead", 1, 16, 8)
    st.markdown("---")
    st.markdown("---")
    st.markdown("**🎟️ Sponsor Exemptions / Special Entries**")
    st.caption("For non-tour-members entering specific events. Format: Player | Tournament")
    exemptions_input = st.text_area(
        "Exemptions:",
        value="",
        height=80,
        placeholder="Santiago de La Fuente | VidantaWorld Mexico Open",
        label_visibility="collapsed"
    )
    parsed_exemptions = {}
    for line in exemptions_input.strip().split("\n"):
        if "|" in line:
            parts = line.split("|")
            if len(parts) == 2:
                player = parts[0].strip()
                event = parts[1].strip()
                if player not in parsed_exemptions:
                    parsed_exemptions[player] = []
                parsed_exemptions[player].append(event)
    st.session_state["manual_exemptions"] = parsed_exemptions
    if st.button("✅ Apply Exemptions", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.markdown("**🏌️ LPGA Confirmed Entries** *(update Tuesday of event week)*")
    st.caption("Format: Player Name | Tournament Name")
    lpga_confirmed_input = st.text_area(
        "Confirmed:",
        value="",
        height=100,
        placeholder="Gaby Lopez | Walmart NW Arkansas Championship\nMaria Fassi | Walmart NW Arkansas Championship",
        label_visibility="collapsed"
    )
    # Save LPGA confirmed to session_state
    parsed_lpga = {}
    for line in lpga_confirmed_input.strip().split("\n"):
        if "|" in line:
            parts = line.split("|")
            if len(parts) == 2:
                player = parts[0].strip()
                event = parts[1].strip()
                if player not in parsed_lpga:
                    parsed_lpga[player] = []
                parsed_lpga[player].append(event)
    st.session_state["lpga_confirmed"] = parsed_lpga
    if st.button("✅ Apply LPGA Entries", use_container_width=True):
        st.rerun()

    st.markdown("---")
    verify_on = st.checkbox("✅ Nationality verification", value=False)
    st.caption("Confirms Mexican nationality via API. Slower.")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption("PGA Tour · Korn Ferry · PGA Tour Americas: live\nLIV Golf · LPGA · Asian Tour: 2026 hardcoded\nRefreshes every 30min")
    st.markdown("---")
    st.markdown("**🇲🇽 Mexico Events**")
    st.info("VidantaWorld Mexico Open\nOct 28 — Field posts Tuesday Oct 20\n\nExpect: Santiago de La Fuente, Álvaro Ortiz, Omar Morales")

st.markdown("""<div class="hero"><h1>MEXICAN ATHLETE TRACKER</h1>
<p>Professional golf — worldwide competitions — live data</p>
<div class="updated">Last updated: """ + datetime.now().strftime('%B %d, %Y at %H:%M') + """</div></div>""", unsafe_allow_html=True)

# Get exemptions and confirmed from session_state
manual_exemptions = st.session_state.get("manual_exemptions", {})
lpga_confirmed = st.session_state.get("lpga_confirmed", {})

with st.spinner("Fetching live tournament data across all tours..."):
    athlete_data = build_athlete_data(MEXICAN_GOLFERS, manual_exemptions)

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

                    # Personal info from database
                    db = ATHLETE_DB.get(name, {})
                    if db:
                        st.markdown(f"""
                        <div class="profile-section">
                          <div style="margin-bottom:0.75rem">
                            <span class="profile-stat"><div class="stat-val">{db.get("age","—")}</div><div class="stat-label">Age</div></span>
                            <span class="profile-stat"><div class="stat-val">{db.get("turned_pro","—")}</div><div class="stat-label">Turned Pro</div></span>
                            <span class="profile-stat"><div class="stat-val">{db.get("wins","—")}</div><div class="stat-label">Pro Wins</div></span>
                            <span class="profile-stat"><div class="stat-val">#{db.get("current_ranking","—")}</div><div class="stat-label">Current Rank</div></span>
                            <span class="profile-stat"><div class="stat-val">#{db.get("best_ranking","—")}</div><div class="stat-label">Best Rank</div></span>
                          </div>
                          <div style="font-size:0.8rem;color:#888;margin-bottom:0.5rem">📍 {db.get("birthplace","—")} &nbsp;|&nbsp; 🎓 {db.get("college","—")}</div>
                          <div style="font-size:0.82rem;color:#bbb;line-height:1.5">{db.get("bio","")}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Sponsors
                        sponsors = db.get("sponsors", [])
                        if sponsors:
                            st.markdown("**🤝 Current Sponsors:**")
                            sponsor_html = " ".join([f'<span class="sponsor-chip">{s["name"]} <span class="cat">· {s["category"]}</span></span>' for s in sponsors])
                            st.markdown(sponsor_html, unsafe_allow_html=True)
                        else:
                            st.markdown("**🤝 Sponsors:** *No sponsors on file — [contact us to add]*")

                        # Career highlights
                        highlights = db.get("highlights", [])
                        if highlights:
                            with st.expander("🏆 Career Highlights"):
                                for h in highlights:
                                    st.markdown(f'<div class="highlight-item">⭐ {h}</div>', unsafe_allow_html=True)

                        # News popup button
                        if st.button(f"📰 Latest News — {name.split()[0]}", key=f"news_{name}"):
                            st.session_state[f"show_news_{name}"] = True

                        # News popup
                        if st.session_state.get(f"show_news_{name}"):
                            with st.container():
                                st.markdown(f"---\n**📰 Recent News: {name}**")
                                with st.spinner("Searching for latest news..."):
                                    try:
                                        from xml.etree import ElementTree as ET
                                        news_found = False
                                        rss_urls = [
                                            "https://www.pgatour.com/rss/news.xml",
                                            "https://www.golfchannel.com/rss/feed",
                                        ]
                                        for rss_url in rss_urls:
                                            try:
                                                r = requests.get(rss_url, headers=HEADERS, timeout=8)
                                                if r.status_code == 200:
                                                    root = ET.fromstring(r.content)
                                                    items = root.findall(".//item")
                                                    first = name.split()[0].lower()
                                                    last = name.split()[-1].lower()
                                                    relevant = []
                                                    for item in items:
                                                        t = item.find("title")
                                                        txt = t.text if t is not None else ""
                                                        if first in txt.lower() or last in txt.lower():
                                                            l = item.find("link")
                                                            p = item.find("pubDate")
                                                            relevant.append({
                                                                "title": txt,
                                                                "link": l.text if l is not None else "#",
                                                                "date": p.text[:16] if p is not None else ""
                                                            })
                                                    if relevant:
                                                        for n in relevant[:4]:
                                                            st.markdown(f"• [{n['title']}]({n['link']}) *{n['date']}*")
                                                        news_found = True
                                                        break
                                            except:
                                                continue
                                        if not news_found:
                                            search_name = name.replace(" ", "+")
                                            st.markdown(f"No news in feeds — [Search Google News for {name}](https://www.google.com/search?q={search_name}+golf&tbm=nws)")
                                    except Exception as e:
                                        search_name = name.replace(" ", "+")
                                        st.markdown(f"[Search Google News for {name}](https://www.google.com/search?q={search_name}+golf&tbm=nws)")
                                if st.button("Close", key=f"close_news_{name}"):
                                    st.session_state[f"show_news_{name}"] = False
                                    st.rerun()
                with cb:
                    st.markdown(f'<div style="text-align:right"><div style="font-family:Bebas Neue,sans-serif;font-size:2rem;color:#006847">{len(upcoming)}</div><div style="font-size:0.7rem;color:#666;text-transform:uppercase">Upcoming</div></div>', unsafe_allow_html=True)
                # Merge possible events into upcoming display
                possible_events = data.get("possible", [])
                possible_filtered = [p for p in possible_events 
                                    if p["date"] == "TBD" or today <= p["date"] <= cutoff]

                # Combine confirmed + possible, sort by date
                combined = []
                for e in upcoming:
                    combined.append({**e, "status": "confirmed"})
                for p in possible_filtered:
                    # Don't add if already in confirmed
                    if not any(fuzz.token_sort_ratio(p["name"].lower(), e["name"].lower()) >= 80 
                               for e in upcoming):
                        combined.append({**p, "status": "possible"})
                combined.sort(key=lambda x: x["date"] if x["date"] != "TBD" else "9999")

                if combined:
                    st.markdown("**Upcoming Events:**")
                    if tour == "LPGA Tour":
                        confirmed_for_player = lpga_confirmed.get(name, [])
                        for e in combined:
                            is_confirmed = any(fuzz.token_sort_ratio(e["name"].lower(), c.lower()) >= 80 for c in confirmed_for_player)
                            if is_confirmed:
                                st.markdown(f'<div class="event-card" style="border-left-color:#66bb6a"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} <span class="upcoming-pill">confirmed</span></p><p class="event-meta">📍 {e["location"]} &nbsp;|&nbsp; {badge(e["tour"])} &nbsp;|&nbsp; 💰 {e.get("purse","")}</p></div><div class="event-date">{e["date"]}</div></div></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="event-card" style="border-left-color:#f48fb1"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} <span style="background:#2a1a2e;color:#f48fb1;border:1px solid #f48fb1;border-radius:20px;padding:2px 8px;font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:1px">possible</span></p><p class="event-meta">📍 {e["location"]} &nbsp;|&nbsp; {badge(e["tour"])} &nbsp;|&nbsp; 💰 {e.get("purse","")}</p></div><div class="event-date">{e["date"]}</div></div></div>', unsafe_allow_html=True)
                        if not combined:
                            st.caption("⚠️ LPGA fields post Tuesday of event week.")
                    else:
                        st.markdown("**Upcoming Events:**")
                        for e in combined:
                            if e.get("status") == "possible":
                                st.markdown(f'<div class="event-card" style="border-left-color:#ffa726;opacity:0.85"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} <span style="background:#2e2a1a;color:#ffa726;border:1px solid #ffa726;border-radius:20px;padding:2px 8px;font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:1px">possible</span></p><p class="event-meta">📍 {e["location"]} &nbsp;|&nbsp; {badge(e["tour"])}</p></div><div class="event-date" style="color:#ffa726">{e["date"]}</div></div></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="event-card"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} <span class="upcoming-pill">upcoming</span></p><p class="event-meta">📍 {e["location"]} &nbsp;|&nbsp; {badge(e["tour"])}</p></div><div class="event-date">{e["date"]}</div></div></div>', unsafe_allow_html=True)
                else:
                    st.markdown("*No events found in selected time range.*")


                if past:
                    with st.expander(f"Past events ({len(past)})"):
                        # Get results data if available
                        results_data = get_results_for_athlete(name)
                        # Build results lookup with fuzzy matching
                        def find_result(event_name, results_list):
                            if not results_list:
                                return None
                            best_score = 0
                            best_result = None
                            for r in results_list:
                                score = fuzz.token_sort_ratio(
                                    strip_accents(event_name.lower()),
                                    strip_accents(r["name"].lower())
                                )
                                if score > best_score:
                                    best_score = score
                                    best_result = r
                            return best_result if best_score >= 70 else None

                        for e in past[-10:]:
                            result = find_result(e["name"], results_data)

                            if result:
                                pos = result["position"]
                                earnings = f"💰 ${result['earnings']:,}" if result["earnings"] else ""
                                score = f"({result['score']})" if result["score"] and result["score"] != "—" else ""

                                if pos == "CUT":
                                    pos_badge = '<span style="background:#2a1a1a;color:#ef5350;border:1px solid #ef5350;border-radius:20px;padding:2px 8px;font-size:0.65rem;font-weight:600">✂️ CUT</span>'
                                    pos_color = "#ef5350"
                                elif result["wins"]:
                                    pos_badge = '<span style="background:#1a2a1a;color:#66bb6a;border:1px solid #66bb6a;border-radius:20px;padding:2px 8px;font-size:0.65rem;font-weight:600">🏆 WIN</span>'
                                    pos_color = "#66bb6a"
                                elif result["top10"]:
                                    pos_badge = f'<span style="background:#1a2e1a;color:#66bb6a;border:1px solid #66bb6a;border-radius:20px;padding:2px 8px;font-size:0.65rem;font-weight:600">{pos} {score}</span>'
                                    pos_color = "#66bb6a"
                                else:
                                    pos_badge = f'<span style="background:#1a1a1a;color:#aaa;border:1px solid #444;border-radius:20px;padding:2px 8px;font-size:0.65rem">{pos} {score}</span>'
                                    pos_color = "#666"

                                st.markdown(f'<div class="event-card" style="opacity:0.8;border-left-color:{pos_color}"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} &nbsp;{pos_badge}</p><p class="event-meta">📍 {e["location"]} &nbsp;|&nbsp; {badge(e["tour"])} &nbsp;{earnings}</p></div><div class="event-date">{e["date"]}</div></div></div>', unsafe_allow_html=True)
                            else:
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
    sub1,sub2,sub3,sub4,sub5,sub6 = st.tabs(["PGA Tour","Korn Ferry","PGA Tour Americas","LIV Golf","LPGA Tour","Asian Tour"])
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

    with sub6:
        st.caption("🌏 Asian Tour + International Series — Santiago de La Fuente & Carlos Ortiz (Int'l Series only)")
        for e in ASIAN_TOUR_SCHEDULE_2026:
            is_up = e["start_date"] >= today
            pill = '<span class="upcoming-pill">upcoming</span>' if is_up else '<span class="past-pill">completed</span>'
            series_badge = '<span style="background:#1a2e2e;color:#80cbc4;border:1px solid #80cbc4;border-radius:20px;padding:2px 8px;font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:1px">Int\'l Series</span>' if e["series"] == "International Series" else '<span style="background:#1a1a1a;color:#aaa;border:1px solid #444;border-radius:20px;padding:2px 8px;font-size:0.65rem;letter-spacing:1px">Asian Tour</span>'
            st.markdown(f'<div class="event-card" style="opacity:{"1" if is_up else "0.4"}"><div style="display:flex;justify-content:space-between;align-items:center"><div><p class="event-name">{e["name"]} &nbsp;{pill} &nbsp;{series_badge}</p><p class="event-meta">📍 {e["location"]} &nbsp;|&nbsp; 💰 {e["purse"]}</p></div><div class="event-date">{e["start_date"]}</div></div></div>', unsafe_allow_html=True)
