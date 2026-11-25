"""Additional facts for the revised template. Usage: facts2.py facts.json stats.json final.json charts.json recall.json"""
import json, sys, collections
FA = json.load(open(sys.argv[1], encoding="utf-8")); S = json.load(open(sys.argv[2], encoding="utf-8"))
F = json.load(open(sys.argv[3], encoding="utf-8")); CH = json.load(open(sys.argv[4], encoding="utf-8")); RC = json.load(open(sys.argv[5], encoding="utf-8"))
X = S["extra"]; N = len(F)
def pct(n, d): return f"{100 * n / d:.0f}" if d else "0"
def join(items):
    items = [i for i in items if i]
    return items[0] if len(items) == 1 else (" and ".join(items) if len(items) == 2 else ", ".join(items[:-1]) + ", and " + items[-1])
f = {}
# recall
f["n_known"] = RC["n_known"]; f["n_known_retrieved"] = RC["n_retrieved"]; f["pct_known_retrieved"] = f"{100 * RC['n_retrieved'] / RC['n_known']:.0f}"
f["n_known_missed"] = RC["n_known"] - RC["n_retrieved"]
#
import os as _os
_p0 = _os.path.join(_os.path.dirname(_os.path.abspath(sys.argv[4])), "charts_all_before_v5.json")
CHT = json.load(open(_p0, encoding="utf-8")) if _os.path.exists(_p0) else CH
inc = {s["rid"] for s in F}
pairs = []
for r in sorted(inc):
    a = CHT["A"].get(r, {})
    if "dt_maturity_v2" not in a: continue
    c1 = a.get("dt_maturity_coder1") or CHT["ADJ"].get(r, {}).get("dt_maturity") or a["dt_maturity"]
    if a.get("dt_maturity_coder1") is None and CHT["ADJ"].get(r, {}).get("twin_adjudicated"):
        c1 = a["dt_maturity"]
    pairs.append((c1, a["dt_maturity_v2"]))
n = len(pairs); agree = sum(x == y for x, y in pairs)
cats = set(x for x, _ in pairs) | set(y for _, y in pairs)
po = agree / n; pe = sum((sum(x == c for x, _ in pairs) / n) * (sum(y == c for _, y in pairs) / n) for c in cats)
f["twin_double_n"] = n; f["twin_agree_n"] = agree; f["twin_kappa"] = f"{(po - pe) / (1 - pe):.2f}"
f["twin_adjudicated"] = sum(1 for r in inc if CHT["ADJ"].get(r, {}).get("twin_adjudicated"))
f["twin_confusion"] = {f"{x}|{y}": c for (x, y), c in collections.Counter(pairs).items()}
# not retrieved
pubs = X["not_retrieved_publishers"]
top = list(pubs.items())[:3]
f["n_nr_nodoi"] = pubs.get("No DOI", 0)
f["nr_publishers"] = join([f"{k} ({v})" for k, v in top]) if top else "no single publisher"
# sensitivity
sv = X["sens"]
def sp(k, which): a, d = sv[k][which]; return pct(a, d)
f["sens_tr_full"], f["sens_tr_abs"] = sp("temporal_resolution_reported", "full"), sp("temporal_resolution_reported", "abs")
f["sens_val_full"], f["sens_val_abs"] = sp("validation_reported", "full"), sp("validation_reported", "abs")
core = [k for k in ("ai", "shadow_or_twin") if sv[k]["p"] >= 0.05]
f["sens_core_sentence"] = ("The codes for AI use and for the digital twin level do not differ significantly between the two groups." if len(core) == 2
                           else "The codes for AI use and the digital twin level also differ between the two groups, so these shares should be read with the same caution.")
# characteristics
pc = X["physical_counterpart"]
f["n_specific"] = pc.get("specific_installation", 0); f["pct_specific"] = pct(f["n_specific"], N)
f["n_generic"] = pc.get("generic_design", 0); f["pct_generic"] = pct(f["n_generic"], N)
# climate
f["n_site_specific"] = X["n_site_specific"]; f["n_B"] = X["n_B"]; f["pct_B_site"] = pct(X["n_B"], X["n_site_specific"])
f["n_hot_arid"] = X["n_hot_arid"]; f["n_cold_arid"] = X["n_cold_arid"]
def ci(t): return f"{t[0]:.0f}–{t[1]:.0f}%"
def pfmt(p): return "<0.001" if p < 0.001 else f"{p:.2f}" if p >= 0.01 else f"{p:.3f}"
for k in ["ai", "field_validation", "water", "soiling", "measured", "operation"]:
    c = X[f"cmp_{k}"]
    f[f"cmp_{k}_B_n"], f[f"cmp_{k}_B_d"] = c["B"]; f[f"cmp_{k}_nonB_n"], f[f"cmp_{k}_nonB_d"] = c["nonB"]
    f[f"cmp_{k}_B_pct"] = pct(*c["B"]); f[f"cmp_{k}_nonB_pct"] = pct(*c["nonB"])
    f[f"cmp_{k}_B_ci"] = ci(c["ciB"]); f[f"cmp_{k}_nonB_ci"] = ci(c["ciNonB"]); f[f"cmp_{k}_p"] = pfmt(c["p"])
