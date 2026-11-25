"""Additional analyses. Usage: analyze_extra.py final.json stats.json screening.json records.json  (adds S['extra'])"""
import json, sys, math, collections
F = json.load(open(sys.argv[1], encoding="utf-8")); S = json.load(open(sys.argv[2], encoding="utf-8"))
SC = json.load(open(sys.argv[3], encoding="utf-8")); R = {r["rid"]: r for r in json.load(open(sys.argv[4], encoding="utf-8"))}
N = len(F)
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0, c - h), 100 * min(1, c + h))
def fisher(a, b, c, d):
    """two-sided Fisher exact p for [[a,b],[c,d]]"""
    n1, n2, m1 = a + b, c + d, a + c; n = n1 + n2
    def p(x): return math.comb(n1, x) * math.comb(n2, m1 - x) / math.comb(n, m1)
    p0 = p(a); lo, hi = max(0, m1 - n2), min(n1, m1)
    return min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 * (1 + 1e-9)))
X = {}
def cnt(group, field, multi=False):
    c = collections.Counter()
    for s in group:
        v = s.get(field)
        if multi:
            for x in set(v or []): c[x] += 1
        else: c[v] += 1
    return dict(c.most_common())
for f in ["physical_counterpart", "implementation_status", "coupling", "data_assimilation", "uncertainty_quantification", "fault_or_anomaly_detection"]:
    X[f] = cnt(F, f)
# Koppen subclass for B
sub = collections.Counter()
for s in F:
    for k in set(s.get("koppen_subclass") or []):
        k = (k or "").strip()
        if k.upper().startswith("B"): sub[k[:3] if len(k) >= 3 else k] += 1
X["koppen_B_subclass"] = dict(sub.most_common())
def is_hot_arid(s): return any((k or "").strip()[:3] in ("BWh", "BSh") for k in s.get("koppen_subclass") or [])
def is_cold_arid(s): return any((k or "").strip()[:3] in ("BWk", "BSk") for k in s.get("koppen_subclass") or [])
X["n_hot_arid"] = sum(1 for s in F if is_hot_arid(s)); X["n_cold_arid"] = sum(1 for s in F if is_cold_arid(s))
# site-specific arid comparison
site = [s for s in F if [k for k in s.get("koppen_main") or [] if k != "NR"]]
B = [s for s in site if "B" in s["koppen_main"]]; nonB = [s for s in site if "B" not in s["koppen_main"]]
X["n_site_specific"] = len(site); X["n_B"] = len(B); X["n_nonB"] = len(nonB)
def comp(name, pred):
    a = sum(1 for s in B if pred(s)); c = sum(1 for s in nonB if pred(s))
    X[f"cmp_{name}"] = {"B": [a, len(B)], "nonB": [c, len(nonB)], "p": fisher(a, len(B) - a, c, len(nonB) - c),
                        "ciB": wilson(a, len(B)), "ciNonB": wilson(c, len(nonB))}
