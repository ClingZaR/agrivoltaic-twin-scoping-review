"""Compute synthesis tables from final coded studies. Usage: analyze.py final.json stats.json"""
import json, sys, collections, itertools
F = json.load(open(sys.argv[1], encoding="utf-8"))   # list of included study dicts with metadata merged
N = len(F)
def cnt(field, multi=True):
    c = collections.Counter()
    for s in F:
        v = s.get(field)
        if multi:
            for x in set(v or []): c[x] += 1
        else: c[v] += 1
    return dict(c.most_common())
def pct(n): return round(100 * n / N, 1)
S = {"N": N}
S["year"] = dict(sorted(collections.Counter(s.get("year") for s in F).items(), key=lambda kv: (kv[0] or 0)))
for f in ["study_type", "text_basis", "arid_focus", "mena", "dt_term_used", "dt_maturity", "ai_used", "temporal_resolution", "data_duration", "data_or_code_available", "real_time", "validation_setting"]:
    S[f] = cnt(f, multi=False)
for f in ["av_configuration", "koppen_main", "arid_constraints", "dt_functions", "decision_stage", "subsystems", "method_families", "ai_role", "data_types", "sensing_modalities", "deployment", "decision_timescale"]:
    S[f] = cnt(f)
CANON = {"usa": "United States", "us": "United States", "united states of america": "United States", "u.s.": "United States", "uk": "United Kingdom",
         "england": "United Kingdom", "scotland": "United Kingdom", "korea": "South Korea", "republic of korea": "South Korea", "uae": "United Arab Emirates",
         "the netherlands": "Netherlands", "holland": "Netherlands", "czechia": "Czech Republic", "türkiye": "Turkey", "turkiye": "Turkey", "kingdom of saudi arabia": "Saudi Arabia", "ksa": "Saudi Arabia"}
def canon(c):
    c = (c or "").strip()
    if c.lower() in ("", "nr", "none", "not reported", "na", "n/a", "generic", "not site-specific", "unspecified") or "not named" in c.lower() or "(" in c or len(c) > 40: return None
    return CANON.get(c.lower(), c)
for s in F:
    s["country"] = sorted(set(filter(None, (canon(c) for c in (s.get("country") or [])))))
cc = collections.Counter()
for s in F:
    for c in set(s.get("country") or []): cc[c] += 1
S["n_no_country"] = sum(1 for s in F if not s["country"])
S["country"] = dict(cc.most_common())
S["n_countries"] = len([c for c in cc if c.lower() not in ("none", "nr", "")])
S["venue_type"] = cnt("venue_kind", multi=False)
# cross-tabs
def xtab(f1, f2):
    t = collections.defaultdict(collections.Counter)
    for s in F:
        a = s.get(f1); b = s.get(f2)
        a = a if isinstance(a, list) else [a]; b = b if isinstance(b, list) else [b]
        for x in set(a):
            for y in set(b): t[x][y] += 1
    return {k: dict(v) for k, v in t.items()}
S["x_function_method"] = xtab("dt_functions", "method_families")
S["x_function_data"] = xtab("dt_functions", "data_types")
S["x_function_deploy"] = xtab("dt_functions", "deployment")
S["x_maturity_deploy"] = xtab("dt_maturity", "deployment")
S["x_maturity_realtime"] = xtab("dt_maturity", "real_time")
S["x_dtterm_maturity"] = xtab("dt_term_used", "dt_maturity")
S["x_ai_function"] = xtab("ai_used", "dt_functions")
S["x_ai_validation"] = xtab("ai_used", "validation_setting")
S["x_timescale_deploy"] = xtab("decision_timescale", "deployment")
S["x_subsystem_method"] = xtab("subsystems", "method_families")
S["x_aid_year"] = xtab("year", "ai_used")
# arid vs non-arid
ar = [s for s in F if s.get("arid_focus") == "explicit"]; nar = [s for s in F if s.get("arid_focus") != "explicit"]
def share(group, pred): return (sum(1 for s in group if pred(s)), len(group))
S["arid_compare"] = {
  "ai_used": [share(ar, lambda s: s["ai_used"] == "yes"), share(nar, lambda s: s["ai_used"] == "yes")],
  "field_validation": [share(ar, lambda s: s["validation_setting"].startswith("field")), share(nar, lambda s: s["validation_setting"].startswith("field"))],
  "multi_season": [share(ar, lambda s: s["data_duration"] == "multi_season_or_multi_year"), share(nar, lambda s: s["data_duration"] == "multi_season_or_multi_year")],
  "water_subsystem": [share(ar, lambda s: "water" in s["subsystems"]), share(nar, lambda s: "water" in s["subsystems"])],
  "soiling_subsystem": [share(ar, lambda s: "soiling" in s["subsystems"]), share(nar, lambda s: "soiling" in s["subsystems"])],
  "in_situ_sensors": [share(ar, lambda s: any(m in s["sensing_modalities"] for m in ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "iot_wireless_network"])), share(nar, lambda s: any(m in s["sensing_modalities"] for m in ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "iot_wireless_network"]))],
}
S["ai_methods_detail"] = [s.get("ai_methods_detail") for s in F if s.get("ai_used") == "yes"]
S["three_functions"] = sum(1 for s in F if len(set(s.get("dt_functions") or [])) == 3)
S["dt_term_and_twin"] = sum(1 for s in F if s.get("dt_term_used") == "yes" and s.get("dt_maturity") == "digital_twin")
json.dump(S, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k in ["N", "study_type", "arid_focus", "mena", "dt_maturity", "dt_term_used", "ai_used", "dt_functions", "method_families", "deployment", "real_time", "validation_setting", "koppen_main"]:
    print(k, S[k])
print("countries", list(S["country"].items())[:15])
print("arid_compare", S["arid_compare"])
