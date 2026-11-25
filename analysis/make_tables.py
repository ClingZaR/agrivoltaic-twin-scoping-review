"""Build results tables (JSON specs for build_docx) and figures 2-3.
Usage: make_tables.py final.json stats.json facts.json themes.json static_tables.json out_tables.json figdir"""
import json, sys, os, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

F = json.load(open(sys.argv[1], encoding="utf-8")); S = json.load(open(sys.argv[2], encoding="utf-8"))
FA = json.load(open(sys.argv[3], encoding="utf-8")); TH = json.load(open(sys.argv[4], encoding="utf-8"))
T = json.load(open(sys.argv[5], encoding="utf-8")); figdir = sys.argv[7]
X = S.get("extra", {})
N = len(F)
def pc(n, d=N):
    if not d: return "0"
    v = 100 * n / d
    return "<1" if 0 < v < 0.5 else f"{v:.0f}"
def row(label, n, d=N): return [label, str(n), pc(n, d)]
LAB = {
 "simulation_modeling": "Simulation and modeling", "field_experiment_with_model": "Field experiment with a model", "system_development": "System development",
 "data_driven_model": "Data-driven model", "mixed": "Mixed", "elevated": "Elevated", "interspace_ground_mounted": "Interspace, ground-mounted",
 "vertical_bifacial": "Vertical bifacial", "tracking_or_dynamic": "Tracking or dynamic", "pv_greenhouse": "PV greenhouse", "grazing": "Grazing",
 "semi_transparent_or_spectral": "Semi-transparent or spectrally selective", "generic_or_unspecified": "Generic or unspecified",
 "full_text": "Full text", "abstract_only": "Title and abstract",
 "physics_based": "Physics-based", "statistical": "Statistical", "classical_ml": "Classical machine learning", "deep_learning": "Deep learning",
 "reinforcement_learning": "Reinforcement learning", "metaheuristic_optimization": "Metaheuristic optimization", "mathematical_programming": "Mathematical programming",
 "model_predictive_control": "Model predictive control", "hybrid_physics_ml": "Hybrid physics and machine learning", "rule_based_control": "Rule-based control", "none": "None",
 "monitoring_state_estimation": "Monitoring and state estimation", "prediction": "Prediction", "optimization_control": "Optimization and control",
 "meteorological_irradiance": "Meteorological and irradiance", "pv_electrical": "PV electrical", "crop_plant_measurements": "Crop and plant measurements",
 "soil": "Soil", "microclimate_under_array": "Microclimate under the array", "remote_sensing": "Remote sensing", "simulated_synthetic": "Simulated or synthetic",
 "public_dataset_or_database": "Public dataset or database", "NR": "Not reported", "NA": "Not applicable",
 "in_situ_environmental_sensors": "In situ environmental sensors", "soil_sensors": "Soil sensors", "pv_monitoring": "PV monitoring",
 "plant_sensors_or_manual_crop_sampling": "Plant sensors or manual crop sampling", "imaging_rgb_multispectral_thermal": "Imaging (RGB, multispectral, or thermal)",
 "satellite": "Satellite", "uav": "UAV", "iot_wireless_network": "IoT or wireless sensor network",
 "sub_minute": "Sub-minute", "minute_to_hourly": "Minute to hourly", "daily": "Daily", "coarser": "Coarser than daily",
 "less_than_one_season": "Less than one season", "one_season_or_year": "One season or year", "multi_season_or_multi_year": "More than one season or year",
 "offline_desktop_or_server": "Offline desktop or server", "cloud": "Cloud", "edge_or_embedded": "Edge or embedded", "fog_or_gateway": "Fog or gateway", "multi_tier": "Multi-tier",
 "real_time_operation_demonstrated": "Real-time operation demonstrated", "designed_for_real_time": "Designed for real time, not demonstrated", "offline": "Offline",
 "seconds_or_faster": "Seconds or faster", "minutes_to_hours": "Minutes to hours", "days_to_weeks": "Days to weeks", "season_or_longer": "Season or longer",
 "digital_model": "Digital model", "digital_shadow": "Digital shadow", "digital_twin": "Digital twin",
 "field_measurements_single_site": "Field measurements, one site", "field_measurements_multi_site": "Field measurements, several sites",
 "simulation_benchmark_only": "Comparison with another model only", "laboratory_or_prototype": "Laboratory or prototype",
 "operating_installation": "Operating installation", "prototype_or_testbed": "Prototype or testbed", "concept_or_proposal": "Concept or proposal",
 "specific_installation": "Specific real installation", "generic_design": "Generic or planned design",
 "single_subsystem": "Single subsystem", "parallel_uncoupled": "Several subsystems, not coupled", "one_way": "One-way coupling", "two_way_or_integrated": "Two-way or integrated coupling",
 "sequential_updating": "Repeated updating from measurements", "calibration_only": "One-time calibration",
}
def block(title, field, keys=None, d=N, src=None):
    out = [[f"**{title}**", "", ""]]
    c = (src or S)[field]
    items = list(c.items()) if keys is None else [(k, c.get(k, 0)) for k in keys]
    if keys is None:
        items = [kv for kv in items if kv[0] not in ("NR", "NA", "none", "generic_or_unspecified")] + [kv for kv in items if kv[0] in ("generic_or_unspecified", "none", "NR", "NA")]
    for k, v in items:
        if keys is None and k in ("NA",) and v == 0:
            continue
        out.append(row(LAB.get(k, k), v, d))
    return out
