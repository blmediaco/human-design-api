#!/usr/bin/env python3
"""
Projector.Solutions HD Engine - Railway compatible.
Built in English, for everyone.
"""

import math
from datetime import datetime

import pytz
from fastapi import FastAPI, HTTPException
from geopy.geocoders import Nominatim
from pydantic import BaseModel
from timezonefinder import TimezoneFinder


app = FastAPI(title="Projector.Solutions HD Engine")

geolocator = Nominatim(user_agent="projector_solutions_api")
tf = TimezoneFinder()


class BirthData(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str


def get_historical_offset(city: str, year: int, month: int, day: int, hour: int, minute: int) -> float:
    """Convert a city string to the exact UTC offset for a historical date/time."""
    location = geolocator.geocode(city)
    if not location:
        raise ValueError(f"Could not locate the city: {city}. Try adding the state or country.")

    tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    if not tz_name:
        raise ValueError("Could not determine the timezone for those coordinates.")

    local_tz = pytz.timezone(tz_name)
    dt_naive = datetime(year, month, day, hour, minute)

    try:
        dt_aware = local_tz.localize(dt_naive)
    except pytz.exceptions.AmbiguousTimeError:
        dt_aware = local_tz.localize(dt_naive, is_dst=False)

    return dt_aware.utcoffset().total_seconds() / 3600


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-chart")
def generate_chart(data: BirthData):
    try:
        calculated_offset = get_historical_offset(
            data.city, data.year, data.month, data.day, data.hour, data.minute
        )

        result = calculate_chart(
            birth_year=data.year,
            birth_month=data.month,
            birth_day=data.day,
            birth_hour=data.hour,
            birth_minute=data.minute,
            utc_offset=calculated_offset,
        )

        result["location_metadata"] = {
            "query": data.city,
            "calculated_offset": calculated_offset,
        }

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


GATE_SEQUENCE = [
    25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20,
    16, 35, 45, 12, 15, 52,
    39, 53, 62, 56, 31, 33,
    7, 4, 29, 59, 40, 64,
    47, 6, 46, 18, 48, 57,
    32, 50, 28, 44, 1, 43,
    14, 34, 9, 5, 26, 11,
    10, 58, 38, 54, 61, 60,
    41, 19, 13, 49, 30, 55,
    37, 63, 22, 36,
]

HD_START_DEGREE = 358.25

CENTERS = {
    "Head": [61, 63, 64],
    "Ajna": [4, 11, 17, 24, 43, 47],
    "Throat": [8, 12, 16, 20, 23, 31, 33, 35, 45, 56, 62],
    "Self": [1, 2, 7, 10, 13, 15, 25, 46],
    "Sacral": [3, 5, 9, 14, 27, 29, 34, 42, 59],
    "Root": [19, 28, 38, 39, 41, 52, 53, 54, 58, 60],
    "Spleen": [18, 28, 32, 44, 48, 50, 57],
    "Solar Plexus": [6, 22, 30, 36, 37, 49, 55],
    "Heart": [21, 26, 40, 51],
}

CHANNELS = [
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15),
    (6, 59), (7, 31), (9, 52), (10, 20), (11, 56),
    (12, 22), (13, 33), (16, 48), (17, 62), (18, 58),
    (19, 49), (20, 34), (20, 57), (21, 45), (23, 43),
    (24, 61), (25, 51), (26, 44), (27, 50), (28, 38),
    (29, 46), (30, 41), (32, 54), (34, 57), (35, 36),
    (37, 40), (39, 55), (42, 53), (47, 64),
]

CHANNEL_CENTERS = {
    (1, 8): ("Self", "Throat"),
    (2, 14): ("Self", "Sacral"),
    (3, 60): ("Sacral", "Root"),
    (4, 63): ("Ajna", "Head"),
    (5, 15): ("Sacral", "Self"),
    (6, 59): ("Solar Plexus", "Sacral"),
    (7, 31): ("Self", "Throat"),
    (9, 52): ("Sacral", "Root"),
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
    (47, 64): ("Ajna", "Head"),
}


def normalize_degrees(value):
    return value % 360.0


def sin_deg(value):
    return math.sin(math.radians(value))


def cos_deg(value):
    return math.cos(math.radians(value))


def atan2_deg(y, x):
    return normalize_degrees(math.degrees(math.atan2(y, x)))


def julday(year, month, day, hour):
    if month <= 2:
        year -= 1
        month += 12

    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)

    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
        + hour / 24
    )


