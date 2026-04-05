# Build Scripts

These scripts were used to progressively enrich `app/index.html` with real computed data during development. They are not required to run the app — `app/index.html` is the complete, fully built output and works on its own.

---

## What the build pipeline does

The app's HTML file starts as a base template with placeholder data. Each script reads the file, makes targeted modifications, and writes it back. Running all six in order would reproduce the final deployed app from scratch.

> **Note:** The original template is not included in this repo. `app/index.html` is the final output after all scripts have been applied.

---

## Scripts — run in this order

### 1. `reroute_suggestions.py`
Replaces the default AI route suggestions with 7 geographically diverse proposals across the Capital District — North Greenbush, Castleton-on-Hudson, Schenectady→SUNY Albany, Albany EOC→Samaritan Hospital, Brunswick Industrial Park, and the Wilton→GlobalFoundries corridor. Each route has unique start and end points with no shared endpoints.

### 2. `add_dest_scoring.py`
Adds destination proximity scoring to the route engine. Inserts a `haversineMi()` distance function and a `computeDestBonus()` function that checks each proposed route's midpoint against 14 destination points (hospitals, schools, employment centers). Routes within 2 miles of a destination receive bonus points: +8 for hospitals, +6 for schools/colleges, +10 for employment centers, capped at +20 total.

### 3. `add_cost_distance.py`
Adds cost efficiency scoring. Each route gets an estimated annual operating cost (`costKyr`) and a computed straight-line length (`routeMi`). Cost per mile is calculated and used to assign an efficiency bonus: ≤$15K/mi → +8pts, ≤$25K/mi → +5pts, ≤$40K/mi → +2pts.

### 4. `add_overlap.py`
Analyzes each proposed route against the existing CDTA network and tags it as one of: `none` (new corridor), `extension` (extends an existing route), `frequency` (adds runs to an existing route), or `parallel` (runs alongside an existing route). Applies a score penalty accordingly: -3 for extensions/frequency boosts, -6 for parallel corridors. Displays the overlap status in popups and sidebar cards.

### 5. `inject_road_paths.py`
Calls the [OSRM public routing API](https://router.project-osrm.org) once per proposed route to fetch real road-following geometry (200–740 coordinate points per route). Hardcodes the results as a `roadPaths` object directly in the HTML so routes trace actual streets rather than straight lines. Results are also saved to `route_paths.json` as a cache — so if you re-run the script, it will re-fetch fresh geometry from OSRM and overwrite the cache.

> **Requires internet access** to call the OSRM API. If OSRM is unreachable, the script falls back gracefully and routes remain as straight lines.

### `route_paths.json`
The cached output of `inject_road_paths.py` — contains the pre-fetched OSRM road geometry for all 7 proposed routes as arrays of `[lat, lng]` coordinate pairs. Included in the repo so the geometry is available for reference even without re-running the script. Keys are `s1` through `s7`, each with a `path` array, point count (`pts`), and road distance in miles (`dist_mi`).

### 6. `inject_transit_times.py`
Computes transit access times for all 14 adult education facilities using real CDTA route data. For each facility, calculates: walk time to nearest stop (at 20 min/mile), average wait time (half the route headway), and ride time to the nearest hub (distance ÷ average route speed). Reclassifies each facility's access status (`served` / `partial` / `desert`) based on total transit time rather than raw distance, and adds a `transitTimeMins` field to each facility object.

---

## How to run

**Run all scripts in sequence:**
```bash
python run_all.py path/to/app/index.html
```

**Or run individually:**
```bash
python reroute_suggestions.py path/to/app/index.html
python add_dest_scoring.py path/to/app/index.html
python add_cost_distance.py path/to/app/index.html
python add_overlap.py path/to/app/index.html
python inject_road_paths.py path/to/app/index.html
python inject_transit_times.py path/to/app/index.html
```

If no path is provided, each script will prompt you and default to `../app/index.html` relative to the script's location.

---

## Requirements

- Python 3.7+
- No external packages — only standard library (`json`, `urllib`, `re`, `os`, `sys`)
- Internet connection required for `inject_road_paths.py` only

---

## Data sources used by these scripts

| Data | Source |
|------|--------|
| CDTA route stops & headways | [CDTA published schedules](https://www.cdta.org/) |
| Adult ed facility locations | [NYSED facility directory](https://www.nysed.gov) |
| Road geometry | [OSRM public API](https://project-osrm.org/) via OpenStreetMap |
| Destination locations (hospitals, schools, jobs) | Manually geocoded from public records |