abk = X["ai_by_koppen"]
f["n_ai_B"] = abk.get("B", 0); f["n_ai_C"] = abk.get("C", 0); f["n_ai_nosite"] = abk.get("NR", 0)
# methods
f["n_pred_operation"] = X["function_by_stage"]["prediction"]["operation"]
cp = X["coupling"]; f["n_coup_one_way"] = cp.get("one_way", 0); f["n_coup_two_way"] = cp.get("two_way_or_integrated", 0)
f["n_uq"] = X["uncertainty_quantification"].get("yes", 0); f["pct_uq"] = pct(f["n_uq"], N)
da = X["data_assimilation"]; f["n_assim"] = da.get("sequential_updating", 0); f["n_calib"] = da.get("calibration_only", 0); f["pct_calib"] = pct(f["n_calib"] + f["n_assim"], N)
# twins
tw = [s for s in F if s["dt_maturity"] in ("digital_shadow", "digital_twin")]
f["n_shadow_or_twin"] = len(tw)
impl = collections.Counter((s["dt_maturity"], s.get("implementation_status")) for s in tw)
f["n_twin_operating"] = impl.get(("digital_twin", "operating_installation"), 0)
tw_t = [s for s in tw if s["dt_maturity"] == "digital_twin"]; tw_s = [s for s in tw if s["dt_maturity"] == "digital_shadow"]
def impl_phrase(group):
    c = collections.Counter(s.get("implementation_status") for s in group)
    lab = {"operating_installation": ("runs", "run", "on an operating installation"), "prototype_or_testbed": ("runs", "run", "on a prototype or testbed"),
           "concept_or_proposal": ("exists only as a design", "exist only as designs", "")}
    parts = []
    for k, v in c.most_common():
        sg, pl, rest = lab.get(k, ("is", "are", k))
        parts.append(f"{v} {sg if v == 1 else pl} {rest}".rstrip())
    return join(parts)
f["twin_impl_sentence"] = (f"Of the digital twins, {impl_phrase(tw_t)}. Of the digital shadows, {impl_phrase(tw_s)}." if tw_t and tw_s else "")
# operational subset
op = X["indicators_operational"]; al = X["indicators_all"]
f["n_operational"] = X["n_operational"]; f["pct_operational"] = pct(X["n_operational"], N)
for k, (a, d) in op.items(): f[f"op_{k}"] = pct(a, d)
for k, (a, d) in al.items(): f[f"all_{k}"] = pct(a, d)
f["op_better_all"] = all(op[k][0] / max(1, op[k][1]) >= al[k][0] / max(1, al[k][1]) for k in op)
FA.update(f)
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k in ["twin_double_n", "twin_agree_n", "twin_kappa", "twin_adjudicated", "nr_publishers", "sens_core_sentence", "n_specific", "pct_B_site", "n_hot_arid", "n_cold_arid",
          "cmp_ai_B_pct", "cmp_ai_nonB_pct", "cmp_ai_p", "n_pred_operation", "n_coup_two_way", "n_assim", "twin_impl_sentence", "n_operational", "op_better_all", "twin_confusion"]:
    print(k, "=", f.get(k))

# ---- additional analyses ----
import random
g = {}
# kappa CI by bootstrap (fixed seed) and adjudication breakdown
def kap(pp):
    n = len(pp); po = sum(a == b for a, b in pp) / n
    cs = set(a for a, _ in pp) | set(b for _, b in pp)
    pe = sum((sum(a == c for a, _ in pp) / n) * (sum(b == c for _, b in pp) / n) for c in cs)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0
