"""Derive named facts for the manuscript template.
Usage: facts.py final.json stats.json flow.json agree.json themes.json facts.json   (themes.json may be "-")"""
import json, sys, collections

F = json.load(open(sys.argv[1], encoding="utf-8"))
S = json.load(open(sys.argv[2], encoding="utf-8"))
FL = json.load(open(sys.argv[3], encoding="utf-8"))
AG = json.load(open(sys.argv[4], encoding="utf-8"))
TH = json.load(open(sys.argv[5], encoding="utf-8")) if sys.argv[5] != "-" else {}
N = len(F)


def p(n, d=None):
    d = N if d is None else d
    return f"{100 * n / d:.0f}" if d else "0"


def g(field, key):
    return S.get(field, {}).get(key, 0)


f = {"N": N}
f.update(FL)
yrs = [s["year"] for s in F if s.get("year")]
f["year_min"], f["year_max"] = min(yrs), max(yrs)
f["n_since_2022"] = sum(1 for y in yrs if y >= 2022); f["pct_since_2022"] = p(f["n_since_2022"])
f["n_2025_2026"] = sum(1 for y in yrs if y >= 2025); f["pct_2025_2026"] = p(f["n_2025_2026"])
f["n_journal"] = sum(1 for s in F if s["venue_kind"] == "journal"); f["n_conf"] = N - f["n_journal"]
for k, short in [("simulation_modeling", "sim"), ("field_experiment_with_model", "fe"), ("system_development", "sys"),
                 ("data_driven_model", "dd"), ("mixed", "mixed")]:
    f[f"n_{short}"] = g("study_type", k); f[f"pct_{short}"] = p(f[f"n_{short}"])
for k in ["full_text", "abstract_only"]:
    f[f"n_{k}"] = g("text_basis", k); f[f"pct_{k}"] = p(f[f"n_{k}"])
for k in ["elevated", "interspace_ground_mounted", "vertical_bifacial", "tracking_or_dynamic", "pv_greenhouse", "grazing",
          "semi_transparent_or_spectral", "generic_or_unspecified"]:
    f[f"n_cfg_{k}"] = g("av_configuration", k); f[f"pct_cfg_{k}"] = p(f[f"n_cfg_{k}"])
# RQ1
f["n_countries"] = S["n_countries"]; f["n_no_country"] = S["n_no_country"]; f["pct_no_country"] = p(S["n_no_country"])
top = list(S["country"].items())
f["top_countries"] = ", ".join(f"{c} ({n})" for c, n in top[:8])
for k in "ABCDE":
    f[f"n_kop_{k}"] = g("koppen_main", k); f[f"pct_kop_{k}"] = p(f[f"n_kop_{k}"])
f["n_kop_NR"] = g("koppen_main", "NR"); f["pct_kop_NR"] = p(f["n_kop_NR"])
for k in ["explicit", "motivation_only", "none"]:
    f[f"n_arid_{k}"] = g("arid_focus", k); f[f"pct_arid_{k}"] = p(f[f"n_arid_{k}"])
f["n_mena"] = g("mena", "yes"); f["pct_mena"] = p(f["n_mena"])
MENA = {"Algeria", "Bahrain", "Djibouti", "Egypt", "Iran", "Iraq", "Israel", "Jordan", "Kuwait", "Lebanon", "Libya", "Malta", "Morocco", "Oman",
        "Palestine", "Qatar", "Saudi Arabia", "Syria", "Tunisia", "United Arab Emirates", "Yemen"}
mena_c = collections.Counter(c for s in F for c in s["country"] if c in MENA)
f["n_mena_by_country"] = sum(1 for s in F if any(c in MENA for c in s["country"]))
f["mena_countries"] = ", ".join(f"{c} ({n})" for c, n in mena_c.most_common())
arid = [s for s in F if s["arid_focus"] == "explicit"]
f["n_arid"] = len(arid)
ac = collections.Counter(x for s in arid for x in set(s["arid_constraints"]) if x != "none")
for k in ["water_scarcity_irrigation", "heat_or_high_temperature", "dust_soiling", "high_irradiance", "salinity"]:
    f[f"n_aridc_{k}"] = ac.get(k, 0); f[f"pct_aridc_{k}"] = p(ac.get(k, 0), len(arid))
