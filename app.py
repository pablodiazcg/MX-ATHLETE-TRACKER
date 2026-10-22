import subprocess

with open("/Users/pablodiazcg/Downloads/app.py", "r") as f:
    content = f.read()

# Fix Yael Chahin — correct ranking and turned pro year
content = content.replace(
    '"turned_pro": 2023,\n        "college": "Colorado Mesa University",\n        "wins": 0,\n        "current_ranking": 500,\n        "best_ranking": 500,',
    '"turned_pro": 2024,\n        "college": "Colorado Mesa University",\n        "wins": 0,\n        "current_ranking": 2511,\n        "best_ranking": 2497,'
)

# Fix Alvaro Ortiz — now on PGA Tour with 2 KFT wins
content = content.replace(
    '"wins": 5,\n        "current_ranking": 180,\n        "best_ranking": 180,',
    '"wins": 5,\n        "current_ranking": 120,\n        "best_ranking": 120,'
)

# Add Roberto Lebrija to PLAYER_IDS
content = content.replace(
    '"Yael Chahin":             "66975",\n}',
    '"Yael Chahin":             "66975",\n    "Roberto Lebrija":         "37124",\n}'
)

# Add Roberto Lebrija to PLAYER_TOUR_CODE
content = content.replace(
    '"Yael Chahin":             "Y",\n}',
    '"Yael Chahin":             "Y",\n    "Roberto Lebrija":         "R",\n}'
)

# Add Roberto Lebrija to ASIAN_TOUR_MEXICAN_PLAYERS
content = content.replace(
    'ASIAN_TOUR_MEXICAN_PLAYERS = [\n    "Santiago de La Fuente",\n    "Carlos Ortiz",\n]',
    'ASIAN_TOUR_MEXICAN_PLAYERS = [\n    "Santiago de La Fuente",\n    "Carlos Ortiz",\n    "Roberto Lebrija",\n]'
)

# Add Roberto Lebrija to DEFAULT_MEXICAN_GOLFERS
content = content.replace(
    '"Yael Chahin",\n    "Marcelo Garza",',
    '"Yael Chahin",\n    "Roberto Lebrija",\n    "Marcelo Garza",'
)

# Add Roberto Lebrija to ATHLETE_DB
lebrija_entry = '''    "Roberto Lebrija": {
        "full_name": "Roberto Lebrija",
        "born": "March 9, 1999",
        "birthplace": "Mexico City, Mexico",
        "age": 27,
        "height": "6\'2\\"",
        "turned_pro": 2023,
        "college": "Lynn University / University of Oregon",
        "wins": 0,
        "current_ranking": 1094,
        "best_ranking": 1094,
        "wins_list": [],
        "highlights": [
            "Active International Series competitor 2026",
            "Multiple PGA Tour Americas starts",
            "PGA Tour starts including Mexico Open and 3M Open",
            "From Mexico City, Mexico",
            "Attended Lynn University and University of Oregon",
        ],
        "sponsors": [],
        "social": {},
        "bio": "Young Mexican professional from Mexico City. Attended Lynn University and University of Oregon. Competing on the Asian Tour International Series alongside PGA Tour and PGA Tour Americas events. One of Mexico\\'s most versatile touring professionals.",
    },
'''

content = content.replace(
    '"Yael Chahin": {',
    lebrija_entry + '\n    "Yael Chahin": {'
)

with open("/Users/pablodiazcg/Downloads/app.py", "w") as f:
    f.write(content)

check = open("/Users/pablodiazcg/Downloads/app.py").read()
print("✅ Yael ranking fixed" if "2511" in check else "❌ Missing")
print("✅ Roberto Lebrija added" if "Mexico City, Mexico" in check and "Lebrija" in check else "❌ Missing")
print("✅ Lebrija in PLAYER_IDS" if '"Roberto Lebrija":         "37124"' in check else "❌ Missing")
print("✅ Lebrija in Asian Tour" if '"Roberto Lebrija"' in check and "ASIAN_TOUR_MEXICAN_PLAYERS" in check else "❌ Missing")

subprocess.run(['pbcopy'], input=check.encode('utf-8'))
print("\n✅ Copied! GitHub → pencil → Cmd+A → Delete → Cmd+V → Commit!")
