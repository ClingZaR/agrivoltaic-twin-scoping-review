"""Generated, data-ordered phrases for the manuscript template. Usage: phrases.py facts.json stats.json final.json themes.json  (updates facts.json)"""
import json, sys, collections
FA = json.load(open(sys.argv[1], encoding="utf-8")); S = json.load(open(sys.argv[2], encoding="utf-8"))
F = json.load(open(sys.argv[3], encoding="utf-8")); TH = json.load(open(sys.argv[4], encoding="utf-8"))
N = len(F)
def num(n): return f"{n:,}"
def pct(n, d=N): return f"{100 * n / d:.0f}"
def join(items):
    items = [i for i in items if i]
    if len(items) <= 1: return "".join(items)
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]
def ranked(counter, labels, keys=None, min_n=1, with_pct_first=True, d=N, unit=" studies"):
    pairs = [(k, counter.get(k, 0)) for k in (keys or labels)]
    pairs = [(k, n) for k, n in pairs if n >= min_n]
    pairs.sort(key=lambda kv: (-kv[1], list(labels).index(kv[0]) if kv[0] in labels else 99))
    out = []
    for i, (k, n) in enumerate(pairs):
        if i == 0 and with_pct_first: out.append(f"{labels[k]} ({num(n)}{unit}, {pct(n, d)}%)")
        else: out.append(f"{labels[k]} ({num(n)})")
    return pairs, out
P = {}
CFG = {"elevated": "elevated systems", "tracking_or_dynamic": "tracking or dynamic systems", "pv_greenhouse": "PV greenhouses", "vertical_bifacial": "vertical bifacial systems",
       "semi_transparent_or_spectral": "semi-transparent or spectrally selective modules", "interspace_ground_mounted": "interspace ground-mounted systems"}
_, o = ranked(S["av_configuration"], CFG, with_pct_first=False)
P["cfg_list"] = join(o)
KOP = {"C": "C, temperate", "B": "B, arid and semi-arid", "A": "A, tropical", "D": "D, continental", "E": "E, polar"}
pairs, o = ranked(S["koppen_main"], KOP)
P["kop_sentence"] = f"The most frequent class is {o[0]}, followed by {join(o[1:])}." if len(o) > 1 else f"The only class is {o[0]}."
arid = [s for s in F if s["arid_focus"] == "explicit"]
ac = collections.Counter(x for s in arid for x in set(s["arid_constraints"]) if x != "none")
AC = {"water_scarcity_irrigation": "water scarcity and irrigation", "heat_or_high_temperature": "heat or high temperature", "high_irradiance": "high irradiance",
      "dust_soiling": "dust and soiling", "salinity": "salinity"}
pairs, o = ranked(ac, AC, keys=[k for k in AC if k != "dust_soiling"], with_pct_first=False)
P["aridc_list"] = join(o)
P["salinity_sentence"] = ("No arid study considers salinity." if ac.get("salinity", 0) == 0 else
                          f"Salinity is considered in {num(ac['salinity'])} arid {'study' if ac['salinity'] == 1 else 'studies'}.")
a, d = S["arid_compare"]["ai_used"][0]
P["arid_ai_sentence"] = f"Only {num(a)} of the {num(d)} arid studies ({pct(a, d)}%) {'uses' if a == 1 else 'use'} AI"
MF = {"statistical": "statistical models", "rule_based_control": "rule-based control", "mathematical_programming": "mathematical programming",
      "metaheuristic_optimization": "metaheuristic optimization", "model_predictive_control": "model predictive control"}
pairs, o = ranked(S["method_families"], MF, with_pct_first=False)
P["other_methods_list"] = join(o)
AIF = {"deep_learning": "deep learning", "classical_ml": "classical machine learning", "hybrid_physics_ml": "hybrid physics and machine learning models", "reinforcement_learning": "reinforcement learning"}
pairs = sorted([(k, S["method_families"].get(k, 0)) for k in AIF], key=lambda kv: -kv[1])
nz = [(k, n) for k, n in pairs if n > 0]
zero = [AIF[k] for k, n in pairs if n == 0]
parts = []
for i, (k, n) in enumerate(nz):
    lab = AIF[k][0].upper() + AIF[k][1:] if i == 0 else AIF[k]
    parts.append(f"{lab} {'appears ' if i == 0 else ''}in {num(n)} {'study' if n == 1 else 'studies'}")
s = join(parts) + "." if parts else ""
if zero:
    s += f" No included study uses {join(zero)}."
P["ai_family_sentence"] = s.strip()
ai = [x for x in F if x["ai_used"] == "yes"]
yrs = sorted(x["year"] for x in ai if x.get("year"))
since = sum(1 for y in yrs if y >= 2024)
early = [y for y in yrs if y < 2020]
if early:
    P["ai_recency_sentence"] = (f"Apart from {num(len(early))} early {'study' if len(early) == 1 else 'studies'} ({join(sorted(set(map(str, early))))}), AI use is recent: "
                                f"{num(since)} of the {num(len(ai))} AI studies ({pct(since, len(ai))}%) were published from 2024 onward.")
else:
    P["ai_recency_sentence"] = f"AI use is recent: {num(since)} of the {num(len(ai))} AI studies ({pct(since, len(ai))}%) were published from 2024 onward."