for name, (a, b) in S["arid_compare"].items():
    f[f"arid_{name}_n"], f[f"arid_{name}_d"] = a; f[f"arid_{name}_pct"] = p(*a)
    f[f"nonarid_{name}_n"], f[f"nonarid_{name}_d"] = b; f[f"nonarid_{name}_pct"] = p(*b)
f["n_soiling_all"] = g("subsystems", "soiling"); f["pct_soiling_all"] = p(f["n_soiling_all"])
# RQ2
for k in ["physics_based", "statistical", "classical_ml", "deep_learning", "reinforcement_learning", "metaheuristic_optimization",
          "mathematical_programming", "model_predictive_control", "hybrid_physics_ml", "rule_based_control", "none"]:
    f[f"n_m_{k}"] = g("method_families", k); f[f"pct_m_{k}"] = p(f[f"n_m_{k}"])
f["n_ai"] = g("ai_used", "yes"); f["pct_ai"] = p(f["n_ai"])
ai = [s for s in F if s["ai_used"] == "yes"]
f["ai_first_year"] = min(s["year"] for s in ai if s.get("year")) if ai else ""
f["n_ai_since_2024"] = sum(1 for s in ai if (s.get("year") or 0) >= 2024); f["pct_ai_since_2024"] = p(f["n_ai_since_2024"], len(ai))
for k in ["surrogate_of_simulation", "forecasting", "estimation_or_soft_sensing", "classification_or_detection", "control_or_decision",
          "design_optimization"]:
    f[f"n_air_{k}"] = g("ai_role", k)
for k in ["monitoring_state_estimation", "prediction", "optimization_control"]:
    f[f"n_f_{k}"] = g("dt_functions", k); f[f"pct_f_{k}"] = p(f[f"n_f_{k}"])
f["n_three_functions"] = S["three_functions"]; f["pct_three_functions"] = p(S["three_functions"])
for k in ["design", "operation"]:
    f[f"n_stage_{k}"] = g("decision_stage", k); f[f"pct_stage_{k}"] = p(f[f"n_stage_{k}"])
for k in ["light_shading", "pv_energy", "crop", "microclimate", "water", "soiling", "economics"]:
    f[f"n_sub_{k}"] = g("subsystems", k); f[f"pct_sub_{k}"] = p(f[f"n_sub_{k}"])
nsub = [len(set(s["subsystems"]) - {"economics"}) for s in F]
f["n_sub_3plus"] = sum(1 for x in nsub if x >= 3); f["pct_sub_3plus"] = p(f["n_sub_3plus"])
f["n_light_crop_pv"] = sum(1 for s in F if {"light_shading", "crop", "pv_energy"} <= set(s["subsystems"]))
f["pct_light_crop_pv"] = p(f["n_light_crop_pv"])
f["n_light_crop_pv_water"] = sum(1 for s in F if {"light_shading", "crop", "pv_energy", "water"} <= set(s["subsystems"]))
# RQ3
for k in ["meteorological_irradiance", "pv_electrical", "crop_plant_measurements", "soil", "microclimate_under_array", "remote_sensing",
          "simulated_synthetic", "public_dataset_or_database", "NR"]:
    f[f"n_d_{k}"] = g("data_types", k); f[f"pct_d_{k}"] = p(f[f"n_d_{k}"])
MEAS = ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling",
        "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]
for k in MEAS + ["none", "NR"]:
    f[f"n_s_{k}"] = g("sensing_modalities", k); f[f"pct_s_{k}"] = p(f[f"n_s_{k}"])
meas = [s for s in F if any(m in s["sensing_modalities"] for m in MEAS)]
f["n_measured"] = len(meas); f["pct_measured"] = p(len(meas))
for k in ["sub_minute", "minute_to_hourly", "daily", "coarser", "NR", "NA"]:
    f[f"n_tr_{k}"] = g("temporal_resolution", k); f[f"pct_tr_{k}"] = p(f[f"n_tr_{k}"])
