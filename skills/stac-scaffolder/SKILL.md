---
name: stac-scaffolder
description: Scaffolds a STAC (SpatioTemporal Asset Catalog) project using pystac. Use when the user wants to create a STAC catalog, organize geospatial datasets, or generate metadata for satellite imagery and earth observation data.
---

# Agent Instructions

This skill helps users bootstrap a **Simple STAC Generator** for any dataset using the modern `pystac` library (avoiding complex `stactools` templates).

## Workflow

1.  **Data Discovery (Agentic Step)**:
    *   Ask the user: "Do you have a sample file, or should I help you find one?"
    *   **IF FIND**:
        *   Use your search tools to find "sample data [dataset name] download url".
        *   Look for public URLs (e.g., `.nc`, `.tif`, `.h5`).
        *   Confirm the URL with the user.
        *   *Tip*: For NASA data, look for "Sample Products" on PO.DAAC.

2.  **Scaffolding & Download**:
    *   Run the scaffolder wrapper (handles dependencies auto-magically):
    *   **Option A (Have URL)**:
        ```bash
        ./run.sh --slug "my-project" --download "URL"
        ```
    *   **Option B (Local File)**:
        ```bash
        ./run.sh --slug "my-project"
        ```
        *(Then manually copy your file to `my-project/data/`)*

3.  **Result**:
    *   The script creates a folder `my-project/` containing `build_stac.py`.
    *   It **auto-injects** detected metadata (Time/Geo variables) into the python script.

4.  **Handover**:
    *   Instruct the user:
        1.  `cd my-project`
        2.  `pip install -r requirements.txt`
        3.  `python3 build_stac.py`
    *   The `build_stac.py` script is stand-alone. Iterate on it to perfect your catalog!

## Tips for Finding Data
*   **Is it already STAC?**: If you see `.json` files, you're done! If you see `.nc`/`.tif`, proceed with this skill.
*   **NetCDF files**: The script handles `.nc` metadata extraction well. Provide one if possible!

## Packaging for Claude

To zip this skill for upload, run this from the root of the repository:

```bash
zip -r stac-scaffolder.zip stac-scaffolder/ -x "*/.venv/*" "*/output/*" "*/input/*" "*/.env" "*/__pycache__/*" "*/.DS_Store"
```