rng = random.Random(20261125)
boots = sorted(kap([pairs[rng.randrange(len(pairs))] for _ in pairs]) for _ in range(1000))
g["twin_kappa_ci"] = f"{boots[25]:.2f}–{boots[974]:.2f}"
dis = [p for p in pairs if p[0] != p[1]]
g["twin_disagree_n"] = len(dis)
g["twin_agreed_shadow_twin"] = sum(1 for a, b in pairs if a == b and a in ("digital_shadow", "digital_twin"))
changed = 0
for r in sorted(inc):
    a = CHT["A"].get(r, {}); adj = CHT["ADJ"].get(r, {})
    if adj.get("twin_adjudicated") and a.get("dt_maturity_coder1") and adj.get("dt_maturity") != a.get("dt_maturity_coder1"):
        changed += 1
g["twin_changed_by_adj"] = changed
# AI by period
abp = X["ai_by_period"]
g["ai_period_sentence"] = "The share of studies using AI rose from " + ", to ".join(f"{pct(*v)}% of {k}" for k, v in abp.items() if v[1]) + "."
# AI by climate, complete
abk = X["ai_by_koppen_full"]
lab = {"A": "a tropical site", "B": "an arid site", "C": "a temperate site", "D": "a continental site", "E": "a polar site", "NR": "no classifiable site"}
g["ai_climate_sentence"] = "Of the " + str(FA.get("n_ai", 0)) + " AI studies, " + join([f"{v} {'has' if v == 1 else 'have'} {lab[k]}" for k, v in sorted(abk.items(), key=lambda kv: -kv[1])]) + "."
# digital model share among studies with a virtual model
g["n_with_model"] = X["n_with_model"]; g["pct_dm_of_models"] = pct(FA["n_dt_digital_model"] if isinstance(FA["n_dt_digital_model"], int) else int(str(FA["n_dt_digital_model"]).replace(",", "")), X["n_with_model"])
# limitations base
g["n_lim_text"] = X["n_lim_text"]; g["pct_lim_text"] = pct(X["n_lim_text"], N)
g["n_fut_text"] = X["n_fut_text"]; g["pct_fut_text"] = pct(X["n_fut_text"], N)
sv = X["sens"]["limitations_stated"]
g["lim_full_share"] = pct(sv["full"][0], X["n_lim_text"])
# operational versus design only
od = X["indicators_design"]; opp = X["indicators_p"]
g["n_design_only"] = X["n_design_only"]
for k, (a, d) in od.items(): g[f"des_{k}"] = pct(a, d)
def pf(p): return "<0.001" if p < 0.001 else (f"{p:.2f}" if p >= 0.01 else f"{p:.3f}")
for k, p in opp.items(): g[f"opp_{k}"] = pf(p)
FA.update(g)
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in g.items(): print(k, "=", v)

# ---- calibration of abstract-based coding against full text ----
C = X.get("calib", {})
if C:
    h = {}
    def sens(k): v = C[k]; return v["both"] / v["full"] if v["full"] else None
    def ppv(k): v = C[k]; return v["both"] / v["abs"] if v["abs"] else None
    h["calib_n"] = C["AI used"]["n"]; h["calib_n_total"] = C["Included on eligibility"]["full"]; h["calib_elig_pct"] = pct(C["Included on eligibility"]["abs"], C["Included on eligibility"]["full"])
    for key, lab in [("Field validation", "fv"), ("AI used", "ai"), ("Operational decisions addressed", "op"), ("Real-time operation demonstrated", "rt"),
                     ("Temporal resolution reported", "tr"), ("Data or code shared", "od"), ("Measured data used", "md"), ("Specific real installation", "si")]:
        se = sens(key); h[f"sens_{lab}"] = f"{100 * se:.0f}" if se is not None else "NA"
    # corrected corpus shares: full-text studies as coded, abstract-charted studies scaled by PPV/sensitivity
    IND2 = {"fv": ("Field validation", "field_validation"), "rt": ("Real-time operation demonstrated", "realtime_demo"), "ai": ("AI used", "ai"), "md": ("Measured data used", "measured_data")}
    ft = {k: v for k, v in X["sens"].items()}
    for lab, (ck, sk) in IND2.items():
        se, pv = sens(ck), ppv(ck)
        if not se or not pv: continue
        sk2 = {"field_validation": "field_validation", "realtime_demo": "realtime_demo", "ai": "ai", "measured_data": None}[sk]
        if sk2 is None:
            full_n = sum(1 for s in F if s["text_basis"] == "full_text" and any(m in s["sensing_modalities"] for m in ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]))
            abs_n = sum(1 for s in F if s["text_basis"] != "full_text" and any(m in s["sensing_modalities"] for m in ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]))
        else:
            full_n, abs_n = ft[sk2]["full"][0], ft[sk2]["abs"][0]
        corr = (full_n + abs_n * pv / se) / N
        h[f"corr_{lab}"] = f"{100 * corr:.0f}"
    FA.update(h)
    json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in h.items(): print(k, "=", v)

