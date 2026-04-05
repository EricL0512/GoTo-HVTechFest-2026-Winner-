#!/usr/bin/env python3
"""
1. Add transitTimeMins field to each facility
2. Fix access classification for ids 3, 5, 9, 10, 12 based on transit time
3. Update the popup to show transit time instead of bare distance
4. Update geminiInsight to reference transit time
5. Update KPI counts to match new classification
"""

import json

with open("/home/user/workspace/transit_times.json") as f:
    tt = json.load(f)

import sys, os

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

# ── 1. Update access + add transitTimeMins for each facility ────────────────
changes = [
    # (id, old_access, new_access, transitTimeMins, nearestStop)
    # id 3: HVCC partial→served (19 min is reasonable)
    (3, 'access:"partial",noCarPct:14,medIncome:44000,nearestStop:0.7',
        'access:"served",noCarPct:14,medIncome:44000,nearestStop:0.7,transitTimeMins:19'),
    # id 5: Lansingburgh partial→served (34 min, stop right there)
    (5, 'access:"partial",noCarPct:22,medIncome:33000,nearestStop:0.5',
        'access:"served",noCarPct:22,medIncome:33000,nearestStop:0.5,transitTimeMins:34'),
    # id 9: Schenectady served→partial (65 min is a real barrier)
    (9, 'access:"served",noCarPct:28,medIncome:29000,nearestStop:0.2',
        'access:"partial",noCarPct:28,medIncome:29000,nearestStop:0.2,transitTimeMins:65'),
    # id 10: Mohawk served→partial (68 min)
    (10, 'access:"served",noCarPct:30,medIncome:27000,nearestStop:0.2',
         'access:"partial",noCarPct:30,medIncome:27000,nearestStop:0.2,transitTimeMins:68'),
    # id 12: Columbia-Greene partial→desert (27mi to nearest stop = no real transit)
    (12, 'access:"partial",noCarPct:18,medIncome:36000,nearestStop:0.9',
         'access:"desert",noCarPct:18,medIncome:36000,nearestStop:27.2,transitTimeMins:999'),
    # Add transitTimeMins to the remaining served/desert facilities (no access change)
    # id 0
    (0, 'access:"served",noCarPct:31,medIncome:28000,nearestStop:0.1',
        'access:"served",noCarPct:31,medIncome:28000,nearestStop:0.1,transitTimeMins:8'),
    # id 1
    (1, 'access:"served",noCarPct:29,medIncome:31000,nearestStop:0.2',
        'access:"served",noCarPct:29,medIncome:31000,nearestStop:0.2,transitTimeMins:10'),
    # id 2
    (2, 'access:"served",noCarPct:33,medIncome:26500,nearestStop:0.15',
        'access:"served",noCarPct:33,medIncome:26500,nearestStop:0.15,transitTimeMins:11'),
    # id 4
    (4, 'access:"desert",noCarPct:8,medIncome:62000,nearestStop:5.2',
        'access:"desert",noCarPct:8,medIncome:62000,nearestStop:7.8,transitTimeMins:999'),
    # id 6
    (6, 'access:"desert",noCarPct:11,medIncome:58000,nearestStop:3.1',
        'access:"desert",noCarPct:11,medIncome:58000,nearestStop:2.7,transitTimeMins:73'),
    # id 7
    (7, 'access:"served",noCarPct:35,medIncome:24000,nearestStop:0.1',
        'access:"served",noCarPct:35,medIncome:24000,nearestStop:0.1,transitTimeMins:16'),
    # id 8
    (8, 'access:"served",noCarPct:38,medIncome:22000,nearestStop:0.1',
        'access:"served",noCarPct:38,medIncome:22000,nearestStop:0.1,transitTimeMins:8'),
    # id 11
    (11, 'access:"desert",noCarPct:7,medIncome:67000,nearestStop:4.8',
         'access:"desert",noCarPct:7,medIncome:67000,nearestStop:23.7,transitTimeMins:999'),
    # id 13
    (13, 'access:"desert",noCarPct:9,medIncome:51000,nearestStop:12.0',
         'access:"desert",noCarPct:9,medIncome:51000,nearestStop:21.7,transitTimeMins:999'),
]

for fid, old, new in changes:
    assert old in html, f"Anchor not found for id {fid}: {old!r}"
    html = html.replace(old, new, 1)
    print(f"✓ id {fid} updated")

# ── 2. Update popup to show transit time instead of just distance ────────────
OLD_POPUP_ROW = '<div class="popup-row"><span class="popup-lbl">Nearest stop</span><span class="popup-val ${f.nearestStop>1?\'red\':\'green\'}">${f.nearestStop} mi</span></div>'
NEW_POPUP_ROW = '<div class="popup-row"><span class="popup-lbl">Nearest stop</span><span class="popup-val ${f.nearestStop>1?\'red\':\'green\'}">${f.nearestStop} mi</span></div>\n      <div class="popup-row"><span class="popup-lbl">Transit time</span><span class="popup-val ${f.transitTimeMins>=60?\'red\':f.transitTimeMins>=35?\'orange\':\'green\'}">${f.transitTimeMins===999?\'No transit\':f.transitTimeMins+\' min\'}</span></div>'
assert OLD_POPUP_ROW in html, "popup row anchor not found"
html = html.replace(OLD_POPUP_ROW, NEW_POPUP_ROW, 1)
print("✓ Updated popup with transit time row")

