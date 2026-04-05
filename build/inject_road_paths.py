#!/usr/bin/env python3
"""
Inject real OSRM road paths into index.html.
Strategy: add a roadPaths lookup object just before the aiSuggestions
rendering loop, then replace the straight-line polyline calls with
path lookups — falling back to straight line if a path is missing.
"""
import json, re, os, sys

# Load route_paths.json from same directory as this script
_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "route_paths.json")
with open(_json_path) as f:
    routes = json.load(f)


# Accept path as command-line argument or prompt if not provided
if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    default = os.path.join(os.path.dirname(__file__), "..", "app", "index.html")
    path = input(f"Path to index.html [{default}]: ").strip() or default
path = os.path.abspath(path)
print(f"Target: {path}")
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# ── 1. Build compact JS object with all paths ───────────────────────────
lines = ["// ── OSRM road-following paths (pre-fetched at build time) ──────────────"]
lines.append("const roadPaths = {")
for sid, data in sorted(routes.items()):
    # Reduce precision to 5 decimal places to keep file size manageable
    pts = [[round(lat,5), round(lng,5)] for lat,lng in data["path"]]
    pts_js = json.dumps(pts, separators=(',', ':'))
    lines.append(f"  {sid}: {pts_js},")
lines.append("};")
road_paths_js = "\n".join(lines) + "\n\n"

# ── 2. Insert roadPaths before the AI ROUTE SUGGESTIONS block ───────────
ANCHOR = "// ── AI ROUTE SUGGESTIONS ──────────────────────────────────────────"
assert ANCHOR in html, "AI ROUTE SUGGESTIONS anchor not found"
html = html.replace(ANCHOR, road_paths_js + ANCHOR, 1)
print("✓ Inserted roadPaths object")

# ── 3. Replace straight-line aiRoute polyline with road path ────────────
OLD_ROUTE_LINE = "  const routeLine=L.polyline([[s.lat,s.lng],[s.lat2,s.lng2]],{color:C.teal,weight:3,dashArray:'8 6',opacity:0.8}).addTo(layers.aiRoutes);"
NEW_ROUTE_LINE = "  const _path=roadPaths[s.id]||[[s.lat,s.lng],[s.lat2,s.lng2]];\n  const routeLine=L.polyline(_path,{color:C.teal,weight:3,dashArray:'8 6',opacity:0.8,smoothFactor:1}).addTo(layers.aiRoutes);"
assert OLD_ROUTE_LINE in html, "routeLine anchor not found"
html = html.replace(OLD_ROUTE_LINE, NEW_ROUTE_LINE, 1)
print("✓ Updated AI route polyline to use road path")

# ── 4. Replace straight-line simAfter polyline with road path ────────────
OLD_SIM_LINE = "  L.polyline([[s.lat,s.lng],[s.lat2,s.lng2]],{color:'#437a22',weight:4,opacity:0.9}).addTo(layers.simAfter);"
NEW_SIM_LINE = "  const _spath=roadPaths[s.id]||[[s.lat,s.lng],[s.lat2,s.lng2]];\n  L.polyline(_spath,{color:'#437a22',weight:4,opacity:0.9,smoothFactor:1}).addTo(layers.simAfter);"
assert OLD_SIM_LINE in html, "simAfter polyline anchor not found"
html = html.replace(OLD_SIM_LINE, NEW_SIM_LINE, 1)
print("✓ Updated before/after simulation polyline to use road path")

with open(path, "w", encoding="utf-8") as f:
    f.write(html)

# Report file size
import os
size_kb = os.path.getsize(path) // 1024
print(f"✓ Written index.html — {size_kb}KB")

# Verify all 7 IDs are present
for sid in ["s1","s2","s3","s4","s5","s6","s7"]:
    status = "✓" if sid in routes else "✗ MISSING"
    pts = routes.get(sid, {}).get("pts", 0)
    dist = routes.get(sid, {}).get("dist_mi", "?")
    print(f"  {status} {sid}: {pts} pts, {dist} mi")
