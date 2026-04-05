# GoTo — Government Optimized Transport Operations

> 🏆 **Winner** — HV Open Data Hackathon 2026 · RPI Troy, NY · Built in a single day

**[🗺️ Live Demo](https://ericl0512.github.io/GoTo-Transit-Planner/app/)** · **[📊 Presentation](https://ericl0512.github.io/GoTo-Transit-Planner/presentation/)**

---

## What is GoTo?

Transportation deserts disproportionately affect low-income and vulnerable communities — cutting off access to critical services such as hospitals, child healthcare, adult education, and social support programs — yet government planners have no unified, data-driven tool to identify these gaps, model targeted solutions, and prioritize route investments based on equity, health outcomes, and social impact.

**GoTo is that tool.**

It's an interactive GIS platform that:
- Maps transit deserts across the Capital District using **real transit travel time** (walk + wait + ride), not just distance to the nearest stop
- Overlays equity data — car-free household rates, median income, and destination access — as a heatmap
- Scores 7 proposed new routes using a multi-factor AI engine (need, cost efficiency, destination proximity, and network overlap)
- Simulates the **before/after impact** of implementing top proposals with live KPI toggles
- Provides plain-language analysis per facility powered by the **Gemini API** (in progress)

The entire app is a single `index.html` file. No backend, no install, no dependencies — open it in any browser.

---

## Built with Perplexity Computer

GoTo was designed, researched, coded, and deployed entirely using **[Perplexity Computer](https://www.perplexity.ai/computer)** — an AI-powered development environment that combines web search, data analysis, code generation, and live deployment in one place.

Every part of the stack was produced in a single hackathon session:

- **Data research** — CDTA route schedules, Census ACS queries, NYSED facility locations, and OSRM road geometry were all found, validated, and processed through Perplexity Computer
- **Transit-time classification** — a Python pipeline that computes walk + wait + ride time for 14 facilities using real CDTA headways and speeds was written and debugged in real time
- **Scoring engine** — the multi-factor route scoring model (haversine distance, cost efficiency, destination proximity, overlap detection) was designed and implemented iteratively
- **GIS map** — Leaflet.js integration with real CDTA polylines, 51 bus stops, equity heatmap, and road-following proposed route geometry
- **This presentation** — the hackathon slides were also built as a dynamic HTML presentation within the same session

> Using Perplexity Computer, a fully working data-rich GIS platform was produced from scratch in one day — a direct demonstration of what AI-assisted development enables.

---

## Features

| Feature | Description |
|---------|-------------|
| 🗺️ Interactive GIS map | Leaflet.js map with real CDTA routes, stops, and proposed corridors |
| ⏱️ Transit-time deserts | Access classified by walk + wait + ride time, not just distance |
| 🔥 Equity heatmap | Car-free % and income overlaid as a visual heat layer |
| 🤖 AI route scoring | Multi-factor scoring: need, cost, destinations, overlap |
| 🏥 Destination proximity | Hospitals, schools, and jobs within 2mi boost route scores |
| 📍 Real road geometry | Proposed routes follow actual streets via OSRM |
| 📊 Before/After simulation | Toggle proposals on/off, watch KPIs update live |
| 💬 Gemini analysis panel | Plain-language insight per facility (Gemini API in progress) |

---

## The Problem, Quantified

- **~14,000 adults** in the Capital District face 45+ min transit journeys to their nearest adult education site
- **52 min** average transit travel time for underserved residents — vs. 12 min by car
- **2 confirmed desert zones** where no viable transit journey exists at all
- Schenectady sites were previously marked "served" by every existing tool — GoTo's transit-time model revealed a **hidden 65-min barrier** invisible to distance-based analysis

---

## Repo Structure

```
GoTo-Transit-Planner/
├── index.html                  ← redirects to app/
├── README.md                   ← you are here
├── app/
│   └── index.html              ← the full app (open this in any browser)
├── presentation/
│   └── index.html              ← hackathon slides (open in any browser)
└── build/
    ├── README.md               ← pipeline documentation
    ├── run_all.py              ← run the full pipeline with one command
    ├── reroute_suggestions.py
    ├── add_dest_scoring.py
    ├── add_cost_distance.py
    ├── add_overlap.py
    ├── inject_road_paths.py
    ├── inject_transit_times.py
    └── route_paths.json        ← cached OSRM road geometry
```

**To run the app:** open `app/index.html` in any browser. That's it.

**To re-run the data pipeline:** see [`build/README.md`](build/README.md).

---

## Data Sources

| Dataset | Source | Used for |
|---------|--------|----------|
| CDTA Route Schedules | [cdta.org/schedules](https://www.cdta.org/schedules) | Stop locations, headways, route polylines |
| Census ACS 5-Year | [census.gov](https://data.census.gov) | Car-free household %, median income |
| NYSED Facility Directory | [nysed.gov](https://www.nysed.gov) | Adult education facility locations |
| OpenStreetMap via OSRM | [router.project-osrm.org](https://router.project-osrm.org) | Road-following route geometry |
| Capital District EOC | [cdeocc.org](https://www.cdeocc.org) | Facility validation and context |

---

## Team

**GoTo** was built by:

- **Eric Lin**
- **Matthew Lin**
- **Zachary Lin**
- **Weihao Wu**

HV Open Data Hackathon 2026 · Room 308, DCC · Rensselaer Polytechnic Institute · Troy, NY

---

## Future Plans

1. **Live Gemini API** — real-time contextual insights per facility and route (architecture already in place)
2. **Foot traffic data** — direct route proposals to corridors where demand already exists
3. **Travel-time heatmap** — replace the distance overlay with actual transit travel time per location
4. **Statewide & national expansion** — the scoring model is geography-agnostic; any GTFS feed + Census ACS data powers a GoTo deployment anywhere in the US