H = ["Category", "Studies", "%"]
W3 = [5, 1.2, 1]
# T5 calibration: abstract-only coding versus full-text coding of the same studies
def pfmt(p): return "<0.001" if p < 0.001 else (f"{p:.2f}" if p >= 0.01 else f"{p:.3f}")
CAL = X.get("calib", {})
rows = []
for k, v in CAL.items():
    if k == "Included on eligibility":
        rows.append([k, str(v["full"]), str(v["abs"]), f"{100 * v['abs'] / v['full']:.0f}%", "–"]); continue
    se = f"{100 * v['both'] / v['full']:.0f}%" if v["full"] else "–"
    rows.append([k, str(v["full"]), str(v["abs"]), se, f"{100 * v['agree'] / v['n']:.0f}%"])
T["T5_sensitivity"] = {"caption": "Table 5 Coding From Abstracts Compared With Coding From Full Texts for the Same Studies", "header": ["Field", "Positive from full text", "Positive from abstract", "Share detected from abstract", "Agreement"],
    "widths": [3.4, 1.3, 1.3, 1.4, 1.1], "rows": rows,
    "note": f"The {X.get('calib_n', 91)} studies charted from full text were re-charted from their titles and abstracts alone by a coding run blind to the full-text codes. Except for the first row, counts refer to the studies included on both bases. Share detected = studies positive on both bases divided by studies positive from full text."}
# T6 characteristics
T["T6_characteristics"] = {"caption": "Table 6 Characteristics of the Included Studies", "header": H, "widths": W3,
    "rows": block("Study type", "study_type") + block("Agrivoltaic configuration", "av_configuration") +
            block("Physical counterpart", "physical_counterpart", ["specific_installation", "generic_design", "NA"], src=X) + block("Text basis for charting", "text_basis"),
    "note": f"N = {N}. Configurations are multi-valued, so their percentages can sum to more than 100%."}
# T7 climate
kop_lab = {"A": "A, tropical", "B": "B, arid and semi-arid", "C": "C, temperate", "D": "D, continental", "E": "E, polar", "NR": "Not reported or not site-specific"}
rows = [["**Köppen-Geiger main class**", "", ""]] + [row(kop_lab[k], S["koppen_main"].get(k, 0)) for k in ["A", "B", "C", "D", "E", "NR"] if S["koppen_main"].get(k, 0) or k != "E"]
sub = X.get("koppen_B_subclass", {})
if sub:
    rows += [["**Arid subclasses**", "", ""]]
    SL = {"BWh": "BWh, hot desert", "BWk": "BWk, cold desert", "BSh": "BSh, hot steppe", "BSk": "BSk, cold steppe", "B": "B, subclass not assigned"}
    for k in ["BWh", "BSh", "BWk", "BSk", "B"]:
        if sub.get(k): rows.append(row(SL[k], sub[k]))
rows += [["**Arid focus**", "", ""], row("Arid site or arid target", S["arid_focus"].get("explicit", 0)),
         row("Motivation only", S["arid_focus"].get("motivation_only", 0)), row("None", S["arid_focus"].get("none", 0)),
         ["**MENA site**", "", ""], row("At least one site in the MENA region", FA["n_mena_by_country"])]
