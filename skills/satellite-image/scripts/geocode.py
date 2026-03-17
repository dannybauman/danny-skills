"""Geocode a place name to lat/lon using OpenStreetMap Nominatim."""

import sys
import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode(place_name: str) -> tuple[float, float]:
    """Return (lat, lon) for a place name, or raise on failure."""
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": place_name, "format": "json", "limit": 1},
        headers={"User-Agent": "claude-skills-satellite-image/1.0"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"Could not geocode '{place_name}' — no results found.")
    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    return lat, lon


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python geocode.py 'Place Name'", file=sys.stderr)
        sys.exit(1)
    lat, lon = geocode(" ".join(sys.argv[1:]))
    print(f"{lat},{lon}")
