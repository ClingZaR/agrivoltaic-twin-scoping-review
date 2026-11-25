"""Assemble the final coded dataset.
Usage: assemble.py charts.json records.json final.json
charts.json: {"A": {...}, "B": {...}, "ADJ": {...}} where ADJ holds verification overrides (subset of fields) and
eligibility adjudications (full objects with 'eligible')."""
import json, sys, re
C = json.load(open(sys.argv[1], encoding="utf-8"))
R = {r["rid"]: r for r in json.load(open(sys.argv[2], encoding="utf-8"))}
final, excluded = [], []
for rid, a in C["A"].items():
    s = dict(a)
    adj = C["ADJ"].get(rid)
    if adj:
        for k, v in adj.items():
            if k in ("rid", "justification"):
                continue
            s[k] = v
        s["verified"] = True
        s["verification_note"] = adj.get("justification", "")
    CALIAS = {"USA": "United States", "US": "United States", "U.S.": "United States", "U.S.A.": "United States", "UK": "United Kingdom", "Korea": "South Korea", "Republic of Korea": "South Korea", "UAE": "United Arab Emirates"}
    if isinstance(s.get("country"), list):
        s["country"] = list(dict.fromkeys(CALIAS.get(c.strip(), c.strip()) for c in s["country"]))
    km = [k for k in (s.get("koppen_main") or []) if k != "NR"]
    s["koppen_main"] = sorted(set(km)) if km else ["NR"]
    r = R.get(rid, {})
    s["title"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.get("title") or "")).strip()
    s["year"] = r.get("year"); s["venue"] = r.get("venue"); s["doi"] = r.get("doi"); s["authors"] = r.get("authors") or []
    s["sources"] = r.get("sources"); s["oa_type"] = r.get("oa_type") or r.get("scopus_type") or ",".join(r.get("s2_types") or [])
    t = (s["oa_type"] or "").lower()
    s["venue_kind"] = "conference" if ("conference" in t or "proceeding" in (s["venue"] or "").lower()) else "journal"
    (final if s["eligible"] == "INCLUDE" else excluded).append(s)
final.sort(key=lambda s: (s.get("year") or 0, s["title"]))
for i, s in enumerate(final, 1):
    s["sid"] = f"S{i:03d}"
json.dump(final, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(excluded, open(sys.argv[3].replace(".json", "_excluded.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("included", len(final), "excluded at full text", len(excluded))
