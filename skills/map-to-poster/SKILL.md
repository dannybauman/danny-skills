---
name: map-to-poster
description: Transforms cities into minimalist map posters. Use when the user asks to create a map poster, generate city-based art, or visualize a geographic area using MapToPoster.
---

# Map-to-Poster

This skill is a lean implementation of the **[MapToPoster](https://github.com/originalankur/maptoposter)** project created by **[Ankur Bharti](https://github.com/originalankur)**. It allows you to create beautiful, minimalist map designs from OpenStreetMap data.

> [!NOTE]
> This skill includes only the essential scripts and assets (< 2MB) while ignoring heavy caches and example data.

## Workflow

1.  **Preparation**:
    *   Prompt the user for the **city** and **country** if not specified.
    *   Identify the desired **vibe** (e.g., "vintage", "dark", "blue") and map it to a theme.
2.  **Execution**:
    *   Run the command with the selected options:
        ```bash
        ./run.sh --city "City Name" --country "Country" [options]
        ```

2.  **Options**:
    *   `--theme` / `-t`: Theme name (17 available).
    *   `--distance` / `-d`: Radius in meters (e.g., `5000` for downtown, `30000` for regions).
    *   `--forests`: [NEW] Include detailed forest, woodland, and natural terrain.
    *   `--buildings`: [NEW] Include building footprints for dense urban detail.
    *   `--name`: Custom city title.
    *   `--country-label`: Custom country subtitle.

3.  **Setup**:
    *   `run.sh` automatically manages the Python virtual environment and dependencies using `uv` or `venv`. No manual setup is required by the agent.

4.  **Output**:
    *   Generated posters are saved to the `output/` directory inside this skill folder.
    *   Format: `{city}_{theme}_{timestamp}.png`.

## Theme & Vibe Mapping

| Theme | Aesthetic / Vibe |
|-------|-------|
| `noir` | Dark, moody, modern, black & white |
| `warm_beige` | Vintage, old-school, sepia, classic |
| `pastel_dream` | Soft, colorful, bright, dreamy |
| `blueprint` | Technical, architectural, geometric, blue |
| `forest` | Deep greens, sage, organic, botanical |
| `ocean` | Blues, teals, coastal, aquatic |
| `neon_cyberpunk` | Electric pink/cyan, futuristic, dark |
| `midnight_blue` | Navy & gold, premium, night view |
| `japanese_ink` | Minimalist ink wash, Zen, stark |
| `terracotta` | Mediterranean, warm, earthy |
| `sunset` | Oranges & pinks, warm evening |
| `autumn` | Burnt oranges, reds, seasonal |
| `copper_patina` | Oxidized copper, industrial, unique |
| `monochrome_blue` | Monochromatic blue, calm, unified |
| `feature_based` | Default road hierarchy, clean |
| `gradient_roads` | Smooth shading, modern |
| `contrast_zones` | High contrast, dense urban |

## Feature Toggles
- **Nature Detail**: Use `--forests` for islands, parks, or rural areas to add lush green/woodland polygons.
- **Urban Texture**: Use `--buildings` for city centers to add dense building footprints.

## Personalization
- **Zoom level**: Use `--distance`. Smaller values (e.g., `2000`) zoom in on city centers. Larger values (e.g., `20000`-`50000`) are necessary for islands, parks, or large natural regions where the center point is sparse.

## Troubleshooting
- **Empty Map**: If the output contains text but no map data, it means no features were found in the requested radius.
    - **Action**: Increase the `--distance` (e.g., try `30000` or `50000`).
    - **Action**: Verify the coordinates found in the logs are correct for the intended area.
- **Custom Text**: Use `--name` to change the main title and `--country-label` for the subtitle.

## Agent Instructions

- **Understand Intent**: Map natural language vibes (e.g., "make it look like an old map") to the best theme (`warm_beige`).
- **Clarify if Needed**: If the user asks for a theme or style that isn't possible (e.g., "make it neon green"), explain the available options and suggest the closest match.
- **Personalization**: If the user mentions a specific neighborhood or zoom level, adjust `--distance`. For remote areas/islands (like Kauai), proactively suggest a larger distance (e.g. `30000`).
- **Validation**: If a generation fails or returns an empty map, apologize and suggest a larger `--distance` or a more specific city/country name.
- **Naming**: If the user says "Make a poster for NYC called 'Home'", use `--city "New York" --name "Home"`.
- **Output**: After generation, provide the link: `map-to-poster/output/...`.