rows += [["**Most frequent countries**", "", ""]] + [row(c, n) for c, n in list(S["country"].items())[:10]]
T["T7_climate"] = {"caption": "Table 7 Study Sites by Climate, Arid Focus, and Country", "header": H, "widths": W3, "rows": rows,
    "note": f"N = {N}. Studies with sites in several climates, subclasses, or countries are counted in each row, so rows can overlap; {FA.get('n_hot_arid', '')} studies have a hot arid site and {FA.get('n_cold_arid', '')} a cold arid site."}
# T8 methods x functions (with operational split)
FN = ["monitoring_state_estimation", "prediction", "optimization_control"]
MF = ["physics_based", "statistical", "classical_ml", "deep_learning", "hybrid_physics_ml", "reinforcement_learning", "metaheuristic_optimization",
      "mathematical_programming", "model_predictive_control", "rule_based_control"]
x = S["x_function_method"]
rows = []
for m in MF:
    tot = S["method_families"].get(m, 0)
    if tot == 0 and m != "reinforcement_learning":
        continue
    rows.append([LAB[m], str(tot)] + [str(x.get(fn, {}).get(m, 0)) for fn in FN])
rows.append(["**All studies**", str(N)] + [str(S["dt_functions"].get(fn, 0)) for fn in FN])
fbs = X["function_by_stage"]
rows.append(["**Of which address operational decisions**", str(X["n_operational"])] + [str(fbs[fn]["operation"]) for fn in FN])
T["T8_methods_functions"] = {"caption": "Table 8 Method Families by Digital Twin Function", "header": ["Method family", "Studies", "Monitoring and state estimation", "Prediction", "Optimization and control"],
    "widths": [3.2, 1, 1.6, 1.3, 1.6], "rows": rows,
    "note": f"N = {N}. Cells give the number of studies that use the method family and address the function. Studies can use several method families and address several functions. AI is used in {FA['n_ai']} studies ({FA['pct_ai']}%): classical machine learning, deep learning, reinforcement learning, or hybrid physics and machine learning."}
T["T9_data"] = {"caption": "Table 9 Data Types, Sensing Modalities, and Temporal Properties", "header": H, "widths": W3,
    "rows": block("Data type", "data_types") + block("Sensing modality", "sensing_modalities") +
            block("Finest temporal resolution", "temporal_resolution", ["sub_minute", "minute_to_hourly", "daily", "coarser", "NR", "NA"]) +
            block("Data duration", "data_duration", ["less_than_one_season", "one_season_or_year", "multi_season_or_multi_year", "NR", "NA"]) +
            [["**Data or code shared publicly**", str(FA["n_open"]), FA["pct_open"]]],
    "note": f"N = {N}. Data types and sensing modalities are multi-valued and were coded separately, so their counts can differ (for example, remote sensing data and satellite or UAV sensing). Data duration covers all data, including simulated multi-year runs. Not reported is shown separately from not applicable."}
T["T10_deployment"] = {"caption": "Table 10 Computing, Deployment, Decision Timescale, Digital Twin Level, and Validation", "header": H, "widths": W3,
    "rows": block("Deployment", "deployment") + block("Real-time operation", "real_time", ["real_time_operation_demonstrated", "designed_for_real_time", "offline", "NR"]) +
            block("Decision timescale", "decision_timescale", ["seconds_or_faster", "minutes_to_hours", "days_to_weeks", "season_or_longer"]) +
            block("Digital twin level", "dt_maturity", ["digital_model", "digital_shadow", "digital_twin", "NA"]) +
            block("Implementation status", "implementation_status", ["operating_installation", "prototype_or_testbed", "concept_or_proposal", "NA"], src=X) +
            block("Model updating from measurements", "data_assimilation", ["sequential_updating", "calibration_only", "none"], src=X) +
            block("Validation setting", "validation_setting", ["field_measurements_single_site", "field_measurements_multi_site", "laboratory_or_prototype", "simulation_benchmark_only", "none"]),
    "note": f"N = {N}. Deployment and decision timescale are multi-valued, so a study can appear under several tiers; a multi-tier architecture can be coded together with the tiers it combines. Offline was coded for models run offline, including simulation studies that report no deployment. Digital twin levels follow Kritzinger et al. {{Kritzinger2018}}; Not applicable marks sensing or control systems without a virtual model, and, for implementation status, pure simulations or analyses with no system to implement. A validation setting of none means that no validation is reported."}