comp("ai", lambda s: s["ai_used"] == "yes")
comp("field_validation", lambda s: s["validation_setting"].startswith("field"))
comp("water", lambda s: "water" in s["subsystems"])
comp("soiling", lambda s: "soiling" in s["subsystems"])
comp("measured", lambda s: any(m in s["sensing_modalities"] for m in ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]))
comp("operation", lambda s: "operation" in s["decision_stage"])
# AI studies by climate
ai = [s for s in F if s["ai_used"] == "yes"]
X["ai_by_koppen"] = cnt(ai, "koppen_main", multi=True)
X["ai_by_year"] = cnt(ai, "year")
# operational subset
OP = [s for s in F if "operation" in s["decision_stage"]]
def share(group, pred): k = sum(1 for s in group if pred(s)); return [k, len(group)]
MEAS = ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]
IND = {
 "specific_installation": lambda s: s.get("physical_counterpart") == "specific_installation",
 "measured_data": lambda s: any(m in s["sensing_modalities"] for m in MEAS),
 "multi_season": lambda s: s["data_duration"] == "multi_season_or_multi_year" and any(m in s["sensing_modalities"] for m in MEAS),
 "field_validation": lambda s: s["validation_setting"].startswith("field"),
 "ai": lambda s: s["ai_used"] == "yes",
 "realtime_demo": lambda s: s["real_time"] == "real_time_operation_demonstrated",
 "online_tier": lambda s: any(d in s["deployment"] for d in ["edge_or_embedded", "cloud", "fog_or_gateway", "multi_tier"]),
 "shadow_or_twin": lambda s: s["dt_maturity"] in ("digital_shadow", "digital_twin"),
 "coupled": lambda s: s.get("coupling") in ("one_way", "two_way_or_integrated"),
 "two_way": lambda s: s.get("coupling") == "two_way_or_integrated",
 "assimilation": lambda s: s.get("data_assimilation") == "sequential_updating",
 "calibration": lambda s: s.get("data_assimilation") in ("calibration_only", "sequential_updating"),
 "uq": lambda s: s.get("uncertainty_quantification") == "yes",
 "open_data": lambda s: s["data_or_code_available"] == "yes_public",
}
X["indicators_all"] = {k: share(F, f) for k, f in IND.items()}
X["indicators_operational"] = {k: share(OP, f) for k, f in IND.items()}
DES = [s for s in F if "operation" not in s["decision_stage"]]
X["indicators_design"] = {k: share(DES, f) for k, f in IND.items()}
X["indicators_p"] = {k: fisher(X["indicators_operational"][k][0], len(OP) - X["indicators_operational"][k][0], X["indicators_design"][k][0], len(DES) - X["indicators_design"][k][0]) for k in IND}
X["n_design_only"] = len(DES)
# AI share by period
per = {"studies up to 2021": lambda y: y <= 2021, "studies from 2022 to 2023": lambda y: 2022 <= y <= 2023, "studies from 2024 to 2026": lambda y: y >= 2024}
X["ai_by_period"] = {k: share([s for s in F if s.get("year") and f(s["year"])], lambda s: s["ai_used"] == "yes") for k, f in per.items()}
# AI by climate, complete
X["ai_by_koppen_full"] = cnt(ai, "koppen_main", multi=True)
# digital models among studies with a virtual model
X["n_with_model"] = sum(1 for s in F if s["dt_maturity"] != "NA")
# limitations base
X["n_lim_text"] = sum(1 for s in F if s.get("limitations_stated"))
X["n_fut_text"] = sum(1 for s in F if s.get("future_work_stated"))
X["n_operational"] = len(OP)
# function split by decision stage
X["function_by_stage"] = {fn: {"design_only": sum(1 for s in F if fn in s["dt_functions"] and s["decision_stage"] == ["design"] or (fn in s["dt_functions"] and set(s["decision_stage"]) == {"design"})),
                               "operation": sum(1 for s in F if fn in s["dt_functions"] and "operation" in s["decision_stage"])}
                          for fn in ["monitoring_state_estimation", "prediction", "optimization_control"]}
# full text vs abstract sensitivity
FT = [s for s in F if s["text_basis"] == "full_text"]; AB = [s for s in F if s["text_basis"] != "full_text"]
SENS = {
 "temporal_resolution_reported": lambda s: s["temporal_resolution"] not in ("NR", "NA"),
 "data_duration_reported": lambda s: s["data_duration"] not in ("NR", "NA"),
 "deployment_reported": lambda s: not set(s["deployment"]) <= {"NR", "NA"} and bool(s["deployment"]),
 "validation_reported": lambda s: s["validation_setting"] != "none",
 "field_validation": lambda s: s["validation_setting"].startswith("field"),
 "realtime_demo": lambda s: s["real_time"] == "real_time_operation_demonstrated",
 "open_data": lambda s: s["data_or_code_available"] == "yes_public",
 "ai": lambda s: s["ai_used"] == "yes",
 "shadow_or_twin": lambda s: s["dt_maturity"] in ("digital_shadow", "digital_twin"),
 "limitations_stated": lambda s: bool(s.get("limitations_stated")),
}
X["sens"] = {k: {"full": share(FT, f), "abs": share(AB, f), "p": fisher(sum(1 for s in FT if f(s)), len(FT) - sum(1 for s in FT if f(s)), sum(1 for s in AB if f(s)), len(AB) - sum(1 for s in AB if f(s)))} for k, f in SENS.items()}
X["n_fulltext"] = len(FT); X["n_abstract"] = len(AB)
# venues and not-retrieved profile
X["venue_kind"] = cnt(F, "venue_kind")
nr = SC.get("not_retrieved", [])
pub = collections.Counter()
for r in nr:
    d = (R[r].get("doi") or "")
    pre = d.split("/")[0] if d else "no DOI"
    pub[{"10.1016": "Elsevier", "10.1007": "Springer", "10.1109": "IEEE", "10.3390": "MDPI", "10.1063": "AIP", "no DOI": "No DOI"}.get(pre, "Other")] += 1
X["not_retrieved_publishers"] = dict(pub.most_common())
X["n_not_retrieved"] = len(nr)
S["extra"] = X
json.dump(S, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k in ["physical_counterpart", "implementation_status", "coupling", "data_assimilation", "uncertainty_quantification", "koppen_B_subclass", "n_site_specific", "n_B", "cmp_ai", "cmp_field_validation", "n_operational", "indicators_operational", "not_retrieved_publishers", "venue_kind"]:
    print(k, X[k])
for k, v in X["sens"].items(): print("sens", k, v)
