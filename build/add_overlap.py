#!/usr/bin/env python3
"""
Add overlap awareness to route suggestions:
1. Tag each suggestion with overlap type in data
2. Add overlap penalty to score (-8 if overlaps, -3 if parallel)
3. Surface overlap status in popup and sidebar with clear label
"""

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

# ─────────────────────────────────────────────────────────────────────────────
# 1. Tag each suggestion with overlap metadata
#    overlap: "none" | "parallel" | "extension"
#    overlapNote: human-readable explanation
# ─────────────────────────────────────────────────────────────────────────────

replacements = [
    # s1 — clear new territory
    (
        'id:"s1",title:"North Greenbush → Troy EOC Shuttle",\n    type:"shuttle",priority:"critical",score:96,costKyr:90,',
        'id:"s1",title:"North Greenbush → Troy EOC Shuttle",\n    type:"shuttle",priority:"critical",score:96,costKyr:90,overlap:"none",overlapNote:"New corridor — Rt. 4 east of Troy has zero CDTA service. No duplication.",',
    ),
    # s2 — parallel / extension of rt85, short campus loop
    (
        'id:"s2",title:"HVCC Campus Link — Vandenburgh Ave Extension",\n    type:"bus",priority:"critical",score:92,costKyr:48,',
        'id:"s2",title:"HVCC Campus Link — Vandenburgh Ave Extension",\n    type:"bus",priority:"critical",score:92,costKyr:48,overlap:"extension",overlapRoute:"Route 85",overlapNote:"Extension of existing Rt. 85 — adds 3 on-campus stops not currently served. Short loop addition, not duplication.",',
    ),
    # s3 — clear new territory
    (
        'id:"s3",title:"Castleton-on-Hudson — Route 233 Extension",\n    type:"bus",priority:"critical",score:88,costKyr:55,',
        'id:"s3",title:"Castleton-on-Hudson — Route 233 Extension",\n    type:"bus",priority:"critical",score:88,costKyr:55,overlap:"none",overlapNote:"New corridor — Rt. 9J south of Schodack has no CDTA service. No duplication.",',
    ),
    # s4 — runs on existing rt370 corridor (evening hours only — service gap, not new route)
    (
        'id:"s4",title:"Route 370 Evening Extension — Troy to Schenectady",\n    type:"bus",priority:"high",score:81,costKyr:62,',
        'id:"s4",title:"Route 370 Evening Extension — Troy to Schenectady",\n    type:"bus",priority:"high",score:81,costKyr:62,overlap:"extension",overlapRoute:"Route 370",overlapNote:"Runs on existing Rt. 370 corridor — adds 2 evening trips (8pm & 9:30pm) where service currently ends at 7:15pm. Same road, new hours.",',
    ),
    # s5 — directly on rt85 corridor (weekend frequency boost, same stops)
    (
        'id:"s5",title:"Lansingburgh Weekend Boost — Route 85",\n    type:"stop",priority:"high",score:77,costKyr:38,',
        'id:"s5",title:"Lansingburgh Weekend Boost — Route 85",\n    type:"stop",priority:"high",score:77,costKyr:38,overlap:"frequency",overlapRoute:"Route 85",overlapNote:"Frequency boost on existing Rt. 85 — same stops, same corridor. Adds Saturday 30-min headways and Sunday AM service where none exists.",',
    ),
    # s6 — runs parallel to rt87 for most of its length (last 0.5mi is new)
    (
        'id:"s6",title:"Brunswick Ind. Park — Education-to-Employment Link",\n    type:"shuttle",priority:"medium",score:68,costKyr:44,',
        'id:"s6",title:"Brunswick Ind. Park — Education-to-Employment Link",\n    type:"shuttle",priority:"medium",score:68,costKyr:44,overlap:"parallel",overlapRoute:"Route 87",overlapNote:"Runs parallel to Rt. 87 along Hoosick St — the final 0.5mi to Brunswick Industrial Park is unserved new territory. Connector fills the last-mile gap Rt. 87 leaves.",',
    ),
    # s7 — completely new territory north of Schenectady
    (
        'id:"s7",title:"Saratoga South — Wilton Micro-Transit Pilot",\n    type:"shuttle",priority:"medium",score:61,costKyr:120,',
        'id:"s7",title:"Saratoga South — Wilton Micro-Transit Pilot",\n    type:"shuttle",priority:"medium",score:61,costKyr:120,overlap:"none",overlapNote:"New corridor — Saratoga County south of Saratoga Springs has zero fixed-route transit. No duplication.",',
    ),
]