for k in ["less_than_one_season", "one_season_or_year", "multi_season_or_multi_year", "NR", "NA"]:
    f[f"n_dur_{k}"] = g("data_duration", k); f[f"pct_dur_{k}"] = p(f[f"n_dur_{k}"])
f["n_meas_multi"] = sum(1 for s in meas if s["data_duration"] == "multi_season_or_multi_year")
f["pct_meas_multi"] = p(f["n_meas_multi"], len(meas))
f["n_open"] = g("data_or_code_available", "yes_public"); f["pct_open"] = p(f["n_open"])
# RQ4
for k in ["offline_desktop_or_server", "cloud", "edge_or_embedded", "fog_or_gateway", "multi_tier", "NR", "NA"]:
    f[f"n_dep_{k}"] = g("deployment", k); f[f"pct_dep_{k}"] = p(f[f"n_dep_{k}"])
for k in ["real_time_operation_demonstrated", "designed_for_real_time", "offline", "NR"]:
    f[f"n_rt_{k}"] = g("real_time", k); f[f"pct_rt_{k}"] = p(f[f"n_rt_{k}"])
for k in ["seconds_or_faster", "minutes_to_hours", "days_to_weeks", "season_or_longer"]:
    f[f"n_ts_{k}"] = g("decision_timescale", k); f[f"pct_ts_{k}"] = p(f[f"n_ts_{k}"])
for k in ["digital_model", "digital_shadow", "digital_twin", "NA"]:
    f[f"n_dt_{k}"] = g("dt_maturity", k); f[f"pct_dt_{k}"] = p(f[f"n_dt_{k}"])
f["n_dt_term"] = g("dt_term_used", "yes")
f["n_dt_term_twin"] = S["dt_term_and_twin"]
for k in ["none", "simulation_benchmark_only", "field_measurements_single_site", "field_measurements_multi_site", "laboratory_or_prototype"]:
    f[f"n_val_{k}"] = g("validation_setting", k); f[f"pct_val_{k}"] = p(f[f"n_val_{k}"])
f["n_val_field"] = f["n_val_field_measurements_single_site"] + f["n_val_field_measurements_multi_site"]
f["pct_val_field"] = p(f["n_val_field"])
ai_val = [s for s in ai if s["validation_setting"].startswith("field")]
f["n_ai_field"] = len(ai_val); f["pct_ai_field"] = p(len(ai_val), len(ai))
# themes
if TH:
    inc = {s["rid"] for s in F}
    Fm = {x["rid"]: x for x in F}
    TH = {k: v for k, v in TH.items() if k in inc}
    TH = {k: {"limitation_codes": v["limitation_codes"] if Fm[k].get("limitations_stated") else [], "future_codes": v["future_codes"] if Fm[k].get("future_work_stated") else []} for k, v in TH.items()}
    lc = collections.Counter(x for v in TH.values() for x in set(v["limitation_codes"]))
    fc = collections.Counter(x for v in TH.values() for x in set(v["future_codes"]))
    nl = sum(1 for v in TH.values() if v["limitation_codes"]); nf = sum(1 for v in TH.values() if v["future_codes"])
    f["n_with_lim"] = nl; f["n_with_fut"] = nf
    f["pct_with_lim"] = p(nl); f["pct_with_fut"] = p(nf)
    for k, v in lc.items():
        f[f"n_{k}"] = v; f[f"pct_{k}"] = p(v, nl)
    for k, v in fc.items():
        f[f"n_{k}"] = v; f[f"pct_{k}"] = p(v, nf)
for k, v in AG.items():
    if isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
        f[f"agree_{k}"] = f"{100 * v[0]:.0f}"; f[f"kappa_{k}"] = f"{v[1]:.2f}"
    elif isinstance(v, (int, float)):
        f[f"ag_{k}"] = f"{v:.2f}" if isinstance(v, float) else v
json.dump(f, open(sys.argv[6], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(f), "facts")