# T11 twins
tw = [s for s in F if s["dt_maturity"] in ("digital_shadow", "digital_twin")]
tw.sort(key=lambda s: (s["dt_maturity"] != "digital_twin", s.get("year") or 0))
rows = []
for s in tw:
    rows.append([f"{{{s['rid']}}}", str(s.get("year") or ""), LAB[s["dt_maturity"]], LAB.get(s.get("implementation_status"), s.get("implementation_status") or "Not reported"),
                 ", ".join(LAB.get(f, f) for f in s["dt_functions"]) or "Not reported", s["one_line_summary"]])
T["T11_twins"] = {"caption": "Table 11 Included Studies at the Digital Shadow and Digital Twin Levels", "header": ["Study", "Year", "Level", "Implementation", "Functions", "Summary"],
    "widths": [0.8, 0.6, 1.0, 1.3, 1.6, 4.0], "rows": rows,
    "note": "Levels were coded twice independently under explicit decision rules and adjudicated; they reflect the data flow described in each study, not the authors' terminology."}
# T12 operational subset
IL = {"specific_installation": "Models or instruments a specific installation", "measured_data": "Uses measured data", "multi_season": "Data over more than one season",
      "field_validation": "Field validation", "ai": "AI used", "coupled": "Subsystems coupled (one-way or two-way)", "two_way": "Two-way or integrated coupling",
      "calibration": "Model calibrated or updated from measurements", "assimilation": "Model updated repeatedly from measurements", "uq": "Uncertainty quantified",
      "realtime_demo": "Real-time operation demonstrated", "online_tier": "Edge, fog, cloud, or multi-tier deployment", "shadow_or_twin": "Digital shadow or twin", "open_data": "Data or code shared"}
IL["multi_season"] = "Measured data over more than one season"; IL["calibration"] = "Model calibrated against measurements"
io, idd, ip = X["indicators_operational"], X["indicators_design"], X["indicators_p"]
rows = [[lab, f"{io[k][0]} ({pc(*io[k])}%)", f"{idd[k][0]} ({pc(*idd[k])}%)", pfmt(ip[k]) if (io[k][0] + idd[k][0]) else "–"] for k, lab in IL.items()]
T["T12_operational"] = {"caption": "Table 12 Twin-Relevant Indicators for Studies Addressing Operational Decisions and for Design-Only Studies", "header": ["Indicator", f"Operational decisions (n = {X['n_operational']})", f"Design only (n = {X['n_design_only']})", "p"],
    "widths": [3.8, 1.8, 1.7, 0.8], "rows": rows, "note": "Operational decisions include tracking, irrigation, cleaning, scheduling, and fault detection during operation; design-only studies address only design-stage decisions. p = two-sided Fisher's exact test, reported descriptively without correction for multiple comparisons."}
# T13 themes
LT = {"L2_model_simplification": "Model simplification or idealized assumptions", "L6_missing_coupling": "Processes not coupled or not all considered",
      "L4_data_or_sensing": "Data or sensing limitations", "L1_short_or_single_site": "Short, single-season, or single-site data",
      "L7_economic_or_practical": "Economic or practical constraints not addressed", "L3_limited_transferability": "Results specific to one crop, climate, or design",
      "L8_no_real_time_or_deployment": "No real-time operation or deployment", "L5_computational_cost": "Computational cost"}
FT = {"F1_longer_multisite_validation": "Longer or multi-site field validation", "F7_design_or_operation_optimization": "Design or operation optimization",
      "F2_coupled_or_hybrid_models": "Coupled or hybrid physics and machine learning models", "F3_other_crops_climates_designs": "Other crops, climates, or designs",
      "F5_better_sensing_or_data": "Better sensing, monitoring, or data sharing", "F6_economics_or_lca": "Economic or life-cycle analysis",
      "F4_real_time_control_or_twin": "Real-time control, automation, or digital twin", "F8_improved_ai_methods": "Improved AI methods"}
