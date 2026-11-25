"""Compare blind abstract-only coding with full-text coding for the full-text studies.
Usage: calibration.py final.json blind_abstract_runs.json stats.json"""
import json, sys
sys.path.insert(0, sys.argv[2].rsplit("/", 1)[0] if False else "")
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "search"))
from parse_journal import load
F = {s["rid"]: s for s in json.load(open(sys.argv[1], encoding="utf-8"))}
o = load(sys.argv[2]); S = json.load(open(sys.argv[3], encoding="utf-8"))
B = {s["rid"]: s for v in o.values() for s in v["studies"]}
MEAS = ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]
FIELDS = {
 "Included on eligibility": lambda s: s["eligible"] == "INCLUDE",
 "AI used": lambda s: s["ai_used"] == "yes",
 "Digital shadow or twin": lambda s: s["dt_maturity"] in ("digital_shadow", "digital_twin"),
 "Operational decisions addressed": lambda s: "operation" in s["decision_stage"],
 "Specific real installation": lambda s: s.get("physical_counterpart") == "specific_installation",
 "Measured data used": lambda s: any(m in s["sensing_modalities"] for m in MEAS),
 "Field validation": lambda s: s["validation_setting"].startswith("field"),
 "Real-time operation demonstrated": lambda s: s["real_time"] == "real_time_operation_demonstrated",
 "Edge, fog, cloud, or multi-tier deployment": lambda s: any(d in s["deployment"] for d in ["edge_or_embedded", "cloud", "fog_or_gateway", "multi_tier"]),
 "Temporal resolution reported": lambda s: s["temporal_resolution"] not in ("NR", "NA"),
 "Measured data over more than one season": lambda s: s["data_duration"] == "multi_season_or_multi_year" and any(m in s["sensing_modalities"] for m in MEAS),
 "Two-way or integrated coupling": lambda s: s.get("coupling") == "two_way_or_integrated",
 "Data or code shared": lambda s: s["data_or_code_available"] == "yes_public",
}
common = [r for r in B if r in F]
out = {}
for name, f in FIELDS.items():
    if name == "Included on eligibility":
        a = sum(1 for r in common if f(B[r])); out[name] = {"full": len(common), "abs": a, "both": a, "n": len(common)}
        continue
    pairs = [(f(F[r]), f(B[r])) for r in common if B[r]["eligible"] == "INCLUDE"]
    n = len(pairs); tp = sum(1 for x, y in pairs if x and y); fpos = sum(1 for x, y in pairs if x); apos = sum(1 for x, y in pairs if y)
    agree = sum(1 for x, y in pairs if x == y)
    out[name] = {"n": n, "full": fpos, "abs": apos, "both": tp, "agree": agree}
S.setdefault("extra", {})["calib"] = out
S["extra"]["calib_n"] = len(common)
json.dump(S, open(sys.argv[3], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in out.items(): print(k, v)