AR = {"forecasting": "forecasting", "estimation_or_soft_sensing": "estimation or soft sensing", "classification_or_detection": "classification or detection",
      "surrogate_of_simulation": "surrogates of simulation models", "design_optimization": "design optimization", "control_or_decision": "control or decision"}
pairs, o = ranked(S["ai_role"], AR, with_pct_first=False)
P["ai_role_sentence"] = f"AI most often serves {o[0]}, followed by {join(o[1:])}." if len(o) > 1 else (f"AI serves {o[0]}." if o else "")
DT = {"simulated_synthetic": "simulated or synthetic data", "meteorological_irradiance": "meteorological and irradiance data", "crop_plant_measurements": "crop and plant measurements",
      "microclimate_under_array": "microclimate measurements under the array", "public_dataset_or_database": "public datasets or databases", "pv_electrical": "PV electrical data",
      "soil": "soil data", "remote_sensing": "remote sensing data"}
pairs, o = ranked(S["data_types"], DT)
P["data_sentence"] = f"The most frequent data type is {o[0]}, followed by {join(o[1:3])}. " + (f"Less frequent are {join(o[3:])}." if len(o) > 3 else "")
SM = {"in_situ_environmental_sensors": "in situ environmental sensors", "plant_sensors_or_manual_crop_sampling": "manual crop sampling or plant sensors",
      "pv_monitoring": "PV monitoring", "iot_wireless_network": "IoT or wireless sensor networks", "soil_sensors": "soil sensors",
      "imaging_rgb_multispectral_thermal": "imaging (RGB, multispectral, or thermal)", "satellite": "satellites", "uav": "UAVs"}
pairs, o = ranked(S["sensing_modalities"], SM, with_pct_first=False)
P["sensing_sentence"] = f"The most frequent modality is {o[0]}, followed by {join(o[1:4])}." + (f" Less frequent are {join(o[4:])}." if len(o) > 4 else "")
TR = {"minute_to_hourly": "minute to hourly", "sub_minute": "sub-minute", "daily": "daily", "coarser": "coarser than daily"}
pairs, o = ranked(S["temporal_resolution"], TR, with_pct_first=False)
P["tr_sentence"] = f"Among the studies that state a temporal resolution, the most frequent finest resolution is {o[0]}, followed by {join(o[1:])}." if len(o) > 1 else ""
DEP = {"edge_or_embedded": "edge or embedded deployment", "cloud": "cloud deployment", "multi_tier": "multi-tier architectures", "fog_or_gateway": "fog or gateway computing"}
pairs, o = ranked(S["deployment"], DEP, with_pct_first=False)
P["deploy_list"] = join(o)
TS = {"season_or_longer": "season or longer", "minutes_to_hours": "minutes to hours", "days_to_weeks": "days to weeks", "seconds_or_faster": "seconds or faster"}
pairs, o = ranked(S["decision_timescale"], TS, with_pct_first=False)
P["ts_sentence"] = f"The most frequent decision timescale is {o[0]}, followed by {join(o[1:])}."
inc = {x["rid"] for x in F}
Fm = {x["rid"]: x for x in F}
THf = {k: v for k, v in TH.items() if k in inc}
THf = {k: {"limitation_codes": v["limitation_codes"] if Fm[k].get("limitations_stated") else [], "future_codes": v["future_codes"] if Fm[k].get("future_work_stated") else []} for k, v in THf.items()}
LT = {"L2_model_simplification": "model simplification", "L6_missing_coupling": "missing coupling between processes", "L4_data_or_sensing": "data or sensing limitations",
      "L1_short_or_single_site": "short or single-site data", "L7_economic_or_practical": "economic or practical constraints", "L3_limited_transferability": "limited transferability",
      "L8_no_real_time_or_deployment": "no real-time operation or deployment", "L5_computational_cost": "computational cost"}
FT = {"F1_longer_multisite_validation": "longer and multi-site field validation", "F7_design_or_operation_optimization": "design or operation optimization",
      "F2_coupled_or_hybrid_models": "coupled or hybrid models", "F3_other_crops_climates_designs": "extension to other crops, climates, and designs",
      "F5_better_sensing_or_data": "better sensing and data", "F6_economics_or_lca": "economic or life-cycle analysis", "F4_real_time_control_or_twin": "real-time control or digital twins",
      "F8_improved_ai_methods": "improved AI methods"}
lc = collections.Counter(x for v in THf.values() for x in set(v["limitation_codes"]))
fc = collections.Counter(x for v in THf.values() for x in set(v["future_codes"]))
pairs, o = ranked(lc, LT, with_pct_first=False)
P["lim_sentence"] = f"The most frequent stated limitation is {o[0]}, followed by {join(o[1:4])}."
pairs, o = ranked(fc, FT, with_pct_first=False)
P["fut_sentence"] = f"The most frequent future direction is {o[0]}, followed by {join(o[1:4])}."
P["top_lim_list"] = join([LT[k] for k, _ in lc.most_common(3)])
FA.update(P)
# thousands separators for large counts used in text
for k, v in list(FA.items()):
    if k.startswith("n_") and isinstance(v, int) and v >= 1000:
        FA[k] = f"{v:,}"
json.dump(FA, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in P.items(): print(k, "=>", v)