inc = {s["rid"] for s in F}
Fm = {x["rid"]: x for x in F}
THf = {k: v for k, v in TH.items() if k in inc}
THf = {k: {"limitation_codes": v["limitation_codes"] if Fm[k].get("limitations_stated") else [], "future_codes": v["future_codes"] if Fm[k].get("future_work_stated") else []} for k, v in THf.items()}
lc = collections.Counter(x for v in THf.values() for x in set(v["limitation_codes"]))
fc = collections.Counter(x for v in THf.values() for x in set(v["future_codes"]))
nl = sum(1 for v in THf.values() if v["limitation_codes"]); nf = sum(1 for v in THf.values() if v["future_codes"])
rows = [["**Stated limitations**", "", ""]] + [[LT[k], str(v), pc(v, nl)] for k, v in lc.most_common()]
rows += [["**Stated future work**", "", ""]] + [[FT[k], str(v), pc(v, nf)] for k, v in fc.most_common()]
T["T13_themes"] = {"caption": "Table 13 Limitations and Future Work Stated by the Study Authors", "header": ["Theme", "Studies", "%"], "widths": W3, "rows": rows,
    "note": f"Percentages refer to the {nl} studies that state at least one limitation and the {nf} studies that state future work in the text available for charting. A study can have several themes."}
# T14 architecture with three evidence columns
def n_where(pred): return sum(1 for s in F if pred(s))
def has(s, *m): return any(x in s["method_families"] for x in m)
def dep(s, *d): return any(x in s["deployment"] for x in d)
op = lambda s: "operation" in s["decision_stage"]
MEAS3 = ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]
ARCH = [
 ("Tracker and actuator set-points", "Minutes", "Plane-of-array irradiance, tracker angle, PV electrical output (IEC 61724-1 channels), wind", "Rule-based control, model predictive control, light and PV models; fallback set-points when data or communication fail", "Edge",
  lambda s: op(s) and "optimization_control" in s["dt_functions"] and ("minutes_to_hours" in s["decision_timescale"] or "seconds_or_faster" in s["decision_timescale"]),
  lambda s: has(s, "rule_based_control", "model_predictive_control", "physics_based"), lambda s: dep(s, "edge_or_embedded", "multi_tier")),
 ("State estimation of light and microclimate under the array", "Minutes to hours", "Global and diffuse irradiance; PAR at crop height at several positions across the row; air and module temperature, humidity, wind; the same variables on an open-field reference plot", "Ray-tracing or view-factor models, ideally updated by data assimilation; machine learning surrogates", "Fog or gateway",
  lambda s: "monitoring_state_estimation" in s["dt_functions"], lambda s: has(s, "physics_based", "hybrid_physics_ml", "deep_learning", "classical_ml"), lambda s: dep(s, "fog_or_gateway", "multi_tier")),
 ("Short-term forecasting of energy, microclimate, and crop water demand", "Hours to days", "Weather forecasts and the measured history of the streams above", "Machine learning or statistical forecasters combined with physics-based models", "Fog or gateway",
  lambda s: op(s) and "prediction" in s["dt_functions"], lambda s: has(s, "classical_ml", "deep_learning", "hybrid_physics_ml", "statistical"), lambda s: dep(s, "fog_or_gateway", "multi_tier")),
 ("Irrigation scheduling with a shared water balance", "Days", "Soil moisture at several depths, evapotranspiration under the panels, crop stage, irrigation water quality and salinity, irrigation and cleaning water use", "Crop and soil water balance models; machine learning yield and water models", "Fog or cloud",
  lambda s: "water" in s["subsystems"] and op(s), lambda s: has(s, "physics_based", "classical_ml", "deep_learning", "hybrid_physics_ml", "statistical"), lambda s: dep(s, "fog_or_gateway", "cloud", "multi_tier")),
 ("Heat stress of modules and crop (arid sites)", "Hours to days", "Module and canopy temperature, air temperature and humidity, greenhouse cooling water use", "Coupled thermal models of modules and canopy", "Fog or cloud",
  lambda s: "microclimate" in s["subsystems"] and "pv_energy" in s["subsystems"], lambda s: s.get("coupling") == "two_way_or_integrated", lambda s: dep(s, "fog_or_gateway", "cloud", "multi_tier")),
 ("Soiling detection and cleaning (arid sites)", "Days", "Soiling ratio or reference cells, airborne dust, PV output, cleaning water use", "Soiling loss models; machine learning detection", "Edge and cloud",
  lambda s: "soiling" in s["subsystems"] or "dust_soiling" in s["arid_constraints"], lambda s: "soiling" in s["subsystems"], lambda s: dep(s, "edge_or_embedded", "cloud", "multi_tier")),
 ("Design and seasonal planning", "Season or longer", "Typical meteorological year, crop parameters, layout and module options", "Coupled light, crop, PV, and water simulation; surrogate-based optimization", "Cloud or offline",
  lambda s: "design" in s["decision_stage"], lambda s: s.get("coupling") in ("one_way", "two_way_or_integrated"), lambda s: dep(s, "cloud", "offline_desktop_or_server")),
 ("Calibration and model learning", "Seasonal and continuous", "Multi-season measured data with sensor metadata and calibration records", "Parameter estimation, retraining, uncertainty quantification", "Cloud",
  lambda s: any(m in s["sensing_modalities"] for m in MEAS3), lambda s: s.get("data_assimilation") in ("calibration_only", "sequential_updating"), lambda s: dep(s, "cloud", "multi_tier")),
]
rows = []
for name, ts, data, models, tier, f_addr, f_model, f_tier in ARCH:
    addr = [s for s in F if f_addr(s)]
    rows.append([name, ts, data, models, tier, str(len(addr)), str(sum(1 for s in addr if f_model(s))), str(sum(1 for s in addr if f_model(s) and f_tier(s)))])
