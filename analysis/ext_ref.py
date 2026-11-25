"""External human reference: match the per-study codes published by other reviews (extracted with their own wording)
to this review's codes, and compute agreement. Usage: ext_ref.py <run log .jsonl>"""
import json, os, re, sys, difflib, collections
AN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AN, "..", "search"))
F = {s["rid"]: s for s in json.load(open(os.path.join(AN, "final_v5.json"), encoding="utf-8"))}
X = {s["rid"]: s for s in json.load(open(os.path.join(AN, "final_v5_excluded.json"), encoding="utf-8"))}
R = {r["rid"]: r for r in json.load(open(os.path.join(AN, "..", "search", "records_v2_auto.json"), encoding="utf-8"))}
M = json.load(open(os.path.join(AN, "mech_codes.json"), encoding="utf-8"))
lab = {}; res = []
for line in open(sys.argv[1], encoding="utf-8"):
    o = json.loads(line)
    if o.get("type") == "started": lab[o["agentId"]] = o.get("label", "")
    if o.get("type") == "result":
        v = o.get("result")
        if isinstance(v, str):
            try: v = json.loads(v)
            except Exception: continue
        if isinstance(v, dict) and "rows" in v: res.append({"job": lab.get(o["agentId"], ""), "rows": v["rows"]})
def norm(t): return re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower()).split()
IDX = [(rid, norm(r.get("title"))) for rid, r in R.items()]
def match(title):
    a = norm(title)
    if len(a) < 4: return None, 0
    sa = " ".join(a); best, bs = None, 0
    for rid, b in IDX:
        if not b or abs(len(b) - len(a)) > 12: continue
        r = difflib.SequenceMatcher(None, sa, " ".join(b)).ratio()
        if r > bs: best, bs = rid, r
    return (best, bs) if bs >= 0.88 else (None, bs)
def ours_val(s):
    v = s["validation_setting"]
    return "field" if v.startswith("field") or v == "laboratory_or_prototype" else ("software" if v == "simulation_benchmark_only" else "none")
out = {"rows": [], "summary": {}}
for job in res:
    name = (job.get("job") or "").lower()
    for row in job["rows"]:
        rid, sc = match(row.get("ref_title"))
        st = "included" if rid in F else ("excluded" if rid in X else ("not retrieved by search" if rid is None else "screened out"))
        rec = {"source": name, "ref_no": row.get("ref_no"), "ref_title": row.get("ref_title"), "their_code": row.get("code"), "their_text": row.get("review_text"), "rid": rid, "match": round(sc, 2), "status": st}
        if rid in F:
            s = F[rid]; rec["our_text_basis"] = s["text_basis"]
            if "pillai" in name:
                rec["our_country"] = s.get("country"); rec["our_koppen"] = s.get("koppen_main")
            else:
                rec["our_code"] = ours_val(s)
                if rid in M: rec["our_mech_validated"] = M[rid]["validated_subsystems"]
        out["rows"].append(rec)
# de-duplicate (same study in several tables of one review): keep one row per (source, rid), preferring a decisive code
seen = {}
for r in out["rows"]:
    if r["rid"] is None: continue
    k = (r["source"], r["rid"])
    if k not in seen or (seen[k]["their_code"] == "unclear" and r["their_code"] != "unclear"): seen[k] = r
U = list(seen.values())
def agree_val(rows):
    rows = [r for r in rows if r["status"] == "included" and r.get("their_code") in ("field", "none", "software")]
    bin_ = lambda c: "measured" if c == "field" else "not measured"
    pp = [(bin_(r["their_code"]), bin_(r["our_code"])) for r in rows]
    n = len(pp); a = sum(x == y for x, y in pp)
    po = a / n if n else 0; cs = {"measured", "not measured"}
    pe = sum((sum(x == c for x, _ in pp) / n) * (sum(y == c for _, y in pp) / n) for c in cs) if n else 0
    k = (po - pe) / (1 - pe) if n and pe < 1 else float("nan")
    tp = sum(1 for x, y in pp if x == y == "measured"); fn = sum(1 for x, y in pp if x == "measured" and y != "measured"); fp = sum(1 for x, y in pp if x != "measured" and y == "measured")
    return {"n": n, "agree": a, "kappa": round(k, 2), "sens": f"{tp}/{tp + fn}", "ppv": f"{tp}/{tp + fp}", "ft": sum(r["our_text_basis"] == "full_text" for r in rows),
            "disagree": [(r["rid"], r["their_code"], r["our_code"], r["our_text_basis"]) for r in rows if bin_(r["their_code"]) != bin_(r["our_code"])]}
for src in sorted({r["source"] for r in U}):
    rows = [r for r in U if r["source"] == src]
    c = collections.Counter(r["status"] for r in rows)
    out["summary"][src] = {"matched": len(rows), "status": dict(c)}
    if "pillai" not in src: out["summary"][src]["validation"] = agree_val(rows)
    else:
        inc = [r for r in rows if r["status"] == "included"]
        def ctry_ok(r):
            their = (r["their_text"] + " " + r["their_code"]).lower().replace("usa", "united states").replace("u.s.", "united states"); ours = [c.lower() for c in (r["our_country"] or [])] if isinstance(r["our_country"], list) else [str(r["our_country"]).lower()]
            return any(c and c != "nr" and c.split()[0] in their for c in ours)
        out["summary"][src]["country_agree"] = f"{sum(map(ctry_ok, inc))}/{len(inc)}"
        out["summary"][src]["arid_B"] = f"{sum(1 for r in inc if r['our_koppen'] and 'B' in r['our_koppen'])}/{len(inc)}"
        out["summary"][src]["country_disagree"] = [(r["rid"], r["their_code"], r["our_country"]) for r in inc if not ctry_ok(r)]
allv = [r for r in U if "pillai" not in r["source"]]
out["summary"]["validation_pooled"] = agree_val(allv)
out["summary"]["validation_pooled_ft"] = agree_val([r for r in allv if r.get("our_text_basis") == "full_text"])
out["summary"]["validation_pooled_abs"] = agree_val([r for r in allv if r.get("our_text_basis") and r.get("our_text_basis") != "full_text"])
real = [r for r in out["rows"] if not (r["ref_title"] or "").startswith("UNRESOLVED")]
out["summary"]["n_cited_rows_resolved"] = len({(r["ref_title"] or "").lower() for r in real})
out["summary"]["n_not_retrieved"] = len({(r["ref_title"] or "").lower() for r in real if r["rid"] is None})
out["summary"]["not_retrieved_titles"] = sorted({r["ref_title"] for r in real if r["rid"] is None})
cited = {r["rid"] for r in U if r["rid"]}
out["summary"]["n_cited_unique"] = len(cited); out["summary"]["n_cited_included"] = sum(1 for r in cited if r in F)
out["summary"]["n_unmatched_rows"] = sum(1 for r in out["rows"] if r["rid"] is None)
json.dump(out, open(os.path.join(AN, "ext_ref.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out["summary"], ensure_ascii=False, indent=1)[:4000])
