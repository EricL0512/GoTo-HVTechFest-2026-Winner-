#!/usr/bin/env python3
"""
Inject destination proximity scoring into hv-access-map/index.html.
All changes are made via string replacement on exact anchors.
"""
import re

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
# 1. Insert haversine + computeDestBonus + score computation
#    ANCHOR: the comment "// ── AI ROUTE SUGGESTIONS"
# ─────────────────────────────────────────────────────────────────────────────
DEST_SCORING_JS = """
// ── DESTINATION PROXIMITY SCORING ────────────────────────────────────────────
function haversineMi(lat1,lng1,lat2,lng2){
  const R=3958.8,r=Math.PI/180;
  const dLat=(lat2-lat1)*r, dLng=(lng2-lng1)*r;
  const a=Math.sin(dLat/2)**2+Math.cos(lat1*r)*Math.cos(lat2*r)*Math.sin(dLng/2)**2;
  return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}

// Weight config — how many pts each destination type adds per route (if within radius)
const DEST_WEIGHTS={hospital:{pts:8,radiusMi:2},school:{pts:6,radiusMi:2},jobs:{pts:10,radiusMi:2}};
const DEST_BONUS_CAP=20;

function computeDestBonus(s){
  // Use route midpoint for distance calculation
  const midLat=(s.lat+s.lat2)/2, midLng=(s.lng+s.lng2)/2;
  let bonus=0;
  const nearby=[];
  destinations.forEach(d=>{
    const dist=haversineMi(midLat,midLng,d.lat,d.lng);
    const cfg=DEST_WEIGHTS[d.type];
    if(cfg && dist<=cfg.radiusMi){
      bonus+=cfg.pts;
      nearby.push({name:d.name,icon:d.icon,type:d.type,dist:dist.toFixed(1)});
    }
  });
  return {bonus:Math.min(bonus,DEST_BONUS_CAP),nearby};
}

// Apply destination bonuses to all suggestions
aiSuggestions.forEach(s=>{
  const {bonus,nearby}=computeDestBonus(s);
  s.baseScore=s.score;
  s.destBonus=bonus;
  s.score=Math.min(100,s.baseScore+bonus);
  s.nearbyDests=nearby;
});

"""

ANCHOR = "// ── AI Route Suggestions — Troy/Capital District focused ─────────────────"
assert ANCHOR in html, f"Anchor not found: {ANCHOR!r}"
html = html.replace(ANCHOR, DEST_SCORING_JS + ANCHOR)
print("✓ Inserted haversine + computeDestBonus + score application")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Update buildSuggestPopup to show score breakdown + nearby destinations
# ─────────────────────────────────────────────────────────────────────────────
OLD_POPUP = """function buildSuggestPopup(s){
  const scoreColor=s.priority==='critical'?'#a13544':s.priority==='high'?'#da7101':'#01696f';
  return `<div>
    <div class="popup-head suggest">AI ROUTE SUGGESTION · SCORE ${s.score}/100</div>
    <div class="popup-body">
      <div class="popup-title">${s.title}</div>
      <div class="popup-row"><span class="popup-lbl">Type</span><span class="popup-val">${s.type==='bus'?'New Bus Route':s.type==='shuttle'?'Demand-Responsive Shuttle':'New Stop Addition'}</span></div>
      <div class="popup-row"><span class="popup-lbl">Priority</span><span class="popup-val ${s.priority==='critical'?'red':s.priority==='high'?'orange':'green'}">${s.priority.toUpperCase()}</span></div>
      <div class="popup-row"><span class="popup-lbl">Population served</span><span class="popup-val">${s.pop.toLocaleString()}</span></div>
      <div class="popup-row"><span class="popup-lbl">Car-free households</span><span class="popup-val">${s.carFree}%</span></div>
    </div>
    <div class="popup-ai"><div class="popup-ai-lbl">AI Recommendation</div>${s.body}</div>
  </div>`;
}"""

NEW_POPUP = """function buildSuggestPopup(s){
  const scoreColor=s.priority==='critical'?'#a13544':s.priority==='high'?'#da7101':'#01696f';
  const bonusRow=s.destBonus>0
    ? `<div class="popup-row"><span class="popup-lbl">Dest. bonus</span><span class="popup-val green">+${s.destBonus} pts</span></div>`
    : `<div class="popup-row"><span class="popup-lbl">Dest. bonus</span><span class="popup-val" style="color:#888">+0 pts</span></div>`;
  const baseRow=s.baseScore!==undefined
    ? `<div class="popup-row"><span class="popup-lbl">Base score</span><span class="popup-val">${s.baseScore}/100</span></div>`
    : '';
  const nearbyHtml=s.nearbyDests&&s.nearbyDests.length>0
    ? `<div class="popup-row" style="align-items:flex-start"><span class="popup-lbl">Serves</span><span class="popup-val" style="line-height:1.6">${s.nearbyDests.map(d=>`${d.icon} ${d.name} <span style="color:#888;font-size:0.75em">(${d.dist}mi)</span>`).join('<br>')}</span></div>`
    : '';
  const destSection=s.nearbyDests&&s.nearbyDests.length>0
    ? `<div class="popup-ai" style="background:rgba(1,105,111,0.06);border-left:3px solid #01696f;margin-top:6px;padding:8px 10px;font-size:0.82em;color:#2c555a"><strong>Multi-Purpose Corridor:</strong> This route serves ${s.nearbyDests.map(d=>d.name).join(', ')} — amplifying its impact beyond adult education access.</div>`
    : '';
  return `<div>
    <div class="popup-head suggest">AI ROUTE SUGGESTION · SCORE ${s.score}/100</div>
    <div class="popup-body">
      <div class="popup-title">${s.title}</div>
      <div class="popup-row"><span class="popup-lbl">Type</span><span class="popup-val">${s.type==='bus'?'New Bus Route':s.type==='shuttle'?'Demand-Responsive Shuttle':'New Stop Addition'}</span></div>
      <div class="popup-row"><span class="popup-lbl">Priority</span><span class="popup-val ${s.priority==='critical'?'red':s.priority==='high'?'orange':'green'}">${s.priority.toUpperCase()}</span></div>
      <div class="popup-row"><span class="popup-lbl">Population served</span><span class="popup-val">${s.pop.toLocaleString()}</span></div>
      <div class="popup-row"><span class="popup-lbl">Car-free households</span><span class="popup-val">${s.carFree}%</span></div>
      <hr style="border:none;border-top:1px solid #eee;margin:4px 0">
      ${baseRow}
      ${bonusRow}
      ${nearbyHtml}
    </div>
    <div class="popup-ai"><div class="popup-ai-lbl">AI Recommendation</div>${s.body}</div>
    ${destSection}
  </div>`;
}"""