# ---- explanations for the rarity of twins ----
MEAS2 = ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]
online = lambda s: any(d in s["deployment"] for d in ["edge_or_embedded", "cloud", "fog_or_gateway", "multi_tier"]) or s["real_time"] == "real_time_operation_demonstrated"
phys = lambda s: "physics_based" in s["method_families"]
k = {}
ph = [s for s in F if phys(s)]; on = [s for s in F if online(s)]
k["n_phys"] = len(ph); k["n_phys_online"] = sum(online(s) for s in ph)
k["n_online"] = len(on); k["n_online_phys"] = sum(phys(s) for s in on); k["n_online_coupled"] = sum(s.get("coupling") in ("one_way", "two_way_or_integrated") for s in on)
k["n_full_stack"] = sum(1 for s in F if phys(s) and s.get("coupling") in ("one_way", "two_way_or_integrated") and any(m in s["sensing_modalities"] for m in MEAS2) and online(s))
k["n_ai_phys"] = sum(1 for s in F if s["ai_used"] == "yes" and phys(s))
FA.update(k)
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- reports versus research groups (first-author clustering) ----
import re as _re
def _fa(s):
    a = (s.get("authors") or [""])[0] or ""
    a = a.split(",")[0] if "," in a else a.split(" ")[-1]
    return _re.sub(r"[^a-z]", "", a.lower())
fac = collections.Counter(_fa(s) for s in F if _fa(s))
m = {"n_first_authors": len(fac), "n_reports_top10_authors": sum(v for _, v in fac.most_common(10)),
     "n_first_authors_multi": sum(1 for v in fac.values() if v > 1), "n_reports_by_multi": sum(v for v in fac.values() if v > 1)}
FA.update(m)
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(m)

# ---- designed versus demonstrated level ----
DEMO = ("operating_installation", "prototype_or_testbed")
tw2 = [s for s in F if s["dt_maturity"] in ("digital_shadow", "digital_twin")]
d = {"n_demo_stream": sum(1 for s in tw2 if s.get("implementation_status") in DEMO),
     "n_demo_operating": sum(1 for s in tw2 if s.get("implementation_status") == "operating_installation"),
     "n_demo_prototype": sum(1 for s in tw2 if s.get("implementation_status") == "prototype_or_testbed"),
     "n_design_stream": sum(1 for s in tw2 if s.get("implementation_status") not in DEMO),
     "n_demo_twin": sum(1 for s in tw2 if s["dt_maturity"] == "digital_twin" and s.get("implementation_status") in DEMO),
     "n_demo_shadow": sum(1 for s in tw2 if s["dt_maturity"] == "digital_shadow" and s.get("implementation_status") in DEMO)}
FA.update(d)
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(d)

# ---- model families mentioned in titles and abstracts of physics-based studies ----
_RECS = {r["rid"]: r for r in json.load(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "search", "records_v2_auto.json"), encoding="utf-8"))}
_PAT = {"pv_tools": r"PVsyst|\bSAM\b|System Advisor Model|pvlib|PV\*?SOL|PVGIS", "crop_models": r"\bSTICS\b|APSIM|DSSAT|AquaCrop|WOFOST|crop (growth )?model|crop simulation|LINTUL|GECROS|SUCROS",
        "ray": r"ray[- ]?trac|view[- ]?factor|radiosity|bifacial_?radiance|radiance software|monte carlo ray", "et": r"evapotranspiration|Penman|soil water balance|HYDRUS|water balance",
        "thermal": r"energy balance|heat transfer|thermal model|TRNSYS|EnergyPlus", "cfd": r"computational fluid dynamics|\bCFD\b"}
_ph = [s for s in F if "physics_based" in s["method_families"]]
for k, p in _PAT.items():
    FA[f"n_mention_{k}"] = sum(1 for s in _ph if (_re.search(p, (_RECS[s["rid"]].get("title") or "") + " " + (_RECS[s["rid"]].get("abstract") or ""), _re.I) if "abstract" in _RECS[s["rid"]] else _RECS[s["rid"]]["ta_flags"][k]))
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- reconciliation facts requested in the meta-review ----
q = {}
def _named(s):
    out = []
    for c in (s.get("country") or []):
        c = (c or "").strip()
        if c.lower() in ("", "nr", "none", "not reported", "na", "n/a", "generic", "not site-specific", "unspecified") or "not named" in c.lower() or "(" in c or len(c) > 40:
            continue
        out.append(c)
    return out
