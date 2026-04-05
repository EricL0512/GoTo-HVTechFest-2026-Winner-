#!/usr/bin/env python3
"""
Add cost + route-length scoring to aiSuggestions.
1. Add costKyr (annual cost $K) and routeMi (computed from endpoints) to each suggestion
2. Extend computeDestBonus → computeScore to include efficiency penalty (cost/mile)
3. Update popup and sidebar to show cost, route length, and efficiency
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
# 1. Add costKyr to each suggestion (extracted from their existing tags/body text)
# ─────────────────────────────────────────────────────────────────────────────

# s1: ~$90K/yr
old_s1 = '    id:"s1",title:"North Greenbush → Troy EOC Shuttle",\n    type:"shuttle",priority:"critical",score:96,'
new_s1 = '    id:"s1",title:"North Greenbush → Troy EOC Shuttle",\n    type:"shuttle",priority:"critical",score:96,costKyr:90,'
assert old_s1 in html
html = html.replace(old_s1, new_s1, 1)

# s2: HVCC loop extension — est ~$48K/yr (short loop, campus partnership)
old_s2 = '    id:"s2",title:"HVCC Campus Link — Vandenburgh Ave Extension",\n    type:"bus",priority:"critical",score:92,'
new_s2 = '    id:"s2",title:"HVCC Campus Link — Vandenburgh Ave Extension",\n    type:"bus",priority:"critical",score:92,costKyr:48,'
assert old_s2 in html
html = html.replace(old_s2, new_s2, 1)

# s3: ~$55K/yr marginal
old_s3 = '    id:"s3",title:"Castleton-on-Hudson — Route 233 Extension",\n    type:"bus",priority:"critical",score:88,'
new_s3 = '    id:"s3",title:"Castleton-on-Hudson — Route 233 Extension",\n    type:"bus",priority:"critical",score:88,costKyr:55,'
assert old_s3 in html
html = html.replace(old_s3, new_s3, 1)

# s4: ~$62K/yr
old_s4 = '    id:"s4",title:"Route 370 Evening Extension — Troy to Schenectady",\n    type:"bus",priority:"high",score:81,'
new_s4 = '    id:"s4",title:"Route 370 Evening Extension — Troy to Schenectady",\n    type:"bus",priority:"high",score:81,costKyr:62,'
assert old_s4 in html
html = html.replace(old_s4, new_s4, 1)

# s5: ~$38K/yr
old_s5 = '    id:"s5",title:"Lansingburgh Weekend Boost — Route 85",\n    type:"stop",priority:"high",score:77,'
new_s5 = '    id:"s5",title:"Lansingburgh Weekend Boost — Route 85",\n    type:"stop",priority:"high",score:77,costKyr:38,'
assert old_s5 in html
html = html.replace(old_s5, new_s5, 1)

# s6: est ~$44K/yr (3x daily short shuttle)
old_s6 = '    id:"s6",title:"Brunswick Ind. Park — Education-to-Employment Link",\n    type:"shuttle",priority:"medium",score:68,'
new_s6 = '    id:"s6",title:"Brunswick Ind. Park — Education-to-Employment Link",\n    type:"shuttle",priority:"medium",score:68,costKyr:44,'
assert old_s6 in html
html = html.replace(old_s6, new_s6, 1)

# s7: est ~$120K/yr (long-distance on-demand pilot)
old_s7 = '    id:"s7",title:"Saratoga South — Wilton Micro-Transit Pilot",\n    type:"shuttle",priority:"medium",score:61,'
new_s7 = '    id:"s7",title:"Saratoga South — Wilton Micro-Transit Pilot",\n    type:"shuttle",priority:"medium",score:61,costKyr:120,'
assert old_s7 in html
html = html.replace(old_s7, new_s7, 1)

print("✓ Added costKyr to all 7 suggestions")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Replace the apply-bonus block with a new computeScore that also adds
#    route-length and cost-efficiency factors
#
#    Logic:
#      routeMi  = haversineMi(lat, lng, lat2, lng2)   ← straight-line length
#      effScore = costKyr / routeMi  → cost per mile (lower = better)
#      effBonus: ≤$15K/mi → +8, ≤$25K/mi → +5, ≤$40K/mi → +2, else 0
#      (keeps numbers modest and transparent)
# ─────────────────────────────────────────────────────────────────────────────

OLD_APPLY = """// Apply destination bonuses to all suggestions (must run after aiSuggestions is declared)
aiSuggestions.forEach(s=>{
  const {bonus,nearby}=computeDestBonus(s);
  s.baseScore=s.score;
  s.destBonus=bonus;
  s.score=Math.min(100,s.baseScore+bonus);
  s.nearbyDests=nearby;
});"""

NEW_APPLY = """// Apply destination + cost/distance bonuses (must run after aiSuggestions is declared)
aiSuggestions.forEach(s=>{
  // Route length (straight-line between endpoints)
  s.routeMi=Math.round(haversineMi(s.lat,s.lng,s.lat2,s.lng2)*10)/10;

  // Cost efficiency: annual cost per route-mile
  s.costPerMi=s.costKyr && s.routeMi>0 ? Math.round((s.costKyr/s.routeMi)*10)/10 : null;

  // Efficiency bonus: cheaper per mile = higher score
  let effBonus=0;
  if(s.costPerMi!==null){
    if(s.costPerMi<=15)      effBonus=8;
    else if(s.costPerMi<=25) effBonus=5;
    else if(s.costPerMi<=40) effBonus=2;
  }
  s.effBonus=effBonus;

  // Destination proximity bonus
  const {bonus:destBonus,nearby}=computeDestBonus(s);
  s.destBonus=destBonus;
  s.nearbyDests=nearby;

  // Final score
  s.baseScore=s.score;
  s.score=Math.min(100,s.baseScore+s.destBonus+s.effBonus);
});"""

assert OLD_APPLY in html, "Apply block anchor not found"
html = html.replace(OLD_APPLY, NEW_APPLY, 1)
print("✓ Replaced apply block with cost/distance + dest scoring")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Update buildSuggestPopup — add route length, cost, efficiency rows
#    and update score breakdown
# ─────────────────────────────────────────────────────────────────────────────

OLD_POPUP_ROWS = """      <div class="popup-row"><span class="popup-lbl">Population served</span><span class="popup-val">${s.pop.toLocaleString()}</span></div>
      <div class="popup-row"><span class="popup-lbl">Car-free households</span><span class="popup-val">${s.carFree}%</span></div>
      <hr style="border:none;border-top:1px solid #eee;margin:4px 0">
      ${baseRow}
      ${bonusRow}
      ${nearbyHtml}"""

NEW_POPUP_ROWS = """      <div class="popup-row"><span class="popup-lbl">Population served</span><span class="popup-val">${s.pop.toLocaleString()}</span></div>
      <div class="popup-row"><span class="popup-lbl">Car-free households</span><span class="popup-val">${s.carFree}%</span></div>
      <div class="popup-row"><span class="popup-lbl">Route length</span><span class="popup-val">${s.routeMi} mi</span></div>
      ${s.costKyr?`<div class="popup-row"><span class="popup-lbl">Est. annual cost</span><span class="popup-val">$${s.costKyr}K/yr</span></div>`:''}
      ${s.costPerMi!==null?`<div class="popup-row"><span class="popup-lbl">Cost efficiency</span><span class="popup-val ${s.costPerMi<=15?'green':s.costPerMi<=25?'orange':'red'}">$${s.costPerMi}K/mi · ${s.effBonus>0?'+'+s.effBonus+' pts':'no bonus'}</span></div>`:''}
      <hr style="border:none;border-top:1px solid #eee;margin:4px 0">
      ${baseRow}
      ${bonusRow}
      ${nearbyHtml}"""

assert OLD_POPUP_ROWS in html, "Popup rows anchor not found"
html = html.replace(OLD_POPUP_ROWS, NEW_POPUP_ROWS, 1)
print("✓ Updated buildSuggestPopup with route length + cost rows")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Update the dest bonus row label and add eff bonus row to popup breakdown
# ─────────────────────────────────────────────────────────────────────────────

OLD_BONUS_ROW = """  const bonusRow=s.destBonus>0
    ? `<div class="popup-row"><span class="popup-lbl">Dest. bonus</span><span class="popup-val green">+${s.destBonus} pts</span></div>`
    : `<div class="popup-row"><span class="popup-lbl">Dest. bonus</span><span class="popup-val" style="color:#888">+0 pts</span></div>`;"""

NEW_BONUS_ROW = """  const bonusRow=(s.destBonus>0||s.effBonus>0)
    ? `<div class="popup-row"><span class="popup-lbl">Dest. bonus</span><span class="popup-val green">+${s.destBonus} pts</span></div>
       <div class="popup-row"><span class="popup-lbl">Efficiency bonus</span><span class="popup-val ${s.effBonus>0?'green':''}">+${s.effBonus} pts</span></div>`
    : `<div class="popup-row"><span class="popup-lbl">Dest. bonus</span><span class="popup-val" style="color:#888">+0 pts</span></div>
       <div class="popup-row"><span class="popup-lbl">Efficiency bonus</span><span class="popup-val" style="color:#888">+0 pts</span></div>`;"""

assert OLD_BONUS_ROW in html, "bonusRow anchor not found"
html = html.replace(OLD_BONUS_ROW, NEW_BONUS_ROW, 1)
print("✓ Added efficiency bonus row to popup breakdown")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Update sidebar card: add cost + length as small meta line
# ─────────────────────────────────────────────────────────────────────────────

OLD_SIDEBAR_BODY = """    <div class="suggest-body">${s.body.substring(0,180)}...</div>
    <div class="suggest-tags">${s.tags.map(t=>`<span class="suggest-tag">${t}</span>`).join('')}</div>`;"""

NEW_SIDEBAR_BODY = """    <div class="suggest-meta" style="font-size:0.74em;color:#666;margin:3px 0 4px;display:flex;gap:10px">
      <span>📏 ${s.routeMi} mi</span>
      ${s.costKyr?`<span>💰 $${s.costKyr}K/yr</span>`:''}
      ${s.costPerMi!==null?`<span style="color:${s.costPerMi<=15?'#437a22':s.costPerMi<=25?'#da7101':'#a13544'}">$${s.costPerMi}K/mi</span>`:''}
    </div>
    <div class="suggest-body">${s.body.substring(0,180)}...</div>
    <div class="suggest-tags">${s.tags.map(t=>`<span class="suggest-tag">${t}</span>`).join('')}</div>`;"""

assert OLD_SIDEBAR_BODY in html, "Sidebar body anchor not found"
html = html.replace(OLD_SIDEBAR_BODY, NEW_SIDEBAR_BODY, 1)
print("✓ Added cost/length meta line to sidebar cards")

# ─────────────────────────────────────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────────────────────────────────────
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("✓ Written index.html — all cost/distance scoring changes applied")
