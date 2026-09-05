"""Place name -> coordinates.

Coordinates are what the engine needs, and they are stored on the profile so a
chart never depends on re-resolving a place name later. A place can be renamed
or a geocoder can change its mind; a latitude cannot.

Two sources, in order:
  1. A built-in table of major cities, so the app works with no network at all.
  2. Open-Meteo's geocoding API, which needs no API key.
"""
from __future__ import annotations

import unicodedata
from typing import Any

import httpx

# A small offline gazetteer. Enough that the app is usable without a network,
# and enough to cover the places test charts are cast for.
BUILTIN_PLACES: list[dict[str, Any]] = [
    {"name": "New Delhi", "country": "India", "admin": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"name": "Mumbai", "country": "India", "admin": "Maharashtra", "lat": 19.0760, "lon": 72.8777},
    {"name": "Kolkata", "country": "India", "admin": "West Bengal", "lat": 22.5726, "lon": 88.3639},
    {"name": "Chennai", "country": "India", "admin": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707},
    {"name": "Bengaluru", "country": "India", "admin": "Karnataka", "lat": 12.9716, "lon": 77.5946},
    {"name": "Hyderabad", "country": "India", "admin": "Telangana", "lat": 17.3850, "lon": 78.4867},
    {"name": "Pune", "country": "India", "admin": "Maharashtra", "lat": 18.5204, "lon": 73.8567},
    {"name": "Ahmedabad", "country": "India", "admin": "Gujarat", "lat": 23.0225, "lon": 72.5714},
    {"name": "Jaipur", "country": "India", "admin": "Rajasthan", "lat": 26.9124, "lon": 75.7873},
    {"name": "Lucknow", "country": "India", "admin": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462},
    {"name": "Varanasi", "country": "India", "admin": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739},
    {"name": "Prayagraj", "country": "India", "admin": "Uttar Pradesh", "lat": 25.4358, "lon": 81.8463},
    {"name": "Porbandar", "country": "India", "admin": "Gujarat", "lat": 21.6417, "lon": 69.6293},
    {"name": "Patna", "country": "India", "admin": "Bihar", "lat": 25.5941, "lon": 85.1376},
    {"name": "Bhopal", "country": "India", "admin": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126},
    {"name": "Nagpur", "country": "India", "admin": "Maharashtra", "lat": 21.1458, "lon": 79.0882},
    {"name": "Surat", "country": "India", "admin": "Gujarat", "lat": 21.1702, "lon": 72.8311},
    {"name": "Kochi", "country": "India", "admin": "Kerala", "lat": 9.9312, "lon": 76.2673},
    {"name": "Thiruvananthapuram", "country": "India", "admin": "Kerala", "lat": 8.5241, "lon": 76.9366},
    {"name": "Chandigarh", "country": "India", "admin": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    {"name": "Amritsar", "country": "India", "admin": "Punjab", "lat": 31.6340, "lon": 74.8723},
    {"name": "Guwahati", "country": "India", "admin": "Assam", "lat": 26.1445, "lon": 91.7362},
    {"name": "Bhubaneswar", "country": "India", "admin": "Odisha", "lat": 20.2961, "lon": 85.8245},
    {"name": "Indore", "country": "India", "admin": "Madhya Pradesh", "lat": 22.7196, "lon": 75.8577},
    {"name": "Kathmandu", "country": "Nepal", "admin": "Bagmati", "lat": 27.7172, "lon": 85.3240},
    {"name": "Pokhara", "country": "Nepal", "admin": "Gandaki", "lat": 28.2096, "lon": 83.9856},
    {"name": "Colombo", "country": "Sri Lanka", "admin": "Western", "lat": 6.9271, "lon": 79.8612},
    {"name": "Dhaka", "country": "Bangladesh", "admin": "Dhaka", "lat": 23.8103, "lon": 90.4125},
    {"name": "Karachi", "country": "Pakistan", "admin": "Sindh", "lat": 24.8607, "lon": 67.0011},
    {"name": "Lahore", "country": "Pakistan", "admin": "Punjab", "lat": 31.5204, "lon": 74.3587},
    {"name": "London", "country": "United Kingdom", "admin": "England", "lat": 51.5074, "lon": -0.1278},
    {"name": "New York", "country": "United States", "admin": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "San Francisco", "country": "United States", "admin": "California", "lat": 37.7749, "lon": -122.4194},
    {"name": "Chicago", "country": "United States", "admin": "Illinois", "lat": 41.8781, "lon": -87.6298},
    {"name": "Toronto", "country": "Canada", "admin": "Ontario", "lat": 43.6532, "lon": -79.3832},
    {"name": "Sydney", "country": "Australia", "admin": "New South Wales", "lat": -33.8688, "lon": 151.2093},
    {"name": "Melbourne", "country": "Australia", "admin": "Victoria", "lat": -37.8136, "lon": 144.9631},
    {"name": "Singapore", "country": "Singapore", "admin": "", "lat": 1.3521, "lon": 103.8198},
    {"name": "Dubai", "country": "United Arab Emirates", "admin": "Dubai", "lat": 25.2048, "lon": 55.2708},
    {"name": "Kuala Lumpur", "country": "Malaysia", "admin": "", "lat": 3.1390, "lon": 101.6869},
    {"name": "Tokyo", "country": "Japan", "admin": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"name": "Hong Kong", "country": "Hong Kong", "admin": "", "lat": 22.3193, "lon": 114.1694},
    {"name": "Berlin", "country": "Germany", "admin": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"name": "Ulm", "country": "Germany", "admin": "Baden-Wurttemberg", "lat": 48.4011, "lon": 9.9876},
    {"name": "Paris", "country": "France", "admin": "Ile-de-France", "lat": 48.8566, "lon": 2.3522},
    {"name": "Moscow", "country": "Russia", "admin": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"name": "Johannesburg", "country": "South Africa", "admin": "Gauteng", "lat": -26.2041, "lon": 28.0473},
    {"name": "Nairobi", "country": "Kenya", "admin": "Nairobi", "lat": -1.2921, "lon": 36.8219},
    {"name": "Sao Paulo", "country": "Brazil", "admin": "Sao Paulo", "lat": -23.5505, "lon": -46.6333},
    {"name": "Mexico City", "country": "Mexico", "admin": "", "lat": 19.4326, "lon": -99.1332},
    {"name": "Auckland", "country": "New Zealand", "admin": "Auckland", "lat": -36.8485, "lon": 174.7633},
    {"name": "Tromso", "country": "Norway", "admin": "Troms", "lat": 69.6492, "lon": 18.9553},
    {"name": "Suva", "country": "Fiji", "admin": "Central", "lat": -18.1416, "lon": 178.4419},
]


def _fold(s: str) -> str:
    """Case- and accent-insensitive comparison key."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", s.lower().strip())
        if not unicodedata.combining(c)
    )


def _label(row: dict[str, Any]) -> str:
    bits = [row["name"]]
    if row.get("admin"):
        bits.append(row["admin"])
    if row.get("country"):
        bits.append(row["country"])
    return ", ".join(bits)


def search_builtin(query: str, limit: int = 8) -> list[dict[str, Any]]:
    q = _fold(query)
    if not q:
        return []
    starts, contains = [], []
    for row in BUILTIN_PLACES:
        name = _fold(row["name"])
        if name.startswith(q):
            starts.append(row)
        elif q in name or q in _fold(row.get("country", "")):
            contains.append(row)
    out = starts + contains
    return [{
        "name": r["name"], "country": r.get("country", ""),
        "admin": r.get("admin", ""), "latitude": r["lat"], "longitude": r["lon"],
        "label": _label(r), "source": "builtin",
    } for r in out[:limit]]


async def search_remote(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """Open-Meteo geocoding. No key required."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query, "count": limit, "language": "en", "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []

    out = []
    for row in data.get("results") or []:
        out.append({
            "name": row.get("name", ""),
            "country": row.get("country", ""),
            "admin": row.get("admin1", "") or "",
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "label": ", ".join(x for x in [row.get("name"), row.get("admin1"),
                                           row.get("country")] if x),
            "timezone": row.get("timezone"),
            "population": row.get("population"),
            "source": "open-meteo",
        })
    return out


async def search(query: str, limit: int = 8) -> dict[str, Any]:
    """Built-in matches first, then remote results that add something new."""
    local = search_builtin(query, limit)
    remote = await search_remote(query, limit)

    seen = {(round(r["latitude"], 2), round(r["longitude"], 2)) for r in local}
    merged = list(local)
    for r in remote:
        if r["latitude"] is None or r["longitude"] is None:
            continue
        key = (round(r["latitude"], 2), round(r["longitude"], 2))
        if key in seen:
            continue
        seen.add(key)
        merged.append(r)

    return {
        "query": query,
        "results": merged[:limit],
        "offline": not remote,
        "note": ("Showing built-in places only -- the geocoding service could "
                 "not be reached. You can still enter coordinates directly."
                 if not remote else None),
    }
