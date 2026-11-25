"""Compare PDF-based recoding of the readiness conditions with the text-based codes; recompute strict and base readiness;
marginal and drop-one counts. Usage: pdf_recheck.py <run log .jsonl>. Writes pdf_recheck.json."""
import json, os, sys
AN = os.path.dirname(os.path.abspath(__file__))
F = {s["rid"]: s for s in json.load(open(os.path.join(AN, "final_v5.json"), encoding="utf-8"))}
M = json.load(open(os.path.join(AN, "mech_codes.json"), encoding="utf-8"))
P = {}
for _jf in sys.argv[1:]:
    for l in open(_jf, encoding="utf-8"):
        o = json.loads(l)
        if o.get("type") == "result":
            v = o["result"]; v = json.loads(v) if isinstance(v, str) else v
            for s in (v.get("studies", []) if isinstance(v, dict) else []): P[s["rid"]] = s
# adjudication of disagreements that decide strict readiness, against the paper's own text
ADJ = {       "R0984": ("outputs_with_error_statistic", ["pv_energy"], "Crop yield was fitted with empirical curves to the same field data; only the light model was tested on held-out data with an error statistic.")}
P_raw = {k: dict(v) for k, v in P.items()}
for r, (fld, val, why) in ADJ.items():
    if r in P: P[r][fld] = val
_lp = os.path.join(AN, "..", "search", "relayout_items.json")
LAYOUT = {x[0] for x in json.load(open(_lp))} if os.path.exists(_lp) else set()
ids = json.load(open(os.path.join(AN, "..", "search", "c62_ids.json")))
DEC = {"trk": ({"light_shading", "pv_energy", "crop"}, ("crop", "pv_energy"), {"sub_hourly", "hourly"}),
       "irr": ({"water", "crop"}, ("water", "crop"), {"sub_hourly", "hourly", "daily"}),
       "cln": ({"soiling", "pv_energy"}, ("pv_energy", "soiling"), {"sub_hourly", "hourly", "daily"})}
def text_codes(r):
    s = F[r]; m = M[r]; V = set(m["validated_subsystems"]) - {"none", "NA"}
    gof = m["goodness_of_fit_reported"] == "yes"
    return {"V": V, "E": V if gof else set(), "ind": m["validation_independent"] == "yes",
            "link": s["coupling"] in ("one_way", "two_way_or_integrated") or "none" not in m["feedbacks_represented"],
            "spec": s["physical_counterpart"] == "specific_installation", "ts": m["model_time_step"]}
def pdf_codes(r):
    p = P[r]; V = set(p["validated_outputs"]) - {"none"}; E = set(p["outputs_with_error_statistic"]) - {"none"}
    return {"V": V, "E": E, "ind": p["validation_independent"] == "yes", "link": p["subsystems_linked"] == "yes",
            "spec": p["specific_installation"] == "yes", "ts": p["model_time_step"]}
def chain(codes, r):
    subs = set(F[r]["subsystems"]); out = {}
    for k, (need, outs, ts) in DEC.items():
        if not need <= subs: continue
        c = codes(r)
        conds = [all(o in c["E"] for o in outs), c["link"], c["spec"], c["ind"], c["ts"] in ts]
        base = bool(c["V"] & ({"crop", "light_shading", "microclimate"} if k == "trk" else set(outs) | ({"soiling", "other"} if k == "cln" else set()))) and (k != "trk" or "pv_energy" in c["V"]) and c["link"] and c["spec"]
        out[k] = {"conds": conds, "ready": all(conds), "base": base}
    return out
have = [r for r in ids if r in P]
res = {"n_candidates": len(ids), "n_recoded": len(have), "adjudicated": {r: {"field": f_, "value": v_, "reason": w_} for r, (f_, v_, w_) in ADJ.items()}}
# agreement per field (text vs PDF)
def agree(fn):
    pp = [(fn(text_codes(r)), fn(pdf_codes(r))) for r in have]; n = len(pp); a = sum(x == y for x, y in pp)
    po = a / n; cs = set(x for x, _ in pp) | set(y for _, y in pp)
    pe = sum((sum(x == c for x, _ in pp) / n) * (sum(y == c for _, y in pp) / n) for c in cs)
    return {"n": n, "agree": a, "kappa": round((po - pe) / (1 - pe), 2) if pe < 1 else None}
fields = {"any output validated": lambda c: bool(c["V"]), "crop validated": lambda c: "crop" in c["V"], "PV validated": lambda c: "pv_energy" in c["V"],
          "water validated": lambda c: "water" in c["V"], "error statistic reported": lambda c: bool(c["E"]), "independent validation": lambda c: c["ind"],
          "subsystems linked": lambda c: c["link"], "specific installation": lambda c: c["spec"]}
res["agreement"] = {k: agree(fn) for k, fn in fields.items()}
res["pdf_more_validation"] = sum(1 for r in have if len(pdf_codes(r)["V"]) > len(text_codes(r)["V"]))
res["pdf_less_validation"] = sum(1 for r in have if len(pdf_codes(r)["V"]) < len(text_codes(r)["V"]))
# readiness from PDF codes (with text codes for any study not recoded)
codes_mix = lambda r: pdf_codes(r) if r in P else text_codes(r)
names = ["every traded-off output validated with an error statistic", "linked", "specific installation", "independent validation data", "adequate time step"]
_Pkeep = P
def _raw_codes(r):
    global P
    P0 = P; P = P_raw
    try: return pdf_codes(r)
    finally: P = P0
for label, cf in (("text", text_codes), ("pdf", codes_mix), ("pdf_unadjudicated", lambda r: _raw_codes(r) if r in P_raw else text_codes(r))):
    ready = {k: 0 for k in DEC}; base = {k: 0 for k in DEC}; anyr = set(); anyb = set(); marg = [0] * 5; drop = [set() for _ in range(5)]; cand = {k: 0 for k in DEC}
    for r in ids:
        ch = chain(cf, r)
        for k, d in ch.items():
            cand[k] += 1; ready[k] += d["ready"]; base[k] += d["base"]
            if d["ready"]: anyr.add(r)
            if d["base"]: anyb.add(r)
            for i, c in enumerate(d["conds"]): marg[i] += c
            for i in range(5):
                if all(c for j, c in enumerate(d["conds"]) if j != i): drop[i].add(r)
    res[label] = {"cand": cand, "ready": ready, "base": base, "any_ready": len(anyr), "any_base": len(anyb), "any_ready_ids": sorted(anyr), "any_base_ids": sorted(anyb),
                  "marginal": dict(zip(names, marg)), "drop_one": {names[i]: len(drop[i]) for i in range(5)}, "drop_one_ids": {names[i]: sorted(drop[i]) for i in range(5)}}
res["rows"] = [[r, F[r]["title"], ", ".join(sorted(text_codes(r)["V"])) or "none", ", ".join(sorted(pdf_codes(r)["V"])) or "none", ", ".join(sorted(pdf_codes(r)["E"])) or "none",
                P[r]["validation_independent"], P[r]["subsystems_linked"], P[r]["specific_installation"], P[r]["model_time_step"], P[r]["evidence"], "layout-preserving text from the PDF" if r in LAYOUT else "rendered PDF pages"] for r in have]
res["n_layout"] = sum(1 for r in have if r in LAYOUT); res["n_rendered"] = len(have) - res["n_layout"]
json.dump(res, open(os.path.join(AN, "pdf_recheck.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False, indent=1)[:3500])
