---
name: satellite-image
description: Fetch recent Sentinel-2 satellite imagery from Microsoft Planetary Computer. Use when the user wants satellite photos, earth observation images, or remote sensing data for a location.
---

# satellite-image

Fetches the most recent satellite image of a location from Microsoft Planetary Computer (Sentinel-2). No API key required.

## Usage

Run `./run.sh` with either a place name or coordinates:

```bash
# By place name
./run.sh --location "San Francisco"

# By coordinates
./run.sh --lat 37.77 --lon -122.42

# With options
./run.sh --location "Mount Fuji" --days 180 --cloud-cover 10
```

## Options

- `--location "Place Name"` — Geocode a place name to coordinates
- `--lat` / `--lon` — Specify coordinates directly
- `--days N` — Look back N days (default: 90)
- `--cloud-cover N` — Max cloud cover percentage (default: 30)
- `--collection NAME` — STAC collection (default: sentinel-2-l2a)

## Instructions for Claude

To fetch a satellite image, run `./run.sh` from the `satellite-image/` directory with the appropriate arguments. The script sets up its own virtual environment automatically. The resulting PNG is saved to `output/` and opened in the system image viewer.
