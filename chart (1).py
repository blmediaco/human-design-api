#!/usr/bin/env python3
"""
Projector.Solutions HD Engine - Unified
Built in English, for everyone.
"""

import swisseph as swe
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime

app = FastAPI(title="Projector.Solutions HD Engine")

# Initialize the location tools
geolocator = Nominatim(user_agent="projector_solutions_api")
tf = TimezoneFinder()

class BirthData(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str  # Replaced utc_offset

def get_historical_offset(city: str, year: int, month: int, day: int, hour: int, minute: int) -> float:
    """Converts a city string to the exact UTC offset for a specific historical date/time."""
    # 1. Geocode the city
    location = geolocator.geocode(city)
    if not location:
        raise ValueError(f"Could not locate the city: {city}. Try adding the state or country.")

    # 2. Find the Timezone name (e.g., 'America/Boise')
    tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    if not tz_name:
        raise ValueError("Could not determine the timezone for those coordinates.")

    # 3. Calculate the exact UTC offset for that specific date (automatically handles DST)
    local_tz = pytz.timezone(tz_name)
    dt_naive = datetime(year, month, day, hour, minute)
    
    try:
        dt_aware = local_tz.localize(dt_naive)
    except pytz.exceptions.AmbiguousTimeError:
        # Handles the rare 1-hour overlap during Fall DST switch
        dt_aware = local_tz.localize(dt_naive, is_dst=False)

    # Convert seconds to hours
    offset_hours = dt_aware.utcoffset().total_seconds() / 3600
    return offset_hours

@app.post("/generate-chart")
def generate_chart(data: BirthData):
    try:
        # Auto-calculate the offset based on the city and birth date
        calculated_offset = get_historical_offset(
            data.city, data.year, data.month, data.day, data.hour, data.minute
        )

        result = calculate_chart(
            birth_year=data.year,
            birth_month=data.month,
            birth_day=data.day,
            birth_hour=data.hour,
            birth_minute=data.minute,
            utc_offset=calculated_offset
        )
        
        # Inject the parsed location data into the payload so the frontend can display it
        result["location_metadata"] = {
            "query": data.city,
            "calculated_offset": calculated_offset
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Set ephemeris path (uses built-in moshier ephemeris - no files needed)
swe.set_ephe_path('')

# ─────────────────────────────────────────────
# GATE MAP: ecliptic degree → Human Design gate
# Each gate spans 5.625 degrees (360 / 64 gates)
# ─────────────────────────────────────────────

GATE_SEQUENCE = [
    25, 17, 21, 51, 42, 3,   # Aries
    27, 24, 2,  23, 8,  20,  # Taurus
    16, 35, 45, 12, 15, 52,  # Gemini
    39, 53, 62, 56, 31, 33,  # Cancer
    7,  4,  29, 59, 40, 64,  # Leo
    47, 6,  46, 18, 48, 57,  # Virgo+Libra
    32, 50, 28, 44, 1,  43,  # Libra+Scorpio
    14, 34, 9,  5,  26, 11,  # Scorpio+Sag
    10, 58, 38, 54, 61, 60,  # Cap
    41, 19, 13, 49, 30, 55,  # Aquarius
    37, 63, 22, 36            # Pisces
]

HD_START_DEGREE = 358.25  # 28°15' Pisces

CENTERS = {
    "Head":     [61, 63, 64],
    "Ajna":     [4, 11, 17, 24, 43, 47],
    "Throat":   [8, 12, 16, 20, 23, 31, 33, 35, 45, 56, 62],
    "Self":     [1, 2, 7, 10, 13, 15, 25, 46],
    "Sacral":   [3, 5, 9, 14, 27, 29, 34, 42, 59],
    "Root":     [19, 28, 38, 39, 41, 52, 53, 54, 58, 60],
    "Spleen":   [18, 28, 32, 44, 48, 50, 57],
    "Solar Plexus": [6, 22, 30, 36, 37, 49, 55],
    "Heart":    [21, 26, 40, 51]
}

CHANNELS = [
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15),
    (6, 59), (7, 31), (9, 52), (10, 20), (11, 56),
    (12, 22), (13, 33), (16, 48), (17, 62), (18, 58),
    (19, 49), (20, 34), (20, 57), (21, 45), (23, 43),
    (24, 61), (25, 51), (26, 44), (27, 50), (28, 38),
    (29, 46), (30, 41), (32, 54), (34, 57), (35, 36),
    (37, 40), (39, 55), (42, 53), (47, 64)
]

CHANNEL_CENTERS = {
    (1, 8):   ("Self", "Throat"),
    (2, 14):  ("Self", "Sacral"),
    (3, 60):  ("Sacral", "Root"),
    (4, 63):  ("Ajna", "Head"),
    (5, 15):  ("Sacral", "Self"),
    (6, 59):  ("Solar Plexus", "Sacral"),
    (7, 31):  ("Self", "Throat"),
    (9, 52):  ("Sacral", "Root"),
    (10, 20): ("Self", "Throat"),
    (11, 56): ("Ajna", "Throat"),
    (12, 22): ("Throat", "Solar Plexus"),
    (13, 33): ("Self", "Throat"),
    (16, 48): ("Throat", "Spleen"),
    (17, 62): ("Ajna", "Throat"),
    (18, 58): ("Spleen", "Root"),
    (19, 49): ("Root", "Solar Plexus"),
    (20, 34): ("Throat", "Sacral"),
    (20, 57): ("Throat", "Spleen"),
    (21, 45): ("Heart", "Throat"),
    (23, 43): ("Throat", "Ajna"),
    (24, 61): ("Ajna", "Head"),
    (25, 51): ("Self", "Heart"),
    (26, 44): ("Heart", "Spleen"),
    (27, 50): ("Sacral", "Spleen"),
    (28, 38): ("Spleen", "Root"),
    (29, 46): ("Sacral", "Self"),
    (30, 41): ("Solar Plexus", "Root"),
    (32, 54): ("Spleen", "Root"),
    (34, 57): ("Sacral", "Spleen"),
    (35, 36): ("Throat", "Solar Plexus"),
    (37, 40): ("Solar Plexus", "Heart"),
    (39, 55): ("Root", "Solar Plexus"),
    (42, 53): ("Sacral", "Root"),
    (47, 64): ("Ajna", "Head")
}

def degree_to_gate_line(degree):
    gate_size = 360 / 64
    line_size = gate_size / 6
    adjusted = (degree - HD_START_DEGREE) % 360
    index = int(adjusted / gate_size)
    line = int((adjusted % gate_size) / line_size) + 1
    return GATE_SEQUENCE[index], line

def get_planet_positions(jd):
    """Get gate/line for all HD-relevant planets in standard Jovian Archive order."""
    results = {}
    
    # 1. Sun & Earth
    sun_deg = swe.calc_ut(jd, swe.SUN)[0][0]
    gate, line = degree_to_gate_line(sun_deg)
    results["Sun"] = {"degree": sun_deg, "gate": gate, "line": line}
    
    earth_deg = (sun_deg + 180) % 360
    gate, line = degree_to_gate_line(earth_deg)
    results["Earth"] = {"degree": earth_deg, "gate": gate, "line": line}

    # 2. Nodes (True Node)
    nn_deg = swe.calc_ut(jd, swe.TRUE_NODE)[0][0]
    gate, line = degree_to_gate_line(nn_deg)
    results["N.Node"] = {"degree": nn_deg, "gate": gate, "line": line}

    sn_deg = (nn_deg + 180) % 360
    gate, line = degree_to_gate_line(sn_deg)
    results["S.Node"] = {"degree": sn_deg, "gate": gate, "line": line}

    # 3. Remaining Planets
    planets = {
        "Moon":    swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus":   swe.VENUS,
        "Mars":    swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn":  swe.SATURN,
        "Uranus":  swe.URANUS,
        "Neptune": swe.NEPTUNE,
        "Pluto":   swe.PLUTO,
    }

    for name, planet_id in planets.items():
        pos = swe.calc_ut(jd, planet_id)[0][0]
        gate, line = degree_to_gate_line(pos)
        results[name] = {"degree": pos, "gate": gate, "line": line}
        
    return results

def get_defined_centers(all_gates):
    defined = set()
    gate_set = set(all_gates)
    
    for g1, g2 in CHANNELS:
        if g1 in gate_set and g2 in gate_set:
            if (g1, g2) in CHANNEL_CENTERS:
                c1, c2 = CHANNEL_CENTERS[(g1, g2)]
                defined.add(c1)
                defined.add(c2)
    return defined

def determine_type(defined_centers, all_gates):
    has_sacral = "Sacral" in defined_centers
    has_throat = "Throat" in defined_centers
    
    motor_centers = {"Sacral", "Heart", "Solar Plexus", "Root"}
    motor_to_throat = False
    
    gate_set = set(all_gates)
    graph = {center: set() for center in CENTERS.keys()}
    
    for g1, g2 in CHANNELS:
        if g1 in gate_set and g2 in gate_set:
            if (g1, g2) in CHANNEL_CENTERS:
                c1, c2 = CHANNEL_CENTERS[(g1, g2)]
                graph[c1].add(c2)
                graph[c2].add(c1)

    if has_throat:
        visited = set()
        queue = ["Throat"]
        
        while queue:
            current = queue.pop(0)
            if current not in visited:
                visited.add(current)
                if current in motor_centers:
                    motor_to_throat = True
                    break
                queue.extend(list(graph[current] - visited))

    if not defined_centers:
        return "Reflector"
    elif has_sacral and motor_to_throat:
        return "Manifesting Generator"
    elif has_sacral:
        return "Generator"
    elif motor_to_throat:
        return "Manifestor"
    else:
        return "Projector"

def determine_authority(defined_centers):
    priority = [
        ("Solar Plexus", "Emotional"),
        ("Sacral", "Sacral"),
        ("Spleen", "Splenic"),
        ("Heart", "Ego"),
        ("Self", "Self-Projected"),
    ]
    for center, authority in priority:
        if center in defined_centers:
            return authority
    return "Mental/Outer"

def calculate_chart(birth_year, birth_month, birth_day, birth_hour, birth_minute, utc_offset):
    utc_hour = birth_hour - utc_offset
    jd_personality = swe.julday(birth_year, birth_month, birth_day, 
                                 utc_hour + birth_minute/60)
    
    p_sun_deg = swe.calc_ut(jd_personality, swe.SUN)[0][0]
    target_design_deg = (p_sun_deg - 88) % 360
    jd_low = jd_personality - 100
    jd_high = jd_personality - 80
    
    for _ in range(50):
        jd_mid = (jd_low + jd_high) / 2
        jd_design = jd_mid
        sun_deg = swe.calc_ut(jd_mid, swe.SUN)[0][0]
        diff = (sun_deg - target_design_deg + 180) % 360 - 180
        if abs(diff) < 0.0001:
            break
        if diff > 0:
            jd_high = jd_mid
        else:
            jd_low = jd_mid
    
    personality = get_planet_positions(jd_personality)
    design = get_planet_positions(jd_design)
    
    all_gates = set()
    for p in personality.values():
        all_gates.add(p["gate"])
    for p in design.values():
        all_gates.add(p["gate"])
    
    defined_centers = get_defined_centers(all_gates)
    
    p_sun_line = personality["Sun"]["line"]
    d_sun_line = design["Sun"]["line"]
    profile = f"{p_sun_line}/{d_sun_line}"
    
    hd_type = determine_type(defined_centers, all_gates)
    authority = determine_authority(defined_centers)
    
    return {
        "type": hd_type,
        "profile": profile,
        "authority": authority,
        "defined_centers": sorted(defined_centers),
        "undefined_centers": sorted(set(CENTERS.keys()) - defined_centers),
        "personality": personality,
        "design": design,
        "all_active_gates": sorted(all_gates)
    }

def print_chart(result, name=""):
    print(f"\n{'='*50}")
    if name:
        print(f"  Human Design Chart: {name}")
    print(f"{'='*50}")
    print(f"  Type:      {result['type']}")
    print(f"  Profile:   {result['profile']}")
    print(f"  Authority: {result['authority']}")
    print(f"\n  Defined Centers:")
    for c in result['defined_centers']:
        print(f"    ✓ {c}")
    print(f"\n  Open Centers:")
    for c in result['undefined_centers']:
        print(f"    ○ {c}")
    print(f"\n  Active Gates: {result['all_active_gates']}")
    print(f"\n  Personality (Conscious) - Black:")
    for planet, data in result['personality'].items():
        print(f"    {planet:<10} Gate {data['gate']}.{data['line']}  ({data['degree']:.2f}°)")
    print(f"\n  Design (Unconscious) - Red:")
    for planet, data in result['design'].items():
        print(f"    {planet:<10} Gate {data['gate']}.{data['line']}  ({data['degree']:.2f}°)")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    print("\n✦ Human Design Chart Engine ✦\n")
    name = input("Name: ")
    city = input("City, State/Country (e.g., Boise, Idaho): ")
    birth_year = int(input("Birth year (e.g. 1988): "))
    birth_month = int(input("Birth month (e.g. 10): "))
    birth_day = int(input("Birth day (e.g. 9): "))
    birth_hour = int(input("Birth hour in 24hr format (e.g. 14): "))
    birth_minute = int(input("Birth minute (e.g. 30): "))
    
    # Test the geocoding logic locally
    try:
        calculated_offset = get_historical_offset(city, birth_year, birth_month, birth_day, birth_hour, birth_minute)
        print(f"\n[System] Found '{city}'. UTC Offset for this date: {calculated_offset}")
        
        result = calculate_chart(
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            birth_hour=birth_hour,
            birth_minute=birth_minute,
            utc_offset=calculated_offset
        )
        print_chart(result, name)
    except Exception as e:
        print(f"\n[Error] {e}")