assert OLD_POPUP in html, "buildSuggestPopup anchor not found"
html = html.replace(OLD_POPUP, NEW_POPUP)
print("✓ Updated buildSuggestPopup with score breakdown + nearby destinations")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Update sidebar AI card — show destination icons + updated score pill
# ─────────────────────────────────────────────────────────────────────────────
OLD_SIDEBAR = """  el.innerHTML=`
    <div class="suggest-header">
      <div>
        <div class="suggest-type ${s.type==='bus'?'type-bus':s.type==='shuttle'?'type-shuttle':'type-stop'}">${s.type==='bus'?'🚌 Bus Route':s.type==='shuttle'?'🚐 Shuttle':'🚏 New Stop'}</div>
        <div class="suggest-title">${s.title}</div>
      </div>
      <div class="suggest-score ${s.priority==='critical'?'score-critical':s.priority==='high'?'score-high':'score-medium'}">Score ${s.score}</div>
    </div>
    <div class="suggest-body">${s.body.substring(0,180)}...</div>
    <div class="suggest-tags">${s.tags.map(t=>`<span class="suggest-tag">${t}</span>`).join('')}</div>`;"""

NEW_SIDEBAR = """  const destIconsHtml=s.nearbyDests&&s.nearbyDests.length>0
    ? `<span style="margin-left:5px;font-size:0.85em;letter-spacing:1px" title="Serves nearby destinations">${[...new Set(s.nearbyDests.map(d=>d.icon))].join('')}</span>`
    : '';
  const bonusBadge=s.destBonus>0
    ? `<span style="font-size:0.68em;background:#d4f0ed;color:#01696f;border-radius:3px;padding:1px 4px;margin-left:3px;font-weight:600" title="Destination proximity bonus">+${s.destBonus}</span>`
    : '';
  el.innerHTML=`
    <div class="suggest-header">
      <div>
        <div class="suggest-type ${s.type==='bus'?'type-bus':s.type==='shuttle'?'type-shuttle':'type-stop'}">${s.type==='bus'?'🚌 Bus Route':s.type==='shuttle'?'🚐 Shuttle':'🚏 New Stop'}</div>
        <div class="suggest-title">${s.title}</div>
      </div>
      <div class="suggest-score ${s.priority==='critical'?'score-critical':s.priority==='high'?'score-high':'score-medium'}">Score ${s.score}${bonusBadge}${destIconsHtml}</div>
    </div>
    <div class="suggest-body">${s.body.substring(0,180)}...</div>
    <div class="suggest-tags">${s.tags.map(t=>`<span class="suggest-tag">${t}</span>`).join('')}</div>`;"""

assert OLD_SIDEBAR in html, "Sidebar innerHTML anchor not found"
html = html.replace(OLD_SIDEBAR, NEW_SIDEBAR)
print("✓ Updated sidebar card with destination icons and bonus badge")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Update the Gemini showInsight call to mention nearby destinations
# ─────────────────────────────────────────────────────────────────────────────
OLD_INSIGHT_CALL = "    showInsight(s.title,'AI Recommendation: '+s.body);"

NEW_INSIGHT_CALL = """    const destAppend=s.nearbyDests&&s.nearbyDests.length>0
      ? ' This route also serves '+s.nearbyDests.map(d=>d.name).join(', ')+' — making it a multi-purpose corridor with amplified community impact.'
      : '';
    showInsight(s.title,'AI Recommendation: '+s.body+destAppend);"""

# There are two occurrences (marker click + sidebar click) — replace both
count = html.count(OLD_INSIGHT_CALL)
assert count == 2, f"Expected 2 occurrences, found {count}"
html = html.replace(OLD_INSIGHT_CALL, NEW_INSIGHT_CALL)
print(f"✓ Updated {count} showInsight calls with nearby destinations context")

# ─────────────────────────────────────────────────────────────────────────────
# Write out
# ─────────────────────────────────────────────────────────────────────────────
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("✓ Written index.html — all changes applied successfully")