for old, new in replacements:
    assert old in html, f"Anchor not found:\n{old!r}"
    html = html.replace(old, new, 1)

print("✓ Tagged all 7 suggestions with overlap metadata")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Add overlapPenalty to the score computation block
# ─────────────────────────────────────────────────────────────────────────────

OLD_SCORE_APPLY = """  // Final score
  s.baseScore=s.score;
  s.score=Math.min(100,s.baseScore+s.destBonus+s.effBonus);"""

NEW_SCORE_APPLY = """  // Overlap penalty: frequency/extension = -3, parallel = -6 (fills gap but duplicates corridor)
  // "none" overlaps get no penalty — they serve new territory
  s.overlapPenalty=s.overlap==='frequency'?-3:s.overlap==='extension'?-3:s.overlap==='parallel'?-6:0;

  // Final score
  s.baseScore=s.score;
  s.score=Math.min(100,Math.max(0,s.baseScore+s.destBonus+s.effBonus+s.overlapPenalty));"""

assert OLD_SCORE_APPLY in html, "Score apply anchor not found"
html = html.replace(OLD_SCORE_APPLY, NEW_SCORE_APPLY, 1)
print("✓ Added overlapPenalty to score computation")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Update buildSuggestPopup — add overlap status row + note
# ─────────────────────────────────────────────────────────────────────────────

OLD_POPUP_TYPE_ROW = """      <div class="popup-row"><span class="popup-lbl">Type</span><span class="popup-val">${s.type==='bus'?'New Bus Route':s.type==='shuttle'?'Demand-Responsive Shuttle':'New Stop Addition'}</span></div>"""

NEW_POPUP_TYPE_ROW = """      <div class="popup-row"><span class="popup-lbl">Type</span><span class="popup-val">${s.type==='bus'?'New Bus Route':s.type==='shuttle'?'Demand-Responsive Shuttle':'New Stop Addition'}</span></div>
      <div class="popup-row"><span class="popup-lbl">vs Existing</span><span class="popup-val ${s.overlap==='none'?'green':s.overlap==='frequency'?'orange':s.overlap==='extension'?'orange':'red'}">${s.overlap==='none'?'✅ New corridor':s.overlap==='frequency'?'🔁 Frequency boost — '+s.overlapRoute:s.overlap==='extension'?'➕ Extension — '+s.overlapRoute:'🟡 Parallel — '+s.overlapRoute}</span></div>"""

assert OLD_POPUP_TYPE_ROW in html, "Popup type row anchor not found"
html = html.replace(OLD_POPUP_TYPE_ROW, NEW_POPUP_TYPE_ROW, 1)
print("✓ Added overlap status row to popup")

# Add overlap note to popup score breakdown section
OLD_PENALTY_ROW = """  const bonusRow=(s.destBonus>0||s.effBonus>0)"""

NEW_PENALTY_ROW = """  const penaltyRow=s.overlapPenalty<0
    ? `<div class="popup-row"><span class="popup-lbl">Overlap penalty</span><span class="popup-val red">${s.overlapPenalty} pts</span></div>`
    : '';
  const bonusRow=(s.destBonus>0||s.effBonus>0)"""

