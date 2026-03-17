import os
import sys
import argparse
import requests
import xarray as xr
from datetime import datetime

# --- Constants ---
REQUIREMENTS_TXT = """pystac
xarray
netCDF4
h5netcdf
requests
click
"""

TEMPLATE_BUILD_SCRIPT = """import os
import pystac
import xarray as xr
from datetime import datetime, timezone

# --- Configuration (Auto-Generated) ---
# Adjust these variable names to match your data
TIME_VAR = "{time_var}"
LAT_VAR = "{lat_var}"
LON_VAR = "{lon_var}"

COLLECTION_ID = "{slug}"
COLLECTION_TITLE = "{title}"
COLLECTION_DESC = "{desc}"

def get_bbox_and_time(file_path):
    \"\"\"
    Extracts bounding box and datetime from a file using Xarray.
    Adjust this logic for your specific data format.
    \"\"\"
    try:
        ds = xr.open_dataset(file_path)

        # Time
        if TIME_VAR and TIME_VAR in ds:
            # Simplistic: take the first time, or min/max
            # Often data is a single time slice
            dt_val = ds[TIME_VAR].values[0] if ds[TIME_VAR].ndim > 0 else ds[TIME_VAR].values
            # Convert numpy/pandas timestamp to python datetime
            dt = datetime.fromisoformat(str(dt_val).replace("T", " "))
            # Ensure timezone aware (UTC)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            print(f"Warning: Time var '{{TIME_VAR}}' not found. Using now.")
            dt = datetime.now(timezone.utc)

        # BBox
        if LAT_VAR in ds and LON_VAR in ds:
            min_lat = float(ds[LAT_VAR].min())
            max_lat = float(ds[LAT_VAR].max())
            min_lon = float(ds[LON_VAR].min())
            max_lon = float(ds[LON_VAR].max())
            bbox = [min_lon, min_lat, max_lon, max_lat]
        else:
            print(f"Warning: Geo vars '{{LAT_VAR}}/{{LON_VAR}}' not found. Using global.")
            bbox = [-180.0, -90.0, 180.0, 90.0]

        return bbox, dt
    except Exception as e:
        print(f"Error reading metadata from {{file_path}}: {{e}}")
        # Fallback
        return [-180, -90, 180, 90], datetime.now(timezone.utc)

def main():
    # 1. Create Catalog
    catalog = pystac.Catalog(id="catalog", description="Root Catalog")

    # 2. Create Collection
    collection = pystac.Collection(
        id=COLLECTION_ID,
        title=COLLECTION_TITLE,
        description=COLLECTION_DESC,
        extent=pystac.Extent(
            pystac.SpatialExtent([[-180, -90, 180, 90]]),
            pystac.TemporalExtent([[datetime.now(timezone.utc), None]])
        )
    )
    catalog.add_child(collection)

    # 3. Process Files (Example: look in 'data/' folder)
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"Created {{data_dir}}/ folder. Put your data there.")

    for filename in os.listdir(data_dir):
        if not filename.endswith((".nc", ".h5", ".tif")):
            continue

        file_path = os.path.join(data_dir, filename)
        print(f"Processing {{filename}}...")

        bbox, dt = get_bbox_and_time(file_path)

        item = pystac.Item(
            id=os.path.splitext(filename)[0],
            geometry=None, # Populate if you have polygon geometry
            bbox=bbox,
            datetime=dt,
            properties={}
        )
        # Add Asset
        item.add_asset(
            key="data",
            asset=pystac.Asset(href=f"./data/{{filename}}", media_type=pystac.MediaType.HDF5) # Adjust media type
        )

        collection.add_item(item)

    # 4. Save
    print("Saving Catalog...")
    catalog.normalize_hrefs("./stac_output")
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print("Done! Validating...")
    catalog.validate_all()

if __name__ == "__main__":
    main()
"""

# --- Helpers ---
def input_secure(prompt):
    print(f"\n{prompt}", end=' ', flush=True)
    return sys.stdin.readline().strip()

def download_file(url, local_path):
    print(f"Downloading sample from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Saved to {local_path}")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def analyze_netcdf(file_path):
    print(f"\nAnalyzing {file_path} for STAC hints...")
    hints = {"time_var": "", "lat_var": "", "lon_var": ""}
    try:
        ds = xr.open_dataset(file_path)
        # Heuristics
        for v in ['time', 't', 'date', 'time_coverage_start']:
            if v in ds or hasattr(ds, v):
                hints['time_var'] = v
                break
        for v in ['lat', 'latitude', 'LAT']:
            if v in ds:
                hints['lat_var'] = v
                break
        for v in ['lon', 'longitude', 'LON']:
            if v in ds:
                hints['lon_var'] = v
                break
        return hints
    except:
        return hints

def main():
    print("=== Simple STAC Project Creator (pystac) ===")

    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", help="Project folder name")
    parser.add_argument("--download", help="URL to download sample")
    args = parser.parse_args()

    # 1. Setup
    if args.slug:
        slug = args.slug
    else:
        slug = input_secure("Project Name (slug):")

    if not slug: sys.exit(1)

    base_dir = os.path.join(os.getcwd(), slug)
    if os.path.exists(base_dir):
        print(f"Error: {base_dir} already exists.")
        sys.exit(1)

    os.makedirs(base_dir)
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir)

    # 2. Download / Sample
    sample_path = None
    if args.download:
        fname = os.path.basename(args.download) or "sample.nc"
        local_path = os.path.join(data_dir, fname)
        if download_file(args.download, local_path):
            sample_path = local_path

    # 3. Analyze
    hints = {"time_var": "", "lat_var": "", "lon_var": ""}
    if sample_path:
        hints = analyze_netcdf(sample_path)

    # 4. Generate Files
    # requirements.txt
    with open(os.path.join(base_dir, "requirements.txt"), "w") as f:
        f.write(REQUIREMENTS_TXT)

    # build_stac.py
    script_content = TEMPLATE_BUILD_SCRIPT.format(
        time_var=hints['time_var'],
        lat_var=hints['lat_var'],
        lon_var=hints['lon_var'],
        slug=slug,
        title=slug.replace("-", " ").title(),
        desc=f"STAC Collection for {slug}"
    )

    with open(os.path.join(base_dir, "build_stac.py"), "w") as f:
        f.write(script_content)

    print(f"\n--- Project Created: {slug} ---")
    print(f"1. cd {slug}")
    print(f"2. pip install -r requirements.txt")
    print(f"3. python3 build_stac.py")

if __name__ == "__main__":
    main()