def sun_longitude(jd):
    n = jd - 2451545.0
    mean_longitude = normalize_degrees(280.460 + 0.9856474 * n)
    mean_anomaly = normalize_degrees(357.528 + 0.9856003 * n)
    return normalize_degrees(
        mean_longitude
        + 1.915 * sin_deg(mean_anomaly)
        + 0.020 * sin_deg(2 * mean_anomaly)
    )


def moon_longitude(jd):
    n = jd - 2451545.0
    mean_longitude = normalize_degrees(218.316 + 13.176396 * n)
    mean_anomaly = normalize_degrees(134.963 + 13.064993 * n)
    sun_mean_anomaly = normalize_degrees(357.529 + 0.98560028 * n)
    elongation = normalize_degrees(297.850 + 12.190749 * n)
    argument_latitude = normalize_degrees(93.272 + 13.229350 * n)

    return normalize_degrees(
        mean_longitude
        + 6.289 * sin_deg(mean_anomaly)
        + 1.274 * sin_deg(2 * elongation - mean_anomaly)
        + 0.658 * sin_deg(2 * elongation)
        + 0.214 * sin_deg(2 * mean_anomaly)
        - 0.186 * sin_deg(sun_mean_anomaly)
        - 0.114 * sin_deg(2 * argument_latitude)
    )


def node_longitude(jd):
    n = jd - 2451545.0
    return normalize_degrees(125.04452 - 0.0529538083 * n)


def orbital_elements(planet, d):
    elements = {
        "Mercury": (48.3313 + 3.24587e-5 * d, 7.0047 + 5e-8 * d, 29.1241 + 1.01444e-5 * d, 0.387098, 0.205635 + 5.59e-10 * d, 168.6562 + 4.0923344368 * d),
        "Venus": (76.6799 + 2.4659e-5 * d, 3.3946 + 2.75e-8 * d, 54.8910 + 1.38374e-5 * d, 0.723330, 0.006773 - 1.302e-9 * d, 48.0052 + 1.6021302244 * d),
        "Earth": (0.0, 0.0, 282.9404 + 4.70935e-5 * d, 1.000000, 0.016709 - 1.151e-9 * d, 356.0470 + 0.9856002585 * d),
        "Mars": (49.5574 + 2.11081e-5 * d, 1.8497 - 1.78e-8 * d, 286.5016 + 2.92961e-5 * d, 1.523688, 0.093405 + 2.516e-9 * d, 18.6021 + 0.5240207766 * d),
        "Jupiter": (100.4542 + 2.76854e-5 * d, 1.3030 - 1.557e-7 * d, 273.8777 + 1.64505e-5 * d, 5.20256, 0.048498 + 4.469e-9 * d, 19.8950 + 0.0830853001 * d),
        "Saturn": (113.6634 + 2.3898e-5 * d, 2.4886 - 1.081e-7 * d, 339.3939 + 2.97661e-5 * d, 9.55475, 0.055546 - 9.499e-9 * d, 316.9670 + 0.0334442282 * d),
        "Uranus": (74.0005 + 1.3978e-5 * d, 0.7733 + 1.9e-8 * d, 96.6612 + 3.0565e-5 * d, 19.18171 - 1.55e-8 * d, 0.047318 + 7.45e-9 * d, 142.5905 + 0.011725806 * d),
        "Neptune": (131.7806 + 3.0173e-5 * d, 1.7700 - 2.55e-7 * d, 272.8461 - 6.027e-6 * d, 30.05826 + 3.313e-8 * d, 0.008606 + 2.15e-9 * d, 260.2471 + 0.005995147 * d),
        "Pluto": (110.30347, 17.14175, 113.76329, 39.48168677, 0.24880766, 14.53 + 0.00396 * d),
    }
    return elements[planet]


def heliocentric_xyz(planet, jd):
    d = jd - 2451543.5
    ascending_node, inclination, perihelion, semi_major_axis, eccentricity, mean_anomaly = orbital_elements(planet, d)
    mean_anomaly = normalize_degrees(mean_anomaly)

    eccentric_anomaly = mean_anomaly + math.degrees(
        eccentricity * sin_deg(mean_anomaly) * (1 + eccentricity * cos_deg(mean_anomaly))
    )
    xv = semi_major_axis * (cos_deg(eccentric_anomaly) - eccentricity)
    yv = semi_major_axis * math.sqrt(1 - eccentricity * eccentricity) * sin_deg(eccentric_anomaly)

    true_anomaly = atan2_deg(yv, xv)
    radius = math.sqrt(xv * xv + yv * yv)
    argument = true_anomaly + perihelion

    xh = radius * (
        cos_deg(ascending_node) * cos_deg(argument)
        - sin_deg(ascending_node) * sin_deg(argument) * cos_deg(inclination)
    )
    yh = radius * (
        sin_deg(ascending_node) * cos_deg(argument)
        + cos_deg(ascending_node) * sin_deg(argument) * cos_deg(inclination)
    )
    zh = radius * sin_deg(argument) * sin_deg(inclination)
    return xh, yh, zh


