"""Fetch the most recent satellite image for a location from Planetary Computer."""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import planetary_computer
import rioxarray  # noqa: F401 — registers the rio accessor
from pystac_client import Client

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
CONFIG_PATH = ROOT_DIR / "config.json"
OUTPUT_DIR = ROOT_DIR / "output"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    cfg = load_config()
    p = argparse.ArgumentParser(description="Fetch recent satellite imagery.")
    p.add_argument("--location", type=str, help="Place name to geocode")
    p.add_argument("--lat", type=float, help="Latitude")
    p.add_argument("--lon", type=float, help="Longitude")
    p.add_argument("--days", type=int, default=cfg["days_back"], help="Days to look back")
    p.add_argument("--cloud-cover", type=int, default=cfg["max_cloud_cover"], help="Max cloud cover %%")
    p.add_argument("--collection", type=str, default=cfg["collection"], help="STAC collection")
    return p.parse_args()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def open_image(path: Path) -> None:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", str(path)])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", str(path)])
        else:
            print(f"Image saved to {path} (auto-open not supported on {system})")
    except Exception:
        print(f"Could not auto-open image. Saved to: {path}")


def main() -> None:
    args = parse_args()
    cfg = load_config()

    # Resolve coordinates
    if args.location:
        from geocode import geocode
        lat, lon = geocode(args.location)
        label = args.location
        print(f"Geocoded '{args.location}' → {lat:.4f}, {lon:.4f}")
    elif args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
        label = f"{lat:.2f}_{lon:.2f}"
    else:
        print("Error: Provide --location or --lat/--lon", file=sys.stderr)
        sys.exit(1)

    # Build search parameters
    buf = cfg["buffer_degrees"]
    bbox = [lon - buf, lat - buf, lon + buf, lat + buf]
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=args.days)
    date_range = f"{start_date:%Y-%m-%d}/{end_date:%Y-%m-%d}"

    print(f"Searching {args.collection} | bbox={[round(c,3) for c in bbox]} | {date_range} | cloud<{args.cloud_cover}%")

    # Search STAC catalog
    catalog = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(
        collections=[args.collection],
        bbox=bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": args.cloud_cover}},
        sortby=[{"field": "datetime", "direction": "desc"}],
        max_items=5,
    )
    items = list(search.items())
    if not items:
        print("No images found matching criteria. Try increasing --days or --cloud-cover.")
        sys.exit(1)

    # Pick the most recent item
    item = items[0]
    props = item.properties
    capture_date = props.get("datetime", "unknown")
    cloud_pct = props.get("eo:cloud_cover", "?")
    print(f"Found {len(items)} image(s). Using most recent:")
    print(f"  Date captured : {capture_date}")
    print(f"  Cloud cover   : {cloud_pct}%")
    print(f"  Item ID       : {item.id}")

    # Choose the best RGB asset
    if "visual" in item.assets:
        asset_key = "visual"
    elif "rendered_preview" in item.assets:
        asset_key = "rendered_preview"
    else:
        print("Error: No visual/RGB asset found in this item.", file=sys.stderr)
        print(f"Available assets: {list(item.assets.keys())}", file=sys.stderr)
        sys.exit(1)

    href = item.assets[asset_key].href
    print(f"  Asset         : {asset_key}")
    print(f"Downloading image (overview level {cfg['overview_level']})...")

    # Load the image via rioxarray at an overview level for speed
    import rioxarray as rxr
    overview = cfg["overview_level"]
    da = rxr.open_rasterio(href, overview_level=overview)

    # Render to PNG
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = capture_date[:10] if isinstance(capture_date, str) else "unknown"
    filename = f"{slugify(label)}_{date_str}.png"
    out_path = OUTPUT_DIR / filename

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    # da shape is (bands, height, width) — transpose for imshow
    img_data = da.values
    if img_data.shape[0] in (3, 4):
        img_data = img_data[:3].transpose(1, 2, 0)  # (H, W, 3)
        # Normalize to 0-1 if needed (uint16 or large values)
        if img_data.max() > 255:
            img_data = (img_data / img_data.max() * 255).astype("uint8")
        elif img_data.dtype != "uint8":
            img_data = img_data.astype("uint8")
    ax.imshow(img_data)
    ax.set_axis_off()
    ax.set_title(f"{label} — {date_str} (cloud {cloud_pct}%)", fontsize=12)
    fig.savefig(out_path, bbox_inches="tight", dpi=150, pad_inches=0.1)
    plt.close(fig)

    print(f"Saved: {out_path}")
    open_image(out_path)


if __name__ == "__main__":
    main()