T["T14_architecture"] = {"caption": "Table 14 Proposed Reference Architecture: Digital Twin Functions Mapped to Timescales, Data, Models, and Computing Tiers, with the Supporting Evidence",
  "header": ["Function and decision", "Timescale", "Minimum data (proposed)", "Model types (proposed)", "Proposed tier", "Studies addressing", "With proposed model type", "Also at proposed tier"],
  "widths": [1.8, 1.0, 2.2, 1.9, 0.9, 0.8, 0.9, 0.8], "rows": rows,
  "note": "Definitions, by row. Studies addressing: (1) operational optimization or control at the scale of seconds to hours; (2) the monitoring and state estimation function; (3) prediction for operational decisions; (4) water modeled in an operational study; (5) microclimate and PV energy both modeled; (6) soiling modeled or dust considered; (7) design decisions; (8) measured data used. With proposed model type: (1) rule-based control, model predictive control, or a physics-based model; (2) a physics-based or machine learning model; (3) a statistical or machine learning model; (4) a physics-based, statistical, or machine learning model; (5) two-way or integrated coupling; (6) soiling modeled; (7) one-way or two-way coupling; (8) calibration or updating against measurements. Also at proposed tier: deployment reported at the proposed tier, where the fog tier includes multi-tier architectures. The architecture is a proposal; the counts show how far each element is supported by the corpus."}
