"""Known-item recall check: agrivoltaic-titled works cited by related reviews, retrieved or not by our searches."""
import json, re, time, urllib.request, urllib.parse, os
REVIEWS = {"Zainali2025": "10.1016/j.apenergy.2025.125558", "DiDomenico2026": "10.1016/j.atech.2026.102121", "Pillai2026": "10.1016/j.rser.2026.117056",
           "Qiao2026": "10.3390/su18178849", "Monasterio2026": "10.3390/en19061554", "Campana2025": "10.1038/s44359-025-00110-9",
           "Mamun2022": "10.1016/j.rser.2022.112351", "Cosme2025": "10.3390/agronomy15122829"}
AVRE = re.compile(r"agri-?voltaic|agri-?photovoltaic|agro-?photovoltaic|agro-?voltaic|agrivoltaism|agri-?pv\b|agripv|solar sharing|photovoltaic greenhouse|pv greenhouse|solar grazing|agrisolar|dual-use solar|dual use solar", re.I)
cache_p = "crossref_meta_cache.json"
cache = json.load(open(cache_p, encoding="utf-8")) if os.path.exists(cache_p) else {}
def cr(doi):
    d = doi.lower()
    if d in cache: return cache[d]
    for i in range(4):
        try:
            m = json.load(urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(d), headers={"User-Agent": "review-reference-check"}), timeout=40))["message"]
            cache[d] = {"title": (m.get("title") or [""])[0], "type": m.get("type"), "year": (m.get("issued") or {}).get("date-parts", [[None]])[0][0], "reference": [r.get("DOI") for r in m.get("reference", []) if r.get("DOI")], "n_ref": len(m.get("reference", []))}
            break
        except urllib.error.HTTPError as e:
            if e.code == 404: cache[d] = {"title": "", "type": None, "year": None, "reference": [], "n_ref": 0}; break
            time.sleep(2)
        except Exception:
            time.sleep(2)
    time.sleep(0.15)
    return cache.get(d, {"title": "", "reference": [], "n_ref": 0})
R = json.load(open("records_v2_auto.json", encoding="utf-8"))
have = {r["doi"] for r in R if r.get("doi")}
out = {"reviews": {}, "known_items": []}
cited = {}
for k, d in REVIEWS.items():
    m = cr(d)
    out["reviews"][k] = {"doi": d, "n_references": m["n_ref"], "n_with_doi": len(m["reference"])}
    for x in m["reference"]:
        cited.setdefault(x.lower(), set()).add(k)
print({k: v for k, v in out["reviews"].items()})
for i, (d, src) in enumerate(cited.items()):
    m = cr(d)
    if AVRE.search(m.get("title") or ""):
        out["known_items"].append({"doi": d, "title": m["title"], "type": m["type"], "year": m["year"], "cited_by": sorted(src), "retrieved": d in have})
    if i % 100 == 0:
        json.dump(cache, open(cache_p, "w", encoding="utf-8"))
json.dump(cache, open(cache_p, "w", encoding="utf-8"))
ki = out["known_items"]
out["n_known"] = len(ki); out["n_retrieved"] = sum(k["retrieved"] for k in ki)
json.dump(out, open("recall_check.json", "w", encoding="utf-8"), indent=1)
print("known items:", len(ki), "retrieved:", out["n_retrieved"], f"({100 * out['n_retrieved'] / max(1, len(ki)):.1f}%)")
for k in ki:
    if not k["retrieved"]: print("  MISSED:", k["year"], k["type"], k["doi"], k["title"][:100])