assert OLD_PENALTY_ROW in html, "bonusRow declaration anchor not found"
html = html.replace(OLD_PENALTY_ROW, NEW_PENALTY_ROW, 1)
print("✓ Added penaltyRow variable")

# Insert penaltyRow into the breakdown section
OLD_BREAKDOWN = """      ${baseRow}
      ${bonusRow}
      ${nearbyHtml}"""

NEW_BREAKDOWN = """      ${baseRow}
      ${bonusRow}
      ${penaltyRow}
      ${nearbyHtml}"""

assert OLD_BREAKDOWN in html, "Breakdown anchor not found"
html = html.replace(OLD_BREAKDOWN, NEW_BREAKDOWN, 1)
print("✓ Inserted penaltyRow into popup breakdown")

# Add the overlap note below the popup body
OLD_DEST_SECTION = """  const destSection=s.nearbyDests&&s.nearbyDests.length>0"""

NEW_DEST_SECTION = """  const overlapSection=s.overlap!=='none'
    ? `<div class="popup-ai" style="background:rgba(218,113,1,0.06);border-left:3px solid #da7101;margin-top:6px;padding:8px 10px;font-size:0.82em;color:#7a4500"><strong>Note on Existing Service:</strong> ${s.overlapNote}</div>`
    : `<div class="popup-ai" style="background:rgba(67,122,34,0.06);border-left:3px solid #437a22;margin-top:6px;padding:8px 10px;font-size:0.82em;color:#2d5a14"><strong>New Territory:</strong> ${s.overlapNote}</div>`;
  const destSection=s.nearbyDests&&s.nearbyDests.length>0"""

assert OLD_DEST_SECTION in html, "destSection anchor not found"
html = html.replace(OLD_DEST_SECTION, NEW_DEST_SECTION, 1)
print("✓ Added overlapSection variable")

# Insert overlapSection into popup return
OLD_POPUP_RETURN = """    ${destSection}
  </div>`;
}"""

NEW_POPUP_RETURN = """    ${overlapSection}
    ${destSection}
  </div>`;
}"""

assert OLD_POPUP_RETURN in html, "Popup return anchor not found"
html = html.replace(OLD_POPUP_RETURN, NEW_POPUP_RETURN, 1)
print("✓ Inserted overlapSection into popup")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Update sidebar card — add overlap badge next to type pill
# ─────────────────────────────────────────────────────────────────────────────

OLD_TYPE_PILL = """        <div class="suggest-type ${s.type==='bus'?'type-bus':s.type==='shuttle'?'type-shuttle':'type-stop'}">${s.type==='bus'?'🚌 Bus Route':s.type==='shuttle'?'🚐 Shuttle':'🚏 New Stop'}</div>"""

NEW_TYPE_PILL = """        <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap">
          <div class="suggest-type ${s.type==='bus'?'type-bus':s.type==='shuttle'?'type-shuttle':'type-stop'}">${s.type==='bus'?'🚌 Bus Route':s.type==='shuttle'?'🚐 Shuttle':'🚏 New Stop'}</div>
          <div style="font-size:0.68em;padding:2px 5px;border-radius:3px;font-weight:600;background:${s.overlap==='none'?'#d4f0e4':s.overlap==='frequency'?'#fdebd5':s.overlap==='extension'?'#fdebd5':'#fde8cd'};color:${s.overlap==='none'?'#2d6e4e':s.overlap==='frequency'?'#7a4500':'#7a4500'}">${s.overlap==='none'?'✅ New Corridor':s.overlap==='frequency'?'🔁 Freq Boost':'➕ Extension'}</div>
        </div>"""

assert OLD_TYPE_PILL in html, "Sidebar type pill anchor not found"
html = html.replace(OLD_TYPE_PILL, NEW_TYPE_PILL, 1)
print("✓ Added overlap badge to sidebar type pill")

# ─────────────────────────────────────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────────────────────────────────────
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("✓ Written index.html — overlap awareness complete")