q["n_named_unclassified"] = sum(1 for s in F if _named(s) and s["koppen_main"] == ["NR"])
q["n_unnamed_classified"] = sum(1 for s in F if not _named(s) and s["koppen_main"] != ["NR"])
q["n_arid_site"] = sum(1 for s in F if "B" in s["koppen_main"])
q["n_arid_target_only"] = sum(1 for s in F if s["arid_focus"] == "explicit" and "B" not in s["koppen_main"])
GCC = {"Saudi Arabia", "United Arab Emirates", "Kuwait", "Qatar", "Oman", "Bahrain"}
q["n_gcc"] = sum(1 for s in F if any(c.strip() in GCC or c.strip() in ("UAE", "KSA") for c in s["country"]))
MENA2 = {"Algeria", "Bahrain", "Djibouti", "Egypt", "Iran", "Iraq", "Israel", "Jordan", "Kuwait", "Lebanon", "Libya", "Malta", "Morocco", "Oman", "Palestine", "Qatar", "Saudi Arabia", "Syria", "Tunisia", "United Arab Emirates", "Yemen"}
q["n_mena_mentions"] = sum(1 for s in F for c in s["country"] if c in MENA2)
q["n_ai_or_meta"] = sum(1 for s in F if s["ai_used"] == "yes" or "metaheuristic_optimization" in s["method_families"]); q["pct_ai_or_meta"] = pct(q["n_ai_or_meta"], N)
q["n_multi_sub"] = sum(1 for s in F if len(set(s["subsystems"]) - {"economics"}) >= 2)
q["n_light_crop_pv"] = sum(1 for s in F if {"light_shading", "crop", "pv_energy"} <= set(s["subsystems"]))
q["n_impl_na"] = X["implementation_status"].get("NA", 0)
# Lincoln-Petersen estimate for the title-and-abstract stage (records sent forward by each pass)
import glob as _g, os as _os
_sd = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "search")
nA = nB = m = 0
for fpath in _g.glob(_os.path.join(_sd, "abs_r*_results.json")):
    dd = json.load(open(fpath))
    for rid in dd["A"]:
        a = dd["A"][rid]["decision"] != "EXCLUDE"; b = dd["B"].get(rid, {}).get("decision", "EXCLUDE") != "EXCLUDE"
        nA += a; nB += b; m += (a and b)
est = nA * nB / m if m else 0
q["lp_missed"] = f"{max(0, est - (nA + nB - m)):.1f}"; q["lp_nA"], q["lp_nB"], q["lp_m"] = nA, nB, m
# field-experiment proxy among E2 exclusions
_R = _RECS
_e2 = []
for fpath in _g.glob(_os.path.join(_sd, "abs_r*_results.json")):
    dd = json.load(open(fpath))
    _e2 += [rid for rid, v in dd["combined"].items() if v.get("abs_decision") == "EXCLUDE" and (v.get("code") or "") == "E2"]
_e2 += [rid for rid, v in CH["A"].items() if (CH["ADJ"].get(rid, {}).get("eligible") or v["eligible"]) == "EXCLUDE" and v["exclusion_code"] == "E2"]
q["n_e2_total"] = len(set(_e2))
q["n_e2_field"] = sum(1 for rid in set(_e2) if (_re.search(r"field (experiment|trial|study|measurement)|experiment|trial|measured|monitoring campaign", (_R[rid].get("title") or "") + " " + (_R[rid].get("abstract") or ""), _re.I) if "abstract" in _R[rid] else _R[rid]["ta_flags"]["e2_field"]))
FA.update(q)
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(q)

# ---- second eligibility check and missed-AI screen ----
e = {}
sec = [r for r, v in CH["A"].items() if "elig_second" in v]
e["n_elig2"] = len(sec)
e["n_elig2_dis"] = sum(1 for r in sec if CH["A"][r]["elig_second"] == "INCLUDE")
e["n_elig2_overturned"] = sum(1 for r in sec if CH["ADJ"].get(r, {}).get("elig_adjudicated") and CH["ADJ"][r].get("eligible") == "INCLUDE")
_fn = json.load(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "ai_fn_check.json")))
e["ai_fn_candidates"] = _fn["n_candidates"]; e["ai_fn_recoded"] = _fn["n_recoded"]; e["ai_fn_screened"] = sum(1 for s in F if s["ai_used"] == "no")
FA.update(e)
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(e)