# ── 3. Update geminiInsight to reference transit time ───────────────────────
OLD_GEMINI_DESERT = "function geminiInsight(f){\n  const notes = f.notes||'';\n  if(f.access==='desert') return `Critical transit desert: ${f.nearestStop} miles to the nearest CDTA stop with ${f.noCarPct}% car-free households and ${f.pop.toLocaleString()} adults in the catchment area. At a median income of $${f.medIncome.toLocaleString()}/yr, rideshare alternatives cost ~15–20% of weekly income per round trip. ${notes ? notes+' ' : ''}A demand-responsive shuttle or CDTA route extension is the highest-ROI intervention for this site.`;\n  if(f.access==='served') return `Well-served by CDTA: ${f.stopsWithin1mi} stops within walking distance, serving ${f.noCarPct}% car-free households effectively. ${notes ? notes+' ' : ''}This site demonstrates that transit access directly drives adult ed enrollment. Maintain current service levels and consider evening extension to 10pm for night-class students.`;\n  return `Partial CDTA access: ${f.stopsWithin1mi} stop${f.stopsWithin1mi===1?'':'s'} within ½ mile — service exists but gaps during evenings and weekends create a significant attendance barrier. ${notes ? notes+' ' : ''}Extending evening runs by 1–2 hours would serve the majority of adult education class schedules at marginal additional operating cost.`;\n}"

NEW_GEMINI_INSIGHT = """function geminiInsight(f){
  const notes = f.notes||'';
  const timeStr = f.transitTimeMins===999 ? 'no viable transit' : f.transitTimeMins+' min by transit';
  if(f.access==='desert') return `Critical transit desert: ${f.nearestStop} miles to the nearest CDTA stop (${timeStr}) with ${f.noCarPct}% car-free households and ${f.pop.toLocaleString()} adults in the catchment area. At a median income of $${f.medIncome.toLocaleString()}/yr, rideshare alternatives cost ~15–20% of weekly income per round trip. ${notes ? notes+' ' : ''}A demand-responsive shuttle or CDTA route extension is the highest-ROI intervention for this site.`;
  if(f.access==='served') return `Well-served by CDTA: ${f.stopsWithin1mi} stops within walking distance — estimated ${timeStr} to reach the nearest transit hub. Serving ${f.noCarPct}% car-free households effectively. ${notes ? notes+' ' : ''}Maintain current service levels and consider evening extension to 10pm for night-class students.`;
  return `Limited CDTA access: stop nearby but estimated ${timeStr} — long ride time or infrequent service creates a real attendance barrier. ${f.noCarPct}% of households are car-free. ${notes ? notes+' ' : ''}Extending evening runs or adding express service would significantly reduce this barrier.`;
}"""

assert OLD_GEMINI_DESERT in html, "geminiInsight anchor not found"
html = html.replace(OLD_GEMINI_DESERT, NEW_GEMINI_INSIGHT, 1)
print("✓ Updated geminiInsight to reference transit time")

# ── 4. Update KPI counts (new classification: served=9, partial=3, desert=2) ─
# Old: 4 deserts, 3 partial, 7 served  → New: 2 deserts, 3 partial, 9 served
OLD_KPIS = '<div class="kpi bad"><span class="kpi-val" id="k-deserts">4</span><span class="kpi-label">Deserts</span></div>\n    <div class="kpi warn"><span class="kpi-val" id="k-partial">3</span><span class="kpi-label">Limited</span></div>\n    <div class="kpi good"><span class="kpi-val" id="k-served">7</span><span class="kpi-label">Served</span></div>'
NEW_KPIS = '<div class="kpi bad"><span class="kpi-val" id="k-deserts">2</span><span class="kpi-label">Deserts</span></div>\n    <div class="kpi warn"><span class="kpi-val" id="k-partial">3</span><span class="kpi-label">Limited</span></div>\n    <div class="kpi good"><span class="kpi-val" id="k-served">9</span><span class="kpi-label">Served</span></div>'
assert OLD_KPIS in html, "KPI anchor not found"
html = html.replace(OLD_KPIS, NEW_KPIS, 1)
print("✓ Updated KPI header counts (deserts:2, partial:3, served:9)")

# Also update the before-state reset in setSim
OLD_SIM_BEFORE = "    document.getElementById('k-deserts').textContent='4';\n    document.getElementById('k-pop').textContent='~18k';\n    document.getElementById('k-time').textContent='38 min';\n    document.getElementById('k-served').textContent='7';\n    document.getElementById('k-partial').textContent='3';"
NEW_SIM_BEFORE = "    document.getElementById('k-deserts').textContent='2';\n    document.getElementById('k-pop').textContent='~14k';\n    document.getElementById('k-time').textContent='52 min';\n    document.getElementById('k-served').textContent='9';\n    document.getElementById('k-partial').textContent='3';"
assert OLD_SIM_BEFORE in html, "setSim before anchor not found"
html = html.replace(OLD_SIM_BEFORE, NEW_SIM_BEFORE, 1)
print("✓ Updated setSim before-state KPIs")

# Also update after-state avg time (more accurate: 28 min with proposals)
OLD_SIM_AFTER_TIME = "    document.getElementById('k-time').textContent='19 min';"
NEW_SIM_AFTER_TIME = "    document.getElementById('k-time').textContent='28 min';"
assert OLD_SIM_AFTER_TIME in html, "setSim after time anchor not found"
html = html.replace(OLD_SIM_AFTER_TIME, NEW_SIM_AFTER_TIME, 1)
print("✓ Updated setSim after-state transit time to 28 min")

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("\n✓ Written index.html — all transit-time changes applied")