def planet_longitude(name, jd):
    if name == "Sun":
        return sun_longitude(jd)
    if name == "Earth":
        return normalize_degrees(sun_longitude(jd) + 180)
    if name == "Moon":
        return moon_longitude(jd)
    if name == "N.Node":
        return node_longitude(jd)
    if name == "S.Node":
        return normalize_degrees(node_longitude(jd) + 180)

    px, py, _ = heliocentric_xyz(name, jd)
    ex, ey, _ = heliocentric_xyz("Earth", jd)
    return atan2_deg(py - ey, px - ex)


def degree_to_gate_line(degree):
    gate_size = 360 / 64
    line_size = gate_size / 6
    adjusted = (degree - HD_START_DEGREE) % 360
    index = int(adjusted / gate_size)
    line = int((adjusted % gate_size) / line_size) + 1
    return GATE_SEQUENCE[index], line


def get_planet_positions(jd):
    results = {}
    planets = [
        "Sun",
        "Earth",
        "N.Node",
        "S.Node",
        "Moon",
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
    ]

    for name in planets:
        degree = planet_longitude(name, jd)
        gate, line = degree_to_gate_line(degree)
        results[name] = {"degree": degree, "gate": gate, "line": line}

    return results


def get_defined_centers(all_gates):
    defined = set()
    gate_set = set(all_gates)

    for g1, g2 in CHANNELS:
        if g1 in gate_set and g2 in gate_set and (g1, g2) in CHANNEL_CENTERS:
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
        if g1 in gate_set and g2 in gate_set and (g1, g2) in CHANNEL_CENTERS:
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
    if has_sacral and motor_to_throat:
        return "Manifesting Generator"
    if has_sacral:
        return "Generator"
    if motor_to_throat:
        return "Manifestor"
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
    jd_personality = julday(
        birth_year,
        birth_month,
        birth_day,
        utc_hour + birth_minute / 60,
    )

    p_sun_deg = planet_longitude("Sun", jd_personality)
    target_design_deg = (p_sun_deg - 88) % 360
    jd_low = jd_personality - 100
    jd_high = jd_personality - 80
    jd_design = jd_low

    for _ in range(50):
        jd_mid = (jd_low + jd_high) / 2
        jd_design = jd_mid
        sun_deg = planet_longitude("Sun", jd_mid)
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
        "all_active_gates": sorted(all_gates),
    }


def print_chart(result, name=""):
    print(f"\n{'=' * 50}")
    if name:
        print(f"  Human Design Chart: {name}")
    print(f"{'=' * 50}")
    print(f"  Type:      {result['type']}")
    print(f"  Profile:   {result['profile']}")
    print(f"  Authority: {result['authority']}")
    print("\n  Defined Centers:")
    for c in result["defined_centers"]:
        print(f"    - {c}")
    print("\n  Open Centers:")
    for c in result["undefined_centers"]:
        print(f"    - {c}")
    print(f"\n  Active Gates: {result['all_active_gates']}")
    print("\n  Personality (Conscious) - Black:")
    for planet, data in result["personality"].items():
        print(f"    {planet:<10} Gate {data['gate']}.{data['line']}  ({data['degree']:.2f} deg)")
    print("\n  Design (Unconscious) - Red:")
    for planet, data in result["design"].items():
        print(f"    {planet:<10} Gate {data['gate']}.{data['line']}  ({data['degree']:.2f} deg)")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    print("\nHuman Design Chart Engine\n")
    name = input("Name: ")
    city = input("City, State/Country (e.g., Boise, Idaho): ")
    birth_year = int(input("Birth year (e.g. 1988): "))
    birth_month = int(input("Birth month (e.g. 10): "))
    birth_day = int(input("Birth day (e.g. 9): "))
    birth_hour = int(input("Birth hour in 24hr format (e.g. 14): "))
    birth_minute = int(input("Birth minute (e.g. 30): "))

    try:
        calculated_offset = get_historical_offset(
            city, birth_year, birth_month, birth_day, birth_hour, birth_minute
        )
        print(f"\n[System] Found '{city}'. UTC Offset for this date: {calculated_offset}")

        chart_result = calculate_chart(
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            birth_hour=birth_hour,
            birth_minute=birth_minute,
            utc_offset=calculated_offset,
        )
        print_chart(chart_result, name)
    except Exception as exc:
        print(f"\n[Error] {exc}")
