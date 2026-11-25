"""Apply the corrections found by the first author's check (Part A blind coding, Part B verification), adjudicated against the papers.
Overrides go into charts_all.json (ADJ) and mech_codes.json; every change is logged in hc_adjudications.json."""
import json, os
AN = os.path.dirname(os.path.abspath(__file__))
ALL = json.load(open(os.path.join(AN, "charts_all.json"), encoding="utf-8"))
M = json.load(open(os.path.join(AN, "mech_codes.json"), encoding="utf-8"))
LOG = []
def adj(rid, fields, why, part):
    ALL["ADJ"].setdefault(rid, {}).update(fields); LOG.append({"rid": rid, "part": part, "change": fields, "reason": why})
def mech(rid, fields, why, part):
    M[rid].update(fields); LOG.append({"rid": rid, "part": part, "change": {"model coding": fields}, "reason": why})
# Part A: the check's answer accepted after adjudication
adj("R2073", {"eligible": "EXCLUDE", "exclusion_code": "E1", "exclusion_reason": "Solar-powered electrocoagulation and pump unit for irrigation water; crop-side agrivoltaic effects are cited from literature, not modeled or measured (PV-powered farm equipment).", "elig_adjudicated": True},
    "Consistent with the exclusion of other PV-powered farm equipment found in the library round.", "A")
mech("R0644", {"validated_subsystems": ["crop"], "goodness_of_fit_reported": "yes", "validation_independent": "no"}, "The yield regression is compared with measured yield (MAE 0.04, RMSE 0.25 kg per m2) on the data it was fitted to.", "A")
mech("R2661", {"validated_subsystems": ["crop"], "validation_independent": "yes", "goodness_of_fit_reported": "no"}, "The crop sub-models are compared with published field campaigns on the same tracker geometry; the crop parameters were not fitted to them.", "A")
adj("R1808", {"decision_stage": ["design"]}, "Layouts are designed for a one-hectare vineyard; no operational decision is addressed.", "A")
adj("R0644", {"decision_stage": ["design"]}, "The result is a design trade-off (PV cover ratio), not an operational decision.", "A")
adj("R2509", {"decision_stage": []}, "The study calibrates and validates a crop model; decision support is only proposed.", "A")
adj("R1322", {"country": ["Netherlands"], "site_name": "Naaldwijk, Westland", "koppen_main": ["C"], "koppen_subclass": ["Cfb"]}, "A site is named (Naaldwijk, Netherlands, temperate oceanic).", "A")
# Part B: verification
adj("R2039", {"dt_demonstrated": "digital_model", "audit_reason": "Adjudicated after verification: the live MQTT link carries tracker-kit angles to a dashboard, and the pvlib model is run by the user with hand-set inputs for a clear-sky day, so installation data do not reach the model in the implementation; the design describes synchronisation, so the designed level stays a digital shadow."},
    "Part B: the demonstrated data flow reaches only a dashboard, not the model.", "B")
json.dump(ALL, open(os.path.join(AN, "charts_all.json"), "w"), ensure_ascii=False)
json.dump(M, open(os.path.join(AN, "mech_codes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
kept = [{"rid": r, "part": "A", "change": "none", "reason": why} for r, why in [
    ("R2317", "Validation cited from an earlier paper and comparison with county yield statistics do not count as the study's own validation."),
    ("R2668", "Comparison with district-level average yields is a plausibility check, not validation of the modeled field."),
    ("R2280", "Published yield-response relationships are compared with the study's own measurements, which counts as validation."),
    ("R1811", "The planned system includes tracking control of the PV modules, an operational decision."),
    ("R1423", "Golden, Colorado, the validation site, is classed as BSk (semi-arid)."),
    ("R0341", "Part B: crop yield was validated on independent data, but the water output was not, so the strict rule is still failed."),
    ("R2195", "Part B: water was validated on independent data, but crop was calibrated to the compared data, so the strict rule is still failed."),
    ("R1200", "Part B: the PV-output comparison is independent, but soiling is not modeled and the soiling-loss estimate is unvalidated; the cleaning rule requires the soiling output."),
    ("R1618", "Part B: cannot be checked without the full text; the code is unchanged.")]]
json.dump(LOG + kept, open(os.path.join(AN, "hc_adjudications.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(LOG), "changes applied;", len(kept), "codes kept")