json.dump(T, open(sys.argv[6], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(FA, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- Figure 2 ----------
plt.rcParams["font.family"] = "Arial"
def tier(s):
    m = set(s["method_families"])
    if s["ai_used"] == "yes": return "AI or machine learning"
    if m & {"statistical", "metaheuristic_optimization", "mathematical_programming", "model_predictive_control"}: return "Statistical or optimization"
    if "physics_based" in m: return "Physics-based only"
    return "Other (sensing, control, or rule-based)"
order = ["Physics-based only", "Statistical or optimization", "AI or machine learning", "Other (sensing, control, or rule-based)"]
cols = {"Physics-based only": "#9db4cc", "Statistical or optimization": "#5b7fa6", "AI or machine learning": "#c0504d", "Other (sensing, control, or rule-based)": "#c8c8c8"}
years = sorted({s["year"] for s in F if s.get("year")})
yrs = list(range(min(years), max(years) + 1))
cnt = {o: [sum(1 for s in F if s.get("year") == y and tier(s) == o) for y in yrs] for o in order}
fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200)
bottom = [0] * len(yrs)
for o in order:
    ax.bar(yrs, cnt[o], bottom=bottom, color=cols[o], label=o, width=0.8, edgecolor="white", linewidth=0.4)
    bottom = [a + b for a, b in zip(bottom, cnt[o])]
ax.set_ylabel("Included studies", fontsize=8); ax.tick_params(labelsize=7)
ax.set_xticks(yrs[::2] if len(yrs) > 12 else yrs); ax.spines[["top", "right"]].set_visible(False)
ax.legend(fontsize=7, frameon=False, loc="upper left")
ax.text(0.99, 0.97, f"{max(years)}: records to the search date", transform=ax.transAxes, ha="right", va="top", fontsize=6.5, color="#555555")
plt.tight_layout(); plt.savefig(os.path.join(figdir, "fig2_years.png"), facecolor="white"); plt.close()

# ---------- Figure 3: proposed reference architecture ----------
fig, ax = plt.subplots(figsize=(7.6, 6.6), dpi=200); ax.set_xlim(0, 100); ax.set_ylim(-6, 92); ax.axis("off")
def bx(x, y, w, h, title, lines, fc, fs=6.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", lw=0.8, ec="#333333", fc=fc))
    ax.text(x + 1.2, y + h - 2.0, title, fontsize=7.4, fontweight="bold", va="top")
    if lines:
        ax.text(x + 1.2, y + h - 5.0, chr(10).join(lines), fontsize=fs, va="top", linespacing=1.35)
def arr(x1, y1, x2, y2, c="#1f4e79", ls="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", lw=0.9, color=c, linestyle=ls))
bx(2, 66, 70, 24, "Cloud tier  (days to seasons)", ["F4-F5 seasonal re-planning of irrigation and heat management; F6 cleaning planning",
   "F7 design and seasonal planning with coupled light, crop, PV, and water models", "F8 parameter calibration and model retraining, with uncertainty",
   "Data archive with sensor metadata and calibration records"], "#e8eef6")
bx(76, 70, 22, 20, "External inputs", ["Weather forecasts", "Crop calendars", "(to the fog tier)"], "#f4f4f4")
bx(76, 18, 22, 15, "Governance (G)", ["Access control, audit trail,", "override records, data-", "sharing agreements; all", "tiers (IEC 62443)"], "#ececec")
bx(76, 36, 22, 28, "Operators", ["Farmer or landowner;", "PV owner or operator.", "In the loop: see dashboards", "and alerts, approve or", "override plans and", "set-points (fog, edge)"], "#fbf3e6")
bx(2, 40, 70, 22, "Fog or gateway tier  (minutes to days)", ["Time synchronization, unit conversion, and quality control of multi-rate streams",
   "F2 state estimation: light-model parameters (albedo, transmittance) corrected from the sensors", "F3 short-term forecasts of energy, microclimate, and crop water demand",
   "F9 daily light-sharing plan: tracking schedule against a crop light target (executed by F1)",
   "F4-F5 daily irrigation and heat plans, kept running when the cloud link fails; local buffering",
   "Coupled model core: shared light, crop, PV, and water state (F2-F5)"], "#eef3e8")
bx(2, 18, 70, 18, "Edge tier  (seconds to minutes)", ["F1 execution of tracker, valve, and cleaning set-points, with fallback values and safety stow limits",
   "F6 soiling detection from reference cells; data logging", "Inverter firmware runs maximum power point tracking (an input to the twin)",
   "Acts through the plant SCADA, tracker controller, and irrigation controller or climate computer"], "#f6f0e4")
bx(2, 0, 96, 14, "Physical agrivoltaic installation", ["PV array and trackers, crop and soil, irrigation and cleaning systems; an open-field reference plot",
   "Sensors: irradiance and PAR at several positions, air and module temperature, humidity, wind, soil moisture, PV output, soiling, crop imaging"], "#f3f3f3")
for xa in (22, 52):
    arr(xa, 14, xa, 18); arr(xa, 36, xa, 40); arr(xa, 62, xa, 66)
for xa in (30, 60):
    arr(xa, 18, xa, 14, "#c0504d"); arr(xa, 40, xa, 36, "#c0504d"); arr(xa, 66, xa, 62, "#c0504d")
arr(76, 76, 72, 56, "#555555")
arr(76, 48, 72, 48, "#c0504d"); arr(76, 40, 72, 28, "#c0504d")
ax.annotate("", xy=(66, 47.0), xytext=(66, 41.2), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="#1f4e79", connectionstyle="arc3,rad=-0.9"))
ax.text(54.0, 42.2, "state updating", fontsize=5.8, color="#1f4e79")
ax.annotate("", xy=(66, 73.0), xytext=(66, 67.2), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="#1f4e79", connectionstyle="arc3,rad=-0.9"))
ax.text(53.0, 68.2, "calibration loop", fontsize=5.8, color="#1f4e79")
ax.plot([3, 8], [-3.5, -3.5], color="#1f4e79", lw=1.2); ax.text(9, -3.5, "measurements and states (upward)", fontsize=6, va="center")
ax.plot([42, 47], [-3.5, -3.5], color="#c0504d", lw=1.2); ax.text(48, -3.5, "plans, set-points, and commands (downward)", fontsize=6, va="center")
ax.plot([80, 85], [-3.5, -3.5], color="#555555", lw=1.2); ax.text(86, -3.5, "external inputs", fontsize=6, va="center")
plt.savefig(os.path.join(figdir, "fig3_architecture.png"), bbox_inches="tight", facecolor="white"); plt.close()
print("tables and figures written")
