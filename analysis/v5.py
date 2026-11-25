"""Analyses: calibration with precision and intervals, designed and demonstrated levels, risk-set audit,
functions by decision stage, arid comparisons with Newcombe intervals and power, operational vs design-only differences
with intervals and first-author sensitivity, agreement statistics, capture-recapture, and cross-tabulations.
Usage: v5.py final.json stats.json facts.json charts.json tables.json flow.json recall.json supp_out.json"""
import json, sys, os, math, random, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search"))
from parse_journal import load
F = json.load(open(sys.argv[1], encoding="utf-8")); S = json.load(open(sys.argv[2], encoding="utf-8")); X = S["extra"]
FA = json.load(open(sys.argv[3], encoding="utf-8")); CH = json.load(open(sys.argv[4], encoding="utf-8")); T = json.load(open(sys.argv[5], encoding="utf-8"))
FL = json.load(open(sys.argv[6], encoding="utf-8")); RC = json.load(open(sys.argv[7], encoding="utf-8")); SUPP_OUT = sys.argv[8]
N = len(F); FM = {s["rid"]: s for s in F}; f = {}; SUP = {}
BLIND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blind_abstract_runs.json")
def pct(n, d): return f"{100 * n / d:.0f}" if d else "0"
def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))
def wci(k, n): lo, hi = wilson(k, n); return f"{100 * lo:.0f}–{100 * hi:.0f}%"
def newcombe(k1, n1, k2, n2):
    p1, p2 = k1 / n1, k2 / n2; l1, u1 = wilson(k1, n1); l2, u2 = wilson(k2, n2); d = p1 - p2
    return d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
def ndiff(k1, n1, k2, n2):
    d, lo, hi = newcombe(k1, n1, k2, n2)
    def _fmt(v):
        r = round(100 * v)
        return "0" if r == 0 else (f"+{r}" if r > 0 else f"−{abs(r)}")
    return f"{_fmt(d)} ({_fmt(lo)} to {_fmt(hi)})"
def fisher(a, b, c, d):
    n1, n2, m1 = a + b, c + d, a + c; n = n1 + n2
    def p(x): return math.comb(n1, x) * math.comb(n2, m1 - x) / math.comb(n, m1)
    p0 = p(a); lo, hi = max(0, m1 - n2), min(n1, m1)
    return min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 * (1 + 1e-9)))
def pf(p): return "< 0.001" if p < 0.001 else (f"= {p:.2f}" if p >= 0.01 else f"= {p:.3f}")
def join(items):
    items = [i for i in items if i]
    return items[0] if len(items) == 1 else (" and ".join(items) if len(items) == 2 else ", ".join(items[:-1]) + ", and " + items[-1])
MEAS = ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]
ONLINE_DEP = ["edge_or_embedded", "cloud", "fog_or_gateway", "multi_tier"]
meas = lambda s: any(m in s["sensing_modalities"] for m in MEAS)
online = lambda s: any(d in s["deployment"] for d in ONLINE_DEP) or s["real_time"] == "real_time_operation_demonstrated"
vm = lambda s: s["dt_maturity"] != "NA"
def demo(s):
    v = s.get("dt_demonstrated")
    if v: return v
    return s["dt_maturity"] if s["dt_maturity"] in ("digital_model", "NA") else "none_demonstrated"
for s in F: s["_demo"] = demo(s)

# ---------- 1. calibration: abstract-based versus full-text coding ----------
FIELDS = {
 "AI used": lambda s: s["ai_used"] == "yes",
 "Digital shadow or twin (designed)": lambda s: s["dt_maturity"] in ("digital_shadow", "digital_twin"),
 "Operational decisions addressed": lambda s: "operation" in s["decision_stage"],
 "Specific real installation": lambda s: s.get("physical_counterpart") == "specific_installation",
 "Measured data used": meas,
 "Field validation": lambda s: s["validation_setting"].startswith("field"),
 "Real-time operation demonstrated": lambda s: s["real_time"] == "real_time_operation_demonstrated",
 "Edge, fog, cloud, or multi-tier deployment": lambda s: any(d in s["deployment"] for d in ONLINE_DEP),
 "Temporal resolution reported": lambda s: s["temporal_resolution"] not in ("NR", "NA"),
 "Measured data over more than one season": lambda s: s["data_duration"] == "multi_season_or_multi_year" and meas(s),
 "Two-way or integrated coupling": lambda s: s.get("coupling") == "two_way_or_integrated",
 "Model calibrated against measurements": lambda s: s.get("data_assimilation") in ("calibration_only", "sequential_updating"),
 "Uncertainty quantified": lambda s: s.get("uncertainty_quantification") == "yes",
 "Data or code shared": lambda s: s["data_or_code_available"] == "yes_public",
 "Limitations stated": lambda s: bool(s.get("limitations_stated")),
}
B = {s["rid"]: s for v in load(BLIND).values() for s in v["studies"]}
pairs = []  # (full-text record, abstract-based record, set)
set1 = [r for r in B if r in FM and FM[r]["text_basis"] == "full_text" and not FM[r].get("recharted_full_text")]
set1_all = [r for r in B if r in CH["A"]]
for r in set1:
    if B[r]["eligible"] == "INCLUDE": pairs.append((FM[r], B[r], 1))
rech = [r for r in CH.get("ABS", {}) if r in FM and FM[r]["text_basis"] == "full_text"]
for r in rech: pairs.append((FM[r], CH["ABS"][r], 2))
f["cal_n1_total"] = len(set1_all); f["cal_n1"] = sum(1 for p in pairs if p[2] == 1); f["cal_n2"] = sum(1 for p in pairs if p[2] == 2); f["cal_n"] = len(pairs)
f["cal_n1_abs_incl"] = sum(1 for r in set1_all if B[r]["eligible"] == "INCLUDE" and CH["A"][r]["eligible"] == "INCLUDE" or (B[r]["eligible"] == "INCLUDE" and r in FM))
ft_incl1 = [r for r in set1_all if r in FM]
f["cal_n1_ftincl"] = len(ft_incl1); f["cal_n1_absincl"] = sum(1 for r in ft_incl1 if B[r]["eligible"] == "INCLUDE")
f["cal_elig_sens"] = pct(f["cal_n1_absincl"], f["cal_n1_ftincl"])
n_rech = len(CH.get("ABS", {})); n_rech_excl = sum(1 for r in CH.get("ABS", {}) if r not in FM)
f["n_rech_total"] = n_rech; f["n_rech_excl"] = n_rech_excl; f["n_rech_incl"] = n_rech - n_rech_excl; f["pct_rech_excl"] = pct(n_rech_excl, n_rech)
f["n_rech_ft"] = len(rech); f["n_rech_absbasis"] = f["n_rech_incl"] - len(rech)
f["n_ft_first_incl"] = sum(1 for s in F if s["text_basis"] == "full_text" and not s.get("recharted_full_text"))
f["n_no_stage"] = sum(1 for s in F if not s["decision_stage"])
FB = CH.get("FTX_BLIND", {}); f["n_ftx_blind"] = len(FB); f["n_ftx_blind_incl"] = sum(1 for v in FB.values() if v["eligible"] == "INCLUDE")
f["n_ftx_blind_excl"] = f["n_ftx_blind"] - f["n_ftx_blind_incl"]; f["pct_ftx_blind_excl"] = pct(f["n_ftx_blind_excl"], f["n_ftx_blind"])
cal = {}
rows = [["Included on eligibility (first set)", str(f["cal_n1_ftincl"]), str(f["cal_n1_absincl"]), f"{f['cal_elig_sens']}% ({wci(f['cal_n1_absincl'], f['cal_n1_ftincl'])})", "–", "–"]]
for name, fn in FIELDS.items():
    pp = [(fn(a), fn(b)) for a, b, _ in pairs]
    n = len(pp); full = sum(x for x, _ in pp); ab = sum(y for _, y in pp); both = sum(1 for x, y in pp if x and y); agree = sum(1 for x, y in pp if x == y)
    cal[name] = {"n": n, "full": full, "abs": ab, "both": both, "agree": agree}
    se = f"{pct(both, full)}% ({wci(both, full)})" if full else "–"; pv = f"{pct(both, ab)}% ({wci(both, ab)})" if ab else "–"
    rows.append([name, str(full), str(ab), se, pv, f"{pct(agree, n)}%"])
T["T5_sensitivity"] = {"caption": "Table 5 Coding From Abstracts Compared With Coding From Full Texts for the Same Studies",
    "header": ["Field", "Positive from full text", "Positive from abstract", "Detected from abstract, % (95% CI)", "Abstract code confirmed, % (95% CI)", "Agreement"],
    "widths": [2.9, 1.0, 1.0, 1.5, 1.5, 0.9], "rows": rows,
    "note": (f"Two sets of studies coded on both bases are pooled ({f['cal_n']} studies included on both bases). First set: the {f['cal_n1_total']} studies that had been charted from full text when the blind re-charting was done were re-charted from their titles and abstracts by a coding run blind to the full-text codes; {f['cal_n1']} were included on both bases. "
             f"Second set: {f['n_rech_ft']} studies first charted from their abstracts were charted again from full texts obtained later.  Detected from abstract (sensitivity) = studies positive on both bases divided by studies positive from full text. "
             "Abstract code confirmed (precision) = studies positive on both bases divided by studies positive from abstract. Agreement = share of studies coded identically on both bases. Intervals are Wilson 95% intervals. The first row gives, for the first set, how many of the studies included on full text were also included from the abstract.")}
def sens(k): v = cal[k]; return v["both"] / v["full"] if v["full"] else None
def ppv(k): v = cal[k]; return v["both"] / v["abs"] if v["abs"] else None
for k, lab in [("AI used", "ai"), ("Real-time operation demonstrated", "rt"), ("Field validation", "fv"), ("Measured data used", "md"), ("Two-way or integrated coupling", "cp"),
               ("Temporal resolution reported", "tr"), ("Data or code shared", "od"), ("Operational decisions addressed", "op"), ("Specific real installation", "si"),
               ("Digital shadow or twin (designed)", "st"), ("Model calibrated against measurements", "ca"), ("Uncertainty quantified", "uq"), ("Edge, fog, cloud, or multi-tier deployment", "dp")]:
    v = cal[k]; f[f"cs_{lab}_full"] = v["full"]; f[f"cs_{lab}_abs"] = v["abs"]; f[f"cs_{lab}_both"] = v["both"]
    f[f"cs_{lab}_sens"] = pct(v["both"], v["full"]) if v["full"] else "NA"; f[f"cs_{lab}_ppv"] = pct(v["both"], v["abs"]) if v["abs"] else "NA"
KF2 = ["eligible", "ai_used", "dt_maturity", "decision_stage", "physical_counterpart", "validation_setting", "real_time", "deployment", "temporal_resolution", "data_duration", "coupling", "data_assimilation", "data_or_code_available"]
SUP["calibration_pairs"] = {"header": ["Set", "Study ID", "Record ID", "Title"] + [f"{k} (abstract)" for k in KF2] + [f"{k} (full text)" for k in KF2],
    "rows": [[st, a.get("sid"), a["rid"], a.get("title")] + [str(b.get(k)) for k in KF2] + [str(a.get(k)) for k in KF2] for a, b, st in pairs]}
# corrected shares: full-text-charted studies as coded + abstract-charted positives x precision / sensitivity; bootstrap over calibration pairs
rng = random.Random(20261125)
ftS = [s for s in F if s["text_basis"] == "full_text"]; abS = [s for s in F if s["text_basis"] != "full_text"]
f["n_ft_now"] = len(ftS); f["pct_ft_now"] = pct(len(ftS), N); f["n_abs_now"] = len(abS); f["pct_abs_now"] = pct(len(abS), N)
for k, lab in [("Measured data used", "md"), ("Field validation", "fv"), ("AI used", "ai"), ("Real-time operation demonstrated", "rt"), ("Two-way or integrated coupling", "cp")]:
    fn = FIELDS[k]; ftp = sum(fn(s) for s in ftS); abp = sum(fn(s) for s in abS)
    pp = [(fn(a), fn(b)) for a, b, _ in pairs]
    def est(sample):
        full = sum(x for x, _ in sample); ab = sum(y for _, y in sample); both = sum(1 for x, y in sample if x and y)
        if not full or not ab or not both: return None
        return (ftp + abp * (both / ab) / (both / full)) / N
    point = est(pp); bs = sorted(x for x in (est([pp[rng.randrange(len(pp))] for _ in pp]) for _ in range(2000)) if x is not None)
    f[f"corr_{lab}"] = f"{100 * point:.0f}"; f[f"corr_{lab}_ci"] = f"{100 * bs[int(0.025 * len(bs))]:.0f}–{100 * bs[int(0.975 * len(bs)) - 1]:.0f}%"
    allp = ftp + abp; f[f"coded_{lab}"] = pct(allp, N); f[f"n_coded_{lab}"] = allp
    f[f"ft_{lab}_n"] = ftp; f[f"ft_{lab}_pct"] = pct(ftp, len(ftS)); f[f"ft_{lab}_ci"] = wci(ftp, len(ftS))
    f[f"abs_{lab}_pct"] = pct(abp, len(abS))


for k, lab in [("Data or code shared", "od"), ("Temporal resolution reported", "tr"), ("Measured data over more than one season", "ms"), ("Edge, fog, cloud, or multi-tier deployment", "dp"), ("Uncertainty quantified", "uq"), ("Model calibrated against measurements", "ca")]:
    fn = FIELDS[k]; ftp = sum(fn(s) for s in ftS); abp = sum(fn(s) for s in abS)
    f[f"ft_{lab}_n"] = ftp; f[f"ft_{lab}_pct"] = pct(ftp, len(ftS)); f[f"ft_{lab}_ci"] = wci(ftp, len(ftS)); f[f"abs_{lab}_pct"] = pct(abp, len(abS)); f[f"n_coded_{lab}"] = ftp + abp; f[f"coded_{lab}"] = pct(ftp + abp, N)

# ---------- 2. designed and demonstrated digital twin levels ----------
dc = collections.Counter(s["dt_maturity"] for s in F); mc = collections.Counter(s["_demo"] for s in F)
f.update({"n_des_model": dc["digital_model"], "n_des_shadow": dc["digital_shadow"], "n_des_twin": dc["digital_twin"], "n_des_na": dc["NA"],
          "n_demo_shadow": mc["digital_shadow"], "n_demo_twin": mc["digital_twin"], "n_demo_none": mc["none_demonstrated"]})
f["n_des_st"] = dc["digital_shadow"] + dc["digital_twin"]; f["pct_des_st"] = pct(f["n_des_st"], N)
f["n_vm"] = sum(vm(s) for s in F); f["pct_des_model_of_vm"] = pct(dc["digital_model"], f["n_vm"]); f["pct_des_model"] = pct(dc["digital_model"], N)
ds = [s for s in F if s["_demo"] == "digital_shadow"]
f["n_demo_shadow_op"] = sum(s["implementation_status"] == "operating_installation" for s in ds); f["n_demo_shadow_proto"] = sum(s["implementation_status"] == "prototype_or_testbed" for s in ds)
tw = [s for s in F if s["dt_maturity"] == "digital_twin"]; sh = [s for s in F if s["dt_maturity"] == "digital_shadow"]
f["n_twin_demo_model"] = sum(s["_demo"] == "digital_model" for s in tw); f["n_twin_none"] = sum(s["_demo"] == "none_demonstrated" for s in tw)
f["n_shadow_demo_model"] = sum(s["_demo"] == "digital_model" for s in sh); f["n_shadow_none"] = sum(s["_demo"] == "none_demonstrated" for s in sh)
f["n_dt_term"] = sum(s.get("dt_term_used") == "yes" for s in F)
f["n_dt_term_st"] = sum(1 for s in F if s.get("dt_term_used") == "yes" and s["dt_maturity"] in ("digital_shadow", "digital_twin"))
aud = [s for s in F if s.get("twin_audited")]
f["n_risk"] = len(aud); f["n_risk_ft"] = sum(s.get("audit_basis") == "full_text" for s in aud); f["n_risk_abs"] = f["n_risk"] - f["n_risk_ft"]
f["n_risk_ftchg"] = sum(s.get("audit_ft_could_change") == "yes" for s in aud)
f["n_risk_ftchg_st"] = sum(1 for s in aud if s.get("audit_ft_could_change") == "yes" and (s["dt_maturity"] in ("digital_shadow", "digital_twin") or s.get("real_time") != "offline"))
AM = CH.get("AUDIT_META", {}); _ai = [s for s in aud]
f["audit_n"] = len(_ai); f["audit_agree_designed"] = sum(1 for s in _ai if s.get("audit_d1") == s.get("audit_d2")); f["audit_agree_demo"] = sum(1 for s in _ai if s.get("audit_m1") == s.get("audit_m2"))
f["audit_adjudicated"] = sum(1 for s in aud if s["rid"] in AM.get("adjudicated", []))
# kappa for audit
def kap(pp):
    n = len(pp); po = sum(a == b for a, b in pp) / n
    cs = set(a for a, _ in pp) | set(b for _, b in pp)
    pe = sum((sum(a == c for a, _ in pp) / n) * (sum(b == c for _, b in pp) / n) for c in cs)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0
ap = [(s["audit_d1"], s["audit_d2"]) for s in aud]
f["audit_kappa"] = f"{kap(ap):.2f}" if ap else "NA"
# changes made by the audit relative to the earlier codes
CH0p = os.path.join(os.path.dirname(os.path.abspath(sys.argv[4])), "charts_all_before_v5.json")
F4p = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "final_v4.json")
if os.path.exists(F4p):
    F4 = {s["rid"]: s for s in json.load(open(F4p, encoding="utf-8"))}
    ch = [(F4[s["rid"]]["dt_maturity"], s["dt_maturity"]) for s in aud if s["rid"] in F4 and F4[s["rid"]]["dt_maturity"] != s["dt_maturity"]]
    f["n_audit_changed"] = len(ch); f["audit_changes"] = {f"{a}->{b}": c for (a, b), c in collections.Counter(ch).items()}
    f["n_audit_up"] = sum(1 for a, b in ch if ["NA", "digital_model", "digital_shadow", "digital_twin"].index(b) > ["NA", "digital_model", "digital_shadow", "digital_twin"].index(a))
    f["n_audit_down"] = len(ch) - f["n_audit_up"]
LABL = {"digital_model": "Digital model", "digital_shadow": "Digital shadow", "digital_twin": "Digital twin", "NA": "Not applicable", "none_demonstrated": "None demonstrated",
        "operating_installation": "Operating installation", "prototype_or_testbed": "Prototype or testbed", "concept_or_proposal": "Concept or proposal"}
# Table 10: designed and demonstrated level blocks
def lvl_rows(title, counter, keys):
    out = [[f"**{title}**", "", ""]]
    for k in keys: out.append([LABL[k], str(counter.get(k, 0)), pct(counter.get(k, 0), N)])
    return out
t10 = T["T10_deployment"]; rows = t10["rows"]; i0 = next(i for i, r in enumerate(rows) if r[0].strip("*") == "Digital twin level")
i1 = next(i for i in range(i0 + 1, len(rows)) if rows[i][0].startswith("**"))
rows[i0:i1] = lvl_rows("Digital twin level, as designed", dc, ["digital_model", "digital_shadow", "digital_twin", "NA"]) + lvl_rows("Digital twin level, as demonstrated", mc, ["digital_model", "digital_shadow", "digital_twin", "none_demonstrated", "NA"])
dtl = collections.Counter(x for s in F for x in s["decision_timescale"])
it = next(i for i, r in enumerate(rows) if r[0].strip("*") == "Decision timescale"); jt = next(i for i in range(it + 1, len(rows)) if rows[i][0].startswith("**"))
if not any(r[0] == "Not reported" for r in rows[it:jt]) and dtl.get("NR", 0):
    rows.insert(jt, ["Not reported", str(dtl["NR"]), pct(dtl["NR"], N)])
t10["note"] = (f"N = {N}. Deployment and decision timescale are multi-valued, so a study can appear under several tiers; a multi-tier architecture can be coded together with the tiers it combines. "
               "Offline under deployment means that no deployment beyond a desktop or server is reported, and simulation studies that report no deployment are coded offline; offline under real-time operation means that the study does not operate on live data. "
               "Digital twin levels follow Kritzinger et al. {Kritzinger2018}: the designed level is the level of the system as described, and the demonstrated level is the highest level whose data flows were run on an installation, prototype, or testbed with results reported; none demonstrated marks shadows and twins that were only designed. "
               "Not applicable marks sensing or control systems without a virtual model, and, for implementation status, pure simulations or analyses with no system to implement. A validation setting of none means that no validation is reported.")
# Table 11 with evidence columns
def path(s):
    p0 = path0(s); q = " ".join((s.get("audit_actuation_ev") or "").strip().strip('"').split()[:22])
    return p0 + (f": “{q}”" if q and q.lower() != "none stated" else "")
def path0(s):
    a = s.get("audit_actuation"); ev = (s.get("audit_actuation_ev") or "").lower()
    if a == "yes": return "Model output sets actuators automatically" + (" (designed only)" if s["_demo"] != "digital_twin" else "")
    if "manual" in ev or "user" in ev: return "Set-points changed by a person"
    if s.get("audit_threshold") == "yes": return "Rule-based control; model output to people"
    return "Recommendations or displays for people"
def mdesc(m):
    for a, b in [(" (vaguely described)", ""), ("ML analytics", "Machine learning analytics"), ("MPC with", "Model predictive control with"), (", MATLAB simulation", ""), (" (architecture only)", "")]:
        m = m.replace(a, b)
    return (m[:1].upper() + m[1:]) if m else m
def basis(s): return "Full text" if s.get("audit_basis") == "full_text" else "Title and abstract"
st_studies = sorted([s for s in F if s["dt_maturity"] in ("digital_shadow", "digital_twin")], key=lambda s: (s["dt_maturity"] != "digital_twin", s["_demo"] != "digital_shadow", s.get("year") or 0))
rows = []
for s in st_studies:
    q = (s.get("audit_input_ev") or "").strip().strip('"')
    q = " ".join(q.split()[:28]) + ("…" if len(q.split()) > 28 else "")
    rows.append([f"{{{s['rid']}}}", str(s.get("year") or ""), LABL[s["dt_maturity"]], ("Sensing system without a model" if s["_demo"] == "NA" else LABL[s["_demo"]]), LABL.get(s["implementation_status"], s["implementation_status"]), basis(s),
                 mdesc(s.get("audit_model") or ""), path(s), f"“{q}”" if q and q.lower() != "none stated" else "None stated"])
T["T11_twins"] = {"caption": "Table 11 Included Studies at the Digital Shadow and Digital Twin Levels, With the Evidence for Each Level",
    "header": ["Study", "Year", "Designed level", "Demonstrated level", "Installation", "Text basis", "Virtual model", "Path from model to installation, with evidence", "Evidence of automated data flow into the model"],
    "widths": [0.6, 0.5, 0.9, 1.0, 1.0, 0.8, 1.4, 2.2, 2.2], "rows": rows,
    "note": ("Levels were coded by two independent audit runs under the decision rules in Section 3.6, with quoted evidence, and disagreements were adjudicated. They reflect the data flows described in each study, not the authors' terminology. "
             "Text basis states whether the level was coded from the full text or from the title and abstract. Installation gives the implementation status of the system as described; Evidence quotes the passage on which the automated data flow rests. Quotations keep the authors' abbreviations: APV, agrophotovoltaic; DSS, decision support system; ETo, reference evapotranspiration.")}
near = [s for s in F if s["dt_maturity"] == "digital_model" and (s["real_time"] in ("real_time_operation_demonstrated", "designed_for_real_time") or any(d in s["deployment"] for d in ONLINE_DEP))]
f["n_near_miss"] = len(near)
SUP["near_miss"] = {"header": ["Study ID", "Year", "Title", "Real-time operation", "Deployment", "Text basis", "Reason the study is a digital model"],
                    "rows": [[s["sid"], s.get("year"), s["title"], s["real_time"], "; ".join(s["deployment"]), s.get("audit_basis") or s["text_basis"], s.get("audit_reason") or s.get("dt_reason") or ""] for s in near]}
# levels by subgroup (MR-14)
spec = [s for s in F if s.get("physical_counterpart") == "specific_installation"]; op = [s for s in F if "operation" in s["decision_stage"]]
f["n_spec"] = len(spec); f["n_spec_model"] = sum(s["dt_maturity"] == "digital_model" for s in spec); f["n_spec_st"] = sum(s["dt_maturity"] in ("digital_shadow", "digital_twin") for s in spec)
f["n_spec_na"] = sum(s["dt_maturity"] == "NA" for s in spec); f["pct_spec_st"] = pct(f["n_spec_st"], len(spec)); f["pct_spec_model"] = pct(f["n_spec_model"], len(spec))
f["n_spec_model_fv"] = sum(1 for s in spec if s["dt_maturity"] == "digital_model" and s["validation_setting"].startswith("field"))
f["n_op"] = len(op); f["n_op_st"] = sum(s["dt_maturity"] in ("digital_shadow", "digital_twin") for s in op); f["pct_op_st"] = pct(f["n_op_st"], len(op))
f["n_op_demo_st"] = sum(s["_demo"] in ("digital_shadow", "digital_twin") for s in op)
f["n_generic"] = sum(s.get("physical_counterpart") == "generic_design" for s in F); f["n_generic_model"] = sum(1 for s in F if s.get("physical_counterpart") == "generic_design" and s["dt_maturity"] == "digital_model")
f["pct_generic_model_of_dm"] = pct(f["n_generic_model"], dc["digital_model"])
# maturity map: level x validation among models
vmap = collections.Counter((s["dt_maturity"], "field" if s["validation_setting"].startswith("field") else ("other" if s["validation_setting"] != "none" else "none")) for s in F if vm(s))
f["n_dm_field"] = vmap[("digital_model", "field")]; f["n_dm_noval"] = vmap[("digital_model", "none")]
f["n_dm_spec_field_meas"] = sum(1 for s in spec if s["dt_maturity"] == "digital_model" and s["validation_setting"].startswith("field") and meas(s))

# ---------- 3. functions by decision stage ----------
for fn, lab in [("prediction", "pred"), ("optimization_control", "opt"), ("monitoring_state_estimation", "mon")]:
    has = [s for s in F if fn in s["dt_functions"]]
    f[f"n_fn_{lab}"] = len(has); f[f"n_fn_{lab}_op"] = sum("operation" in s["decision_stage"] for s in has); f[f"n_fn_{lab}_des"] = len(has) - f[f"n_fn_{lab}_op"]
    f[f"pct_fn_{lab}_op_of_op"] = pct(f[f"n_fn_{lab}_op"], len(op))
f["n_fn_all3_op"] = sum(1 for s in op if all(x in s["dt_functions"] for x in ["prediction", "optimization_control", "monitoring_state_estimation"]))
f["n_fn_all3"] = sum(1 for s in F if all(x in s["dt_functions"] for x in ["prediction", "optimization_control", "monitoring_state_estimation"]))
# function x level (designed)
SUP["function_by_level"] = {"header": ["Function", "Digital model", "Digital shadow", "Digital twin", "Not applicable"],
    "rows": [[fn] + [sum(1 for s in F if fn in s["dt_functions"] and s["dt_maturity"] == l) for l in ["digital_model", "digital_shadow", "digital_twin", "NA"]] for fn in ["prediction", "optimization_control", "monitoring_state_estimation"]]}

# ---------- 4. why twins are rare: physics-based models and online operation, within studies with a virtual model ----------
V = [s for s in F if vm(s)]; phys = lambda s: "physics_based" in s["method_families"]
f["n_vm_phys"] = sum(phys(s) for s in V); f["n_vm_online"] = sum(online(s) for s in V); f["n_vm_phys_online"] = sum(1 for s in V if phys(s) and online(s))
f["pct_vm_phys_online"] = pct(f["n_vm_phys_online"], f["n_vm_phys"]); f["n_vm_online_phys"] = f["n_vm_phys_online"]; f["pct_vm_online_phys"] = pct(f["n_vm_phys_online"], f["n_vm_online"])
f["n_vm_online_ml"] = sum(1 for s in V if online(s) and (s["ai_used"] == "yes" or "statistical" in s["method_families"]))
f["n_sys_online"] = sum(1 for s in F if not vm(s) and online(s)); f["n_online_all"] = sum(online(s) for s in F)
f["n_vm_full_stack"] = sum(1 for s in V if phys(s) and s.get("coupling") in ("one_way", "two_way_or_integrated") and meas(s) and online(s))

# ---------- 5. arid comparisons ----------
site = [s for s in F if s["koppen_main"] != ["NR"]]; Bg = [s for s in site if "B" in s["koppen_main"]]; Ng = [s for s in site if "B" not in s["koppen_main"]]
hot = lambda s: any((k or "").strip()[:3] in ("BWh", "BSh") for k in (s.get("koppen_subclass") or []))
cold = lambda s: any((k or "").strip()[:3] in ("BWk", "BSk") for k in (s.get("koppen_subclass") or []))
Hg = [s for s in site if hot(s)]; NHg = [s for s in site if not hot(s)]
Mg = [s for s in site if s.get("mena") == "yes"]; NMg = [s for s in site if s.get("mena") != "yes"]
f["n_class"] = len(site); f["n_Bsite"] = len(Bg); f["pct_Bsite_of_class"] = pct(len(Bg), len(site)); f["n_otherclass"] = len(Ng)
f["n_hot"] = len(Hg); f["n_cold"] = sum(cold(s) for s in Bg); f["n_hot_and_cold"] = sum(1 for s in Bg if hot(s) and cold(s)); f["n_B_nosub"] = sum(1 for s in Bg if not hot(s) and not cold(s))
arid_any = [s for s in F if "B" in s["koppen_main"] or s.get("arid_focus") == "explicit"]
f["n_arid_any"] = len(arid_any); f["pct_arid_any"] = pct(len(arid_any), N); f["n_arid_target_only2"] = sum(1 for s in arid_any if "B" not in s["koppen_main"])
f["n_arid_motiv"] = sum(1 for s in F if s.get("arid_focus") == "motivation_only" and "B" not in s["koppen_main"])
f["n_temperate"] = sum("C" in s["koppen_main"] for s in site); f["pct_temperate_of_class"] = pct(f["n_temperate"], len(site))
IND = {"ai": ("use AI", lambda s: s["ai_used"] == "yes"), "water": ("model water", lambda s: "water" in s["subsystems"]),
       "fv": ("report field validation", lambda s: s["validation_setting"].startswith("field")), "soil": ("model soiling", lambda s: "soiling" in s["subsystems"]),
       "meas": ("use measured data", meas), "op": ("address operational decisions", lambda s: "operation" in s["decision_stage"])}
cmp_rows = []
for gname, G1, G0 in [("arid", Bg, Ng), ("hot", Hg, NHg), ("mena", Mg, NMg)]:
    for k, (lab, fn) in IND.items():
        a = sum(fn(s) for s in G1); c = sum(fn(s) for s in G0); n1, n0 = len(G1), len(G0)
        p = fisher(a, n1 - a, c, n0 - c)
        f[f"c5_{gname}_{k}_x"] = a; f[f"c5_{gname}_{k}_n"] = n1; f[f"c5_{gname}_{k}_pct"] = pct(a, n1); f[f"c5_{gname}_{k}_ci"] = wci(a, n1)
        f[f"c5_{gname}_{k}_x0"] = c; f[f"c5_{gname}_{k}_n0"] = n0; f[f"c5_{gname}_{k}_pct0"] = pct(c, n0); f[f"c5_{gname}_{k}_ci0"] = wci(c, n0)
        f[f"c5_{gname}_{k}_diff"] = ndiff(a, n1, c, n0); f[f"c5_{gname}_{k}_p"] = pf(p)
        cmp_rows.append([{"arid": "Arid site (Köppen B)", "hot": "Hot arid site (BWh or BSh)", "mena": "MENA site"}[gname], lab, f"{a}/{n1} ({pct(a, n1)}%, {wci(a, n1)})", f"{c}/{n0} ({pct(c, n0)}%, {wci(c, n0)})", ndiff(a, n1, c, n0), pf(p).replace("= ", "")])
SUP["arid_comparison_v5"] = {"header": ["Group", "Indicator", "Group: x/n (%, 95% CI)", "Other classifiable sites: x/n (%, 95% CI)", "Difference, percentage points (95% CI)", "Fisher p"], "rows": cmp_rows}
# power of the AI contrast for a difference of the observed size
pa, pb = max(f["c5_arid_ai_x"], 0.5) / len(Bg), f["c5_arid_ai_x0"] / len(Ng)
rp = random.Random(7); hits = 0
for _ in range(2000):
    a = sum(rp.random() < pa for _ in range(len(Bg))); c = sum(rp.random() < pb for _ in range(len(Ng)))
    hits += fisher(a, len(Bg) - a, c, len(Ng) - c) < 0.05
f["power_ai"] = pct(hits, 2000)
fa = collections.Counter((s["authors"][0].split()[-1].lower() if s.get("authors") else s["rid"]) for s in Bg)
f["n_Bsite_first_authors"] = len(fa)
unc = [s for s in F if s["koppen_main"] == ["NR"]]
f["n_unclass"] = len(unc); f["n_unclass_sim"] = sum(s["study_type"] == "simulation_modeling" for s in unc); f["pct_unclass_sim"] = pct(f["n_unclass_sim"], len(unc))
f["n_unclass_generic"] = sum(s.get("physical_counterpart") == "generic_design" for s in unc); f["pct_unclass_generic"] = pct(f["n_unclass_generic"], len(unc))
f["n_unclass_abs"] = sum(s["text_basis"] != "full_text" for s in unc); f["pct_unclass_abs"] = pct(f["n_unclass_abs"], len(unc))
ai_site = [s for s in F if s["ai_used"] == "yes"]
f["n_ai"] = len(ai_site); f["n_ai_nosite"] = sum(s["koppen_main"] == ["NR"] for s in ai_site)
f["n_ai_multi_class"] = sum(1 for s in ai_site if len([k for k in s["koppen_main"] if k != "NR"]) > 1)
f["ai_by_class_sentence"] = join([f"{sum(k in s['koppen_main'] for s in ai_site)} {lab}" for k, lab in [("C", "a temperate site"), ("D", "a continental site"), ("B", "an arid site"), ("A", "a tropical site")] if sum(k in s['koppen_main'] for s in ai_site)])

if "T7_climate" in T:
    _r = T["T7_climate"]["rows"]
    def _setrow(label, n):
        for row in _r:
            if row[0] == label: row[1] = str(n); row[2] = pct(n, N) if n else "0"
    sub = lambda s, code: any((k or "").strip()[:3] == code for k in (s.get("koppen_subclass") or []))
    for code, lab in [("BWh", "BWh, hot desert"), ("BSh", "BSh, hot steppe"), ("BWk", "BWk, cold desert"), ("BSk", "BSk, cold steppe")]:
        _setrow(lab, sum(1 for s in Bg if sub(s, code)))
    _setrow("B, subclass not assigned", f["n_B_nosub"])
    _setrow("Arid site or arid target", f["n_arid_any"]); _setrow("Motivation only", f["n_arid_motiv"]); _setrow("None", N - f["n_arid_any"] - f["n_arid_motiv"])
    T["T7_climate"]["note"] = (f"N = {N}; {len(site)} studies have a site that could be assigned a climate class. Studies with sites in several climates, subclasses, or countries are counted in each row, so rows can overlap. "
                              f"Of the {len(Bg)} arid-site studies, {f['n_hot']} have a hot arid site (BWh or BSh) and {f['n_cold']} a cold arid site (BWk or BSk); {f['n_hot_and_cold']} have both, and {f['n_B_nosub']} have no subclass assigned. "
                              "Arid focus: arid site or arid target = a site in a Köppen B climate or an explicit target of arid, semi-arid, desert, or dryland conditions; motivation only = water scarcity or desert conditions used only as motivation.")
# ---------- 6. operational versus design-only: differences with intervals, text basis, first-author sensitivity ----------
des = [s for s in F if s["decision_stage"] == ["design"] or ("operation" not in s["decision_stage"] and "design" in s["decision_stage"])]
# primary analysis: within the full-text core (corpus-wide differences kept as o5c_* facts)
op6 = [s for s in op if s["text_basis"] == "full_text"]; des6 = [s for s in des if s["text_basis"] == "full_text"]
f["n_op6"] = len(op6); f["n_des6"] = len(des6)
INDO = {"Models or instruments a specific installation": lambda s: s.get("physical_counterpart") == "specific_installation", "Uses measured data": meas,
        "Measured data over more than one season": lambda s: s["data_duration"] == "multi_season_or_multi_year" and meas(s), "Field validation": lambda s: s["validation_setting"].startswith("field"),
        "AI used": lambda s: s["ai_used"] == "yes", "Subsystems coupled (one-way or two-way)": lambda s: s.get("coupling") in ("one_way", "two_way_or_integrated"),
        "Two-way or integrated coupling": lambda s: s.get("coupling") == "two_way_or_integrated", "Model calibrated against measurements": lambda s: s.get("data_assimilation") in ("calibration_only", "sequential_updating"),
        "Model updated repeatedly from measurements": lambda s: s.get("data_assimilation") == "sequential_updating", "Uncertainty quantified": lambda s: s.get("uncertainty_quantification") == "yes",
        "Real-time operation demonstrated": lambda s: s["real_time"] == "real_time_operation_demonstrated", "Edge, fog, cloud, or multi-tier deployment": lambda s: any(d in s["deployment"] for d in ONLINE_DEP),
        "Digital shadow or twin, as designed": lambda s: s["dt_maturity"] in ("digital_shadow", "digital_twin"), "Digital shadow or twin, as demonstrated": lambda s: s["_demo"] in ("digital_shadow", "digital_twin"),
        "Data or code shared": lambda s: s["data_or_code_available"] == "yes_public"}
def first(s): return s["authors"][0].split()[-1].lower() if s.get("authors") else s["rid"]
def wshare(G, fn):
    k = collections.Counter(first(s) for s in G); w = [1 / k[first(s)] for s in G]
    return sum(wi for wi, s in zip(w, G) if fn(s)) / sum(w)
rows = []; same_dir = 0; tested = 0; pvals = []
for lab, fn in INDO.items():
    a = sum(fn(s) for s in op6); c = sum(fn(s) for s in des6)
    p = fisher(a, len(op6) - a, c, len(des6) - c); pvals.append([lab, pf(p).replace("= ", "")])
    d = ndiff(a, len(op6), c, len(des6)) if (a + c) else "–"
    rows.append([lab, f"{a} ({pct(a, len(op6))}%)", f"{c} ({pct(c, len(des6))}%)", d])
    if a + c:
        tested += 1; raw = a / len(op6) - c / len(des6); wd = wshare(op6, fn) - wshare(des6, fn)
        same_dir += (raw > 0) == (wd > 0) or abs(raw) < 0.005
T["T12_operational"] = {"caption": "Table 12 Twin-Relevant Indicators for Studies Addressing Operational Decisions and for Design-Only Studies in the Full-Text Core",
    "header": ["Indicator", f"Operational decisions (n = {len(op6)})", f"Design only (n = {len(des6)})", "Difference, percentage points (95% CI)"],
    "widths": [3.6, 1.6, 1.5, 1.8], "rows": rows,
    "note": (f"Operational decisions include tracking, irrigation, cleaning, scheduling, and fault detection during operation; design-only studies address only design-stage decisions. "
             "Differences are operational minus design-only shares with Newcombe 95% intervals, reported as descriptive contrasts; they are not adjusted for multiple comparisons (Holm-adjusted results are in the text); cluster-bootstrap intervals resampling first authors are in Supplementary Material S2, sheet 'Cluster-robust intervals'. "
             "Real-time operation and deployment indicators are more likely by definition in studies of operation. "
             f"{sum(1 for s in ftS if not s['decision_stage'])} core studies, mostly sensing or measurement systems, address neither design nor operational decisions and are in neither group. "
             f"{sum(1 for s in des6 if s['real_time'] == 'real_time_operation_demonstrated')} design-only studies demonstrate real-time operation on live data during experiments, for example to collect the measurements a design study uses.")}
f["op_ft_pct"] = pct(sum(s["text_basis"] == "full_text" for s in op), len(op)); f["des_ft_pct"] = pct(sum(s["text_basis"] == "full_text" for s in des), len(des))
f["op_cluster_same_dir"] = same_dir; f["op_cluster_tested"] = tested; f["n_first_authors"] = len(set(first(s) for s in F))
f["n_reports_shared_author"] = sum(1 for s in F if collections.Counter(first(x) for x in F)[first(s)] > 1)
f["n_design_only"] = len(des6)
SUP["operational_p"] = {"header": ["Indicator", "Fisher p (two-sided)"], "rows": pvals}
for lab, key in [("Uses measured data", "md"), ("Models or instruments a specific installation", "si"), ("AI used", "ai"), ("Real-time operation demonstrated", "rt"), ("Subsystems coupled (one-way or two-way)", "cp"), ("Field validation", "fv")]:
    fn = INDO[lab]; a = sum(fn(s) for s in op6); c = sum(fn(s) for s in des6)
    f[f"o5_{key}"] = pct(a, len(op6)); f[f"d5_{key}"] = pct(c, len(des6)); f[f"o5_{key}_diff"] = ndiff(a, len(op6), c, len(des6))
f["o5_st"] = pct(sum(s["dt_maturity"] in ("digital_shadow", "digital_twin") for s in op6), len(op6))
for key, lab in [("ai", "AI used"), ("fv", "Field validation"), ("md", "Uses measured data"), ("rt", "Real-time operation demonstrated"), ("cp", "Subsystems coupled (one-way or two-way)")]:
    _fn = INDO[lab]; _a = sum(_fn(s) for s in op); _c = sum(_fn(s) for s in des); f[f"o5c_{key}_diff"] = ndiff(_a, len(op), _c, len(des))
f["n_op_all"] = len(op); f["n_des_all"] = len(des)

# ---------- 7. agreement statistics ----------
A, Bc = CH["A"], CH.get("B", {})
CH0p2 = os.path.join(os.path.dirname(os.path.abspath(sys.argv[4])), "charts_all_before_v5.json")
CH0 = json.load(open(CH0p2, encoding="utf-8")) if os.path.exists(CH0p2) else CH
A0, B0 = CH0["A"], CH0.get("B", {})
both = [r for r in B0 if r in A0]; inc2 = [r for r in both if A0[r]["eligible"] == "INCLUDE" and B0[r]["eligible"] == "INCLUDE"]
def pabak(pp):
    k = max(2, len(set(a for a, _ in pp) | set(b for _, b in pp))); po = sum(a == b for a, b in pp) / len(pp)
    return (k * po - 1) / (k - 1)
def posagree(pp, pos):
    a = sum(1 for x, y in pp if x == pos and y == pos); b = sum(1 for x, y in pp if (x == pos) != (y == pos))
    return 2 * a / (2 * a + b) if (2 * a + b) else float("nan")
ag_rows = []; ks = []; pbs = []
pp = [(A0[r]["eligible"], B0[r]["eligible"]) for r in both]
ag_rows.append(["Eligibility", len(pp), f"{100 * sum(a == b for a, b in pp) / len(pp):.0f}%", f"{kap(pp):.2f}", f"{pabak(pp):.2f}", f"{posagree(pp, 'INCLUDE'):.2f}"])
for fld, pos in [("ai_used", "yes"), ("arid_focus", "explicit"), ("mena", "yes"), ("validation_setting", None), ("study_type", None), ("dt_term_used", "yes"), ("real_time", "real_time_operation_demonstrated"),
                 ("temporal_resolution", None), ("data_duration", None), ("physical_counterpart", "specific_installation"), ("implementation_status", None), ("coupling", None), ("data_assimilation", None), ("uncertainty_quantification", "yes")]:
    pp = [(A0[r].get(fld), B0[r].get(fld)) for r in inc2 if A0[r].get(fld) is not None and B0[r].get(fld) is not None]
    if not pp: continue
    k = kap(pp); pb = pabak(pp); ks.append(k); pbs.append(pb)
    ag_rows.append([fld, len(pp), f"{100 * sum(a == b for a, b in pp) / len(pp):.0f}%", f"{k:.2f}", f"{pb:.2f}", f"{posagree(pp, pos):.2f}" if pos else "–"])
FLAB = {"ai_used": "AI use", "arid_focus": "arid focus", "mena": "MENA site", "validation_setting": "validation setting", "study_type": "study type", "dt_term_used": "use of the term digital twin", "real_time": "real-time operation", "temporal_resolution": "temporal resolution", "data_duration": "data duration", "physical_counterpart": "physical counterpart", "implementation_status": "implementation status", "coupling": "coupling", "data_assimilation": "model updating from measurements", "uncertainty_quantification": "uncertainty quantification"}
_mn = min(ag_rows[1:], key=lambda r: float(r[3])); f["kappa_min_field"] = FLAB.get(_mn[0], _mn[0])
f["kappa_min"] = f"{min(ks):.2f}"; f["kappa_max"] = f"{max(ks):.2f}"; f["pabak_min"] = f"{min(pbs):.2f}"; f["pabak_max"] = f"{max(pbs):.2f}"; f["n_kappa_fields"] = len(ks)
f["n_double_sample"] = len(both); f["n_double_both_incl"] = len(inc2)
# decision stage agreement (multi-valued): exact match share
ex = sum(1 for r in inc2 if set(A0[r].get("decision_stage") or []) == set(B0[r].get("decision_stage") or [])); f["ds_exact"] = pct(ex, len(inc2))
oppp = [("operation" in (A0[r].get("decision_stage") or []), "operation" in (B0[r].get("decision_stage") or [])) for r in inc2]; f["ds_op_kappa"] = f"{kap(oppp):.2f}"
SUP["agreement_v5"] = {"header": ["Field", "Studies", "Raw agreement", "Cohen's kappa", "PABAK", "Positive agreement"], "rows": ag_rows}
# capture-recapture (Chapman) for the title-and-abstract screening passes
n1, n2, m = FA.get("lp_nA"), FA.get("lp_nB"), FA.get("lp_m")
if n1 and n2 and m:
    Nh = (n1 + 1) * (n2 + 1) / (m + 1) - 1; var = (n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m) / ((m + 1) ** 2 * (m + 2)); seen = n1 + n2 - m
    f["cr_n1"], f["cr_n2"], f["cr_m"], f["cr_seen"] = n1, n2, m, seen; f["cr_missed"] = f"{Nh - seen:.1f}"; f["cr_hi"] = f"{max(0, Nh - seen + 1.96 * math.sqrt(var)):.1f}"
# recall check interval
f["recall_ci"] = wci(RC["n_retrieved"], RC["n_known"]).replace("%", "") + "%"
f["n_recall_reviews"] = len(RC.get("reviews", [])) if isinstance(RC.get("reviews"), list) else RC.get("n_reviews", 8)

# ---------- 8. cross-tabulations ----------
SUP["level_by_updating"] = {"header": ["Designed level", "Repeated updating", "One-time calibration", "None"], "rows": [[LABL[l]] + [sum(1 for s in F if s["dt_maturity"] == l and s.get("data_assimilation") == u) for u in ["sequential_updating", "calibration_only", "none"]] for l in ["digital_model", "digital_shadow", "digital_twin", "NA"]]}
SUP["validation_by_duration"] = {"header": ["Validation setting", "Less than one season", "One season or year", "More than one season", "Not reported", "Not applicable"],
    "rows": [[v] + [sum(1 for s in F if s["validation_setting"] == v and s["data_duration"] == d) for d in ["less_than_one_season", "one_season_or_year", "multi_season_or_multi_year", "NR", "NA"]] for v in ["field_measurements_multi_site", "field_measurements_single_site", "laboratory_or_prototype", "simulation_benchmark_only", "none"]]}
act = [s for s in F if "tracking_or_dynamic" in s["av_configuration"]]; fix = [s for s in F if "tracking_or_dynamic" not in s["av_configuration"]]
SUP["actuated_vs_fixed"] = {"header": ["Indicator", f"Tracking or dynamic (n = {len(act)})", f"Other configurations (n = {len(fix)})", "Difference (95% CI)"],
    "rows": [[lab, f"{sum(fn(s) for s in act)} ({pct(sum(fn(s) for s in act), len(act))}%)", f"{sum(fn(s) for s in fix)} ({pct(sum(fn(s) for s in fix), len(fix))}%)", ndiff(sum(fn(s) for s in act), len(act), sum(fn(s) for s in fix), len(fix))] for lab, fn in INDO.items()]}
f["n_act"] = len(act); f["act_op_pct"] = pct(sum("operation" in s["decision_stage"] for s in act), len(act)); f["fix_op_pct"] = pct(sum("operation" in s["decision_stage"] for s in fix), len(fix))
f["act_st"] = sum(s["dt_maturity"] in ("digital_shadow", "digital_twin") for s in act)
# deployment tier x function x timescale
SUP["tier_function_timescale"] = {"header": ["Deployment", "Function", "Seconds or faster", "Minutes to hours", "Days to weeks", "Season or longer"],
    "rows": [[d, fn] + [sum(1 for s in F if d in s["deployment"] and fn in s["dt_functions"] and t in s["decision_timescale"]) for t in ["seconds_or_faster", "minutes_to_hours", "days_to_weeks", "season_or_longer"]]
             for d in ["edge_or_embedded", "fog_or_gateway", "cloud", "multi_tier", "offline_desktop_or_server"] for fn in ["prediction", "optimization_control", "monitoring_state_estimation"]]}
edge = [s for s in F if "edge_or_embedded" in s["deployment"]]
f["n_edge"] = len(edge); f["n_edge_act"] = sum(1 for s in edge if "optimization_control" in s["dt_functions"] and "operation" in s["decision_stage"])
f["n_edge_track"] = sum(1 for s in edge if "tracking_or_dynamic" in s["av_configuration"])

# ---------- 9. named subsets for readers ----------
subsets = {"Data or code shared publicly": lambda s: s["data_or_code_available"] == "yes_public",
           "Measured data over more than one season": lambda s: s["data_duration"] == "multi_season_or_multi_year" and meas(s),
           "Field validation at more than one site": lambda s: s["validation_setting"] == "field_measurements_multi_site",
           "Site in the MENA region": lambda s: s.get("mena") == "yes", "Hot arid site (BWh or BSh)": hot, "Soiling modeled": lambda s: "soiling" in s["subsystems"],
           "AI used": lambda s: s["ai_used"] == "yes", "Digital shadow or twin (designed)": lambda s: s["dt_maturity"] in ("digital_shadow", "digital_twin")}
SUP["named_subsets"] = {"header": ["Subset", "Study ID", "Year", "Country", "Configuration", "Text basis", "Title"],
    "rows": [[k, s["sid"], s.get("year"), "; ".join(s.get("country") or []), "; ".join(s["av_configuration"]), s["text_basis"], s["title"]] for k, fn in subsets.items() for s in sorted(F, key=lambda s: s.get("year") or 0) if fn(s)]}
import re as _re
for k, fn in subsets.items(): f["nsub_" + _re.sub("[^a-z]", "", "".join(w[0] for w in k.split()).lower())] = sum(fn(s) for s in F)

# ---------- 9b. Table 14a (proposal) and 14b (evidence, each count with its criterion) ----------
def hasm(s, *m): return any(x in s["method_families"] for x in m)
def dep(s, *d): return any(x in s["deployment"] for x in d)
sub = lambda s, *x: all(y in s["subsystems"] for y in x)
opf = lambda s: "operation" in s["decision_stage"]
aridS = lambda s: "B" in s["koppen_main"]
PROP = [('F1', 'Execution of tracker, valve, and cleaning set-points', 'Seconds to minutes', 'Already in PV monitoring (IEC 61724-1): plane-of-array irradiance, tracker angle, PV output, wind. Minimum addition: PAR at crop height under and between the panels; crop stage from the crop calendar; valve states and flow. Set-points pass through the existing plant SCADA and power plant controller, tracker controller, and irrigation controller or greenhouse climate computer; the tracker controller keeps stow authority within its safety limits', 'Rule-based control or model predictive control with light and PV models', 'Edge', 'Corpus; IEC 61724-1; monitoring reviews {Pereira2026}{DiDomenico2026}; design reasoning'),
 ('F9', 'Crop-PV light-sharing plan: the daily tracking schedule against a crop light target', 'Daily (revised hourly when cloud cover changes)', "Already in PV monitoring: plane-of-array irradiance, PV output, tracker angle. Minimum addition: PAR at crop height under and between the panels; crop stage; the day's weather forecast. Research-grade: canopy light interception", 'Coupled light, crop, and PV models; optimization of the tilt sequence', 'Fog or gateway; set-points executed under F1', 'Corpus; design reasoning'),
 ('F2', 'State estimation of light and microclimate under the array', 'Minutes to hours', 'Already in PV monitoring: global irradiance, module and air temperature, wind. Minimum addition: diffuse irradiance; PAR at crop height at several positions across the row; humidity; ground albedo (bifacial modules). Research-grade: spectral quality (semi-transparent or spectrally selective modules); the same light and weather variables on an open-field reference plot', 'Ray-tracing or view-factor light models precomputed offline, whose parameters such as albedo and module transmittance are corrected from the sensors; machine learning surrogates', 'Fog or gateway', 'Corpus; monitoring reviews {Pereira2026}{DiDomenico2026}{Cosme2025}; design reasoning'),
 ('F3', 'Short-term forecasting of energy, microclimate, and crop water demand', 'Hours to days', 'Minimum: weather forecasts and the measured history of the F2 streams', 'Statistical or machine learning forecasters combined with physics-based models', 'Fog or gateway', 'Corpus'),
 ('F4', 'Irrigation planning with a shared water balance', 'Days (hours at hot arid sites)', 'Already in PV monitoring: irradiance, air temperature, wind. Minimum addition: soil moisture at two or more depths and positions across the row (under the panel, at the drip edge, between rows); net radiation and humidity at crop height for evapotranspiration under the array; rain gauges under and between the panels; irrigation water use and salinity; crop stage and canopy cover. Research-grade: leaf area index; soil hydraulic properties; plant water status (predawn water potential is a manual measurement, as in {R0909}); an independent water-balance or lysimeter check of evapotranspiration', 'Crop and soil water balance models with soil-water and crop states updated from soil-moisture and canopy observations; machine learning yield and water models', 'Fog for daily plans, cloud for seasonal re-planning; set-points executed under F1', 'Corpus; monitoring reviews {DiDomenico2026}{Cosme2025}; design reasoning'),
 ('F5', 'Heat-stress management of modules and crop (hot arid sites)', 'Hours to days', 'Already in PV monitoring: plane-of-array irradiance, module temperature, wind. Minimum addition: canopy temperature; air temperature and humidity under the array; greenhouse cooling water use', 'Coupled thermal models of modules and canopy', 'Fog for daily plans, cloud for seasonal re-planning; set-points executed under F1', 'Corpus gap; design reasoning'),
 ('F6', 'Soiling detection and cleaning planning (arid sites)', 'Days', 'Already in PV monitoring: PV output, plane-of-array irradiance, wind. Minimum addition: soiling ratio from a cleaned and an uncleaned reference cell; humidity and dew, which cement dust; cleaning water use. Research-grade: airborne dust concentration', 'Soiling loss models; machine learning detection', 'Detection at the edge, planning in the cloud', 'Corpus gap; IEC 61724-1'),
 ('F7', 'Design and seasonal planning', 'Season or longer', 'Typical meteorological year, crop parameters, layout and module options', 'Coupled light, crop, PV, and water simulation; surrogate-based optimization', 'Cloud or offline', 'Corpus'),
 ('F8', 'Parameter calibration and model retraining', 'Seasonal or on new data', 'Multi-season measured data with sensor metadata and calibration records, with a period held out from calibration for validation', 'Parameter estimation and retraining with uncertainty quantification', 'Cloud', 'Corpus; monitoring reviews {Pereira2026}{DiDomenico2026}'),
 ('G', 'Data governance and security across all functions', 'Continuous', 'Access and override logs; data-sharing agreements between farmer, landowner, and PV operator; sensor, model, and software version records', 'Role-based access control and audit trail; security zones and conduits', 'All tiers; farm data stay on the fog tier unless shared by agreement', 'Corpus gap; IEC 62443 {IEC62443}; design reasoning')]
_MG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mech_codes.json"), encoding="utf-8"))
EVID = {
 "F1": ("operational optimization or control at the seconds-or-faster or minutes-to-hours timescale", lambda s: opf(s) and "optimization_control" in s["dt_functions"] and ("minutes_to_hours" in s["decision_timescale"] or "seconds_or_faster" in s["decision_timescale"]),
        "rule-based or model predictive control with a light or PV model", lambda s: hasm(s, "rule_based_control", "model_predictive_control") and ("light_shading" in s["subsystems"] or "pv_energy" in s["subsystems"]),
        "edge or multi-tier", lambda s: dep(s, "edge_or_embedded", "multi_tier")),
 "F2": ("monitoring or state estimation of light or microclimate", lambda s: "monitoring_state_estimation" in s["dt_functions"] and ("light_shading" in s["subsystems"] or "microclimate" in s["subsystems"]),
        "physics-based light model run with measured data", lambda s: hasm(s, "physics_based", "hybrid_physics_ml") and "light_shading" in s["subsystems"] and meas(s),
        "fog or multi-tier", lambda s: dep(s, "fog_or_gateway", "multi_tier")),
 "F3": ("prediction for operational decisions", lambda s: opf(s) and "prediction" in s["dt_functions"],
        "hybrid, or statistical or machine learning combined with a physics-based model", lambda s: hasm(s, "hybrid_physics_ml") or (hasm(s, "classical_ml", "deep_learning", "statistical") and hasm(s, "physics_based")),
        "fog or multi-tier", lambda s: dep(s, "fog_or_gateway", "multi_tier")),
 "F4": ("water modeled for operational decisions", lambda s: "water" in s["subsystems"] and opf(s),
        "water modeled together with the crop", lambda s: sub(s, "water", "crop"),
        "fog, cloud, or multi-tier", lambda s: dep(s, "fog_or_gateway", "cloud", "multi_tier")),
 "F5": ("microclimate and PV energy both modeled, with heat as a stated constraint", lambda s: sub(s, "microclimate", "pv_energy") and "heat_or_high_temperature" in (s.get("arid_constraints") or []),
        "two-way or integrated coupling", lambda s: s.get("coupling") == "two_way_or_integrated",
        "fog, cloud, or multi-tier", lambda s: dep(s, "fog_or_gateway", "cloud", "multi_tier")),
 "F6": ("soiling modeled or dust considered", lambda s: "soiling" in s["subsystems"] or "dust_soiling" in (s.get("arid_constraints") or []),
        "soiling modeled", lambda s: "soiling" in s["subsystems"],
        "edge, cloud, or multi-tier", lambda s: dep(s, "edge_or_embedded", "cloud", "multi_tier")),
 "F7": ("design decisions", lambda s: "design" in s["decision_stage"],
        "light, crop, PV, and water all modeled and coupled", lambda s: sub(s, "light_shading", "crop", "pv_energy", "water") and s.get("coupling") in ("one_way", "two_way_or_integrated"),
        None, None),
 "F9": ("tracking or shading planned against a crop light or yield target", lambda s: opf(s) and "optimization_control" in s["dt_functions"] and sub(s, "light_shading", "crop", "pv_energy"),
        "light, crop, and PV modeled and linked", lambda s: sub(s, "light_shading", "crop", "pv_energy") and s.get("coupling") in ("one_way", "two_way_or_integrated"),
        "fog, cloud, or multi-tier", lambda s: dep(s, "fog_or_gateway", "cloud", "multi_tier")),
 "F8": ("model calibrated or updated against measurements", lambda s: s.get("data_assimilation") in ("calibration_only", "sequential_updating"),
        "calibration with uncertainty quantification", lambda s: s.get("uncertainty_quantification") == "yes",
        "cloud or multi-tier", lambda s: dep(s, "cloud", "multi_tier")),
 "G": ("governance or security addressed (full-text coding)", lambda s: _MG.get(s["rid"], {}).get("governance_or_security") == "yes",
        "on a prototype or operating installation", lambda s: s.get("implementation_status") in ("prototype_or_testbed", "operating_installation"), None, None)
}
rows_a = [[i, name, ts, data, models, tier, prov + "; tier: design reasoning"] for i, name, ts, data, models, tier, prov in PROP]
rows_b = []
for i, name, *_ in PROP:
    ca, fa_, cm, fm, ct, ft = EVID[i]
    addr = [s for s in F if fa_(s)]; wm = [s for s in addr if fm(s)]
    na, nm = len(addr), len(wm); nt = sum(1 for s in wm if ft(s)) if ft else None
    ar = lambda L: sum(aridS(s) for s in L)
    cell = lambda n, L: f"{n}" + (f" ({ar(L)} at arid sites)" if i in ("F5", "F6") else "")
    rows_b.append([i, f"{cell(na, addr)}: {ca}", f"{cell(nm, wm)}: {cm}", (f"{nt}: {ct}" if ft else ("Not applicable" if i == "G" else "Not counted: offline is the default for design"))])
    f[f"t14_{i}_addr"] = na; f[f"t14_{i}_model"] = nm; f[f"t14_{i}_tier"] = nt if nt is not None else "NA"
T["T14_architecture"] = {"caption": "Table 14a Proposed Reference Architecture: Functions and Decisions Mapped to Timescales, Proposed Core Data, Model Types, and Computing Tiers",
  "header": ["ID", "Function and decision", "Decision timescale", "Proposed core data", "Model types (proposed)", "Proposed tier", "Basis"],
  "widths": [0.4, 1.6, 1.0, 2.9, 1.8, 1.1, 1.2], "rows": rows_a,
  "note": ("The architecture is a conceptual proposal informed by the charted evidence; it was not coded in the corpus, and no included study tests it. Basis states where each element comes from: the coded studies (corpus), a gap in the coded studies (corpus gap), the monitoring reviews {Pereira2025}, {DiDomenico2026}, {Pereira2026}, {Cosme2025}, IEC 61724-1 {IEC61724}, or design reasoning. "
           "The decision timescale is the interval at which a decision is revised. Each data list is split into what standard PV monitoring already provides (IEC 61724-1), the minimum addition proposed for a digital shadow of that function, and research-grade items for pilot installations. Tiers follow the latency each function tolerates and a footprint criterion: each function runs at the lowest tier that meets its latency, so remote (cloud) computing is limited to seasonal planning and retraining (F4-F5 re-planning, F6 cleaning planning, F7, F8), which run a few times per season and keep data transfer and remote computing energy small. Row G applies to every tier. Suggested recording intervals: PV and irradiance channels as IEC 61724-1 specifies for its Class A or B systems; PAR and microclimate 1 to 10 minutes; soil moisture 15 to 60 minutes. Sensor counts, accuracy classes, sampling intervals, record lengths, and maintenance intervals are left open; for the PV channels they are set by IEC 61724-1 {IEC61724}. "
           "Fallback set-points for loss of data or communication belong to every row executed at the edge; they are discussed with Figure 3.")}
T["T14b_evidence"] = {"caption": "Table 14b Studies in the Corpus That Report Each Element of the Proposed Architecture",
  "header": ["ID", "Studies addressing the function: count and criterion", "Of these, with the proposed model type: count and criterion", "Of these, deployed at the proposed tier: count and criterion"],
  "widths": [0.4, 3.0, 3.0, 2.6], "rows": rows_b,
  "note": (f"N = {N}. Counts are nested from left to right. Counts use the four coded timescale bins (seconds or faster; minutes to hours; days to weeks; season or longer), which are broader than the ranges in Table 14a. Because the corpus was not coded against the architecture, the counts show how far each element has been reported, not whether the architecture is right.")}
f["n_salinity"] = sum("salinity" in (s.get("arid_constraints") or []) for s in F); f["n_salinity_arid"] = sum(1 for s in F if "salinity" in (s.get("arid_constraints") or []) and (aridS(s) or s.get("arid_focus") == "explicit"))
f["n_dust_arid"] = sum(1 for s in arid_any if "dust_soiling" in (s.get("arid_constraints") or [])); f["n_soiling_all"] = sum("soiling" in s["subsystems"] for s in F)

# ---------- 9c. yield of each search string, and automatic exclusions by reason ----------
RECS = {r["rid"]: r for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search", "records_v2_auto.json"), encoding="utf-8"))}
QL = {"Scopus_S1_av": "scopus_s1", "S1_av": "s2_s1", "S1_av_partial_Q1": "oa_enabler", "S1_av_partial_Q3": "oa_arid", "S2_dt": "s2string", "S2_S3_terms": "s3string", "citation_search_reviews": "citation"}
for q, lab in QL.items():
    inc_q = [s for s in F if q in (RECS.get(s["rid"], {}).get("queries") or [])]
    f[f"q_{lab}_incl"] = len(inc_q); f[f"q_{lab}_uniq"] = sum(1 for s in inc_q if len(RECS[s["rid"]].get("queries") or []) == 1)
oa_arid_only = [s for s in F if (RECS.get(s["rid"], {}).get("queries") or []) == ["S1_av_partial_Q3"]]
f["q_oa_arid_only_aridsite"] = sum(1 for s in oa_arid_only if "B" in s["koppen_main"])
AR = FL.get("auto_reasons", {})
f["n_auto_lang"] = sum(v for k, v in AR.items() if k.startswith("E6 not English")); f["n_auto_review"] = sum(v for k, v in AR.items() if k.startswith("E4"))
f["n_auto_type"] = sum(v for k, v in AR.items() if k.startswith("E5")); f["n_auto_norecord"] = sum(v for k, v in AR.items() if k.startswith("E6 no record"))
f["n_auto_preprint"] = AR.get("E5 preprint", 0); f["n_auto_chapter"] = AR.get("E5 book chapter", 0) + AR.get("E5 book", 0); f["n_auto_thesis"] = AR.get("E5 thesis", 0)
f["n_auto_confabs"] = AR.get("E5 conference abstract", 0) + AR.get("E5 conference review", 0)
f["n_assessed_full_fl"] = FL.get("n_assessed_full"); f["n_assessed_abs_fl"] = FL.get("n_assessed_abs")


# ---------- 9d. robustness of the headline, and arid comparisons within full-text-charted studies ----------
flag = [s for s in aud if s.get("audit_ft_could_change") == "yes"]
f["n_flag"] = len(flag)
f["n_flag_vm"] = sum(1 for s in flag if s.get("audit_virtual_model") == "yes")
f["n_flag_input_unclear"] = sum(1 for s in flag if s.get("audit_input") in ("unclear", "yes"))
f["n_flag_act_possible"] = sum(1 for s in flag if s.get("audit_actuation") in ("unclear", "yes") and s.get("audit_virtual_model") == "yes")
f["n_flag_act_possible_hw"] = sum(1 for s in flag if s.get("audit_actuation") in ("unclear", "yes") and s.get("audit_virtual_model") == "yes" and s.get("implementation_status") in ("operating_installation", "prototype_or_testbed"))
ftst = [s for s in F if s["text_basis"] == "full_text" and s["dt_maturity"] in ("digital_shadow", "digital_twin")]
f["n_st_ft"] = len(ftst); f["n_st_abs"] = f["n_des_st"] - len(ftst)
siteF = [s for s in site if s["text_basis"] == "full_text"]; BgF = [s for s in siteF if "B" in s["koppen_main"]]; NgF = [s for s in siteF if "B" not in s["koppen_main"]]
f["n_classF"] = len(siteF); f["n_BsiteF"] = len(BgF); f["n_otherF"] = len(NgF)
for k, (lab, fn) in IND.items():
    a = sum(fn(s) for s in BgF); c = sum(fn(s) for s in NgF)
    if BgF and NgF:
        f[f"c5f_{k}_x"] = a; f[f"c5f_{k}_pct"] = pct(a, len(BgF)); f[f"c5f_{k}_x0"] = c; f[f"c5f_{k}_pct0"] = pct(c, len(NgF)); f[f"c5f_{k}_diff"] = ndiff(a, len(BgF), c, len(NgF))
f["ft_share_Bsite"] = pct(len(BgF), len(Bg)); f["ft_share_other"] = pct(len(NgF), len(Ng))


# ---------- 9e. model structure and validation in full-text studies; field-data inventory of excluded records ----------
_mp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mech_codes.json")
if os.path.exists(_mp):
    MC = json.load(open(_mp, encoding="utf-8"))
    MS = [MC[s["rid"]] for s in F if s["text_basis"] == "full_text" and s["rid"] in MC]
    mv = [m for m in MS if "NA" not in m["validated_subsystems"]]
    f["n_mech"] = len(MS); f["n_mech_model"] = len(mv)
    cnt = lambda key, val: sum(1 for m in mv if val in m[key])
    f["val_none"] = cnt("validated_subsystems", "none"); f["val_any"] = len(mv) - f["val_none"]
    for v, lab in [("light_shading", "light"), ("pv_energy", "pv"), ("crop", "crop"), ("microclimate", "micro"), ("water", "water")]:
        f[f"val_{lab}"] = cnt("validated_subsystems", v)
    f["val_indep"] = sum(1 for m in mv if m["validation_independent"] == "yes"); f["val_notindep"] = sum(1 for m in mv if m["validation_independent"] == "no")
    f["val_indep_nr"] = sum(1 for m in mv if m["validation_independent"] == "NR")
    f["val_multi"] = sum(1 for m in mv if m["validation_duration"] == "more_than_one_season"); f["val_gof"] = sum(1 for m in mv if m["goodness_of_fit_reported"] == "yes")
    for v, lab in [("process_based", "process"), ("empirical_or_statistical", "emp"), ("light_only", "lightonly"), ("none", "none")]:
        f[f"crop_{lab}"] = sum(1 for m in mv if m["crop_representation"] == v)
    for v, lab in [("sub_hourly", "subh"), ("hourly", "hourly"), ("daily", "daily"), ("seasonal_or_static", "static"), ("NR", "nr")]:
        f[f"step_{lab}"] = sum(1 for m in mv if m["model_time_step"] == v)
    f["fb_none"] = cnt("feedbacks_represented", "none"); f["fb_any"] = len(mv) - f["fb_none"]
    for v, lab in [("albedo_bifacial", "albedo"), ("shade_microclimate_crop", "shade"), ("water_energy", "waterenergy"), ("crop_cools_modules", "cool"), ("rain_redistribution", "rain")]:
        f[f"fb_{lab}"] = cnt("feedbacks_represented", v)
    f["op_operated"] = sum(1 for m in MS if m["operational_benefit_measured"] in ("yes", "no")); f["op_benefit"] = sum(1 for m in MS if m["operational_benefit_measured"] == "yes")
    f["gov_yes"] = sum(1 for m in MS if m["governance_or_security"] == "yes"); f["foot_yes"] = sum(1 for m in MS if m["compute_footprint"] == "yes")
    f["pct_mval_none"] = pct(f["val_none"], len(mv))
    _ftm = [s for s in F if s["text_basis"] == "full_text" and s["rid"] in MC and "NA" not in MC[s["rid"]]["validated_subsystems"]]
    f["n_val_field_ft"] = sum(1 for s in _ftm if s["validation_setting"].startswith("field"))
    f["n_val_agree"] = sum(1 for s in _ftm if s["validation_setting"].startswith("field") == ("none" not in MC[s["rid"]]["validated_subsystems"]))
    f["n_cpl2_ft"] = sum(1 for s in _ftm if s.get("coupling") == "two_way_or_integrated")
    f["n_cpl2_fb"] = sum(1 for s in _ftm if s.get("coupling") == "two_way_or_integrated" and "none" not in MC[s["rid"]]["feedbacks_represented"])
    f["n_cpl_fb_agree"] = sum(1 for s in _ftm if (s.get("coupling") == "two_way_or_integrated") == ("none" not in MC[s["rid"]]["feedbacks_represented"]))
    f["pct_crop_process"] = pct(f["crop_process"], len(mv)); f["pct_fb_none"] = pct(f["fb_none"], len(mv))
    L = lambda k: k
    rows = [["**Modeled outputs compared with measurements**", "", ""]] + [[lab, str(f[k]), pct(f[k], len(mv))] for k, lab in [("val_none", "None"), ("val_light", "Light or PAR under the array"), ("val_pv", "PV power or yield"), ("val_crop", "Crop yield, growth, or physiology"), ("val_micro", "Microclimate"), ("val_water", "Soil water or evapotranspiration")]]
    rows += [["**Validation design**", "", ""], ["Validation data stated to be independent of calibration data", str(f["val_indep"]), pct(f["val_indep"], len(mv))], ["Same data used for calibration and validation", str(f["val_notindep"]), pct(f["val_notindep"], len(mv))], ["Independence not stated", str(f["val_indep_nr"]), pct(f["val_indep_nr"], len(mv))], ["Validation over more than one season", str(f["val_multi"]), pct(f["val_multi"], len(mv))], ["Quantitative error metric reported", str(f["val_gof"]), pct(f["val_gof"], len(mv))]]
    rows += [["**Crop representation**", "", ""]] + [[lab, str(f[k]), pct(f[k], len(mv))] for k, lab in [("crop_process", "Process-based crop model"), ("crop_emp", "Empirical, statistical, or machine learning"), ("crop_lightonly", "Light reaching the crop only"), ("crop_none", "Crop not modeled")]]
    rows += [["**Finest model time step**", "", ""]] + [[lab, str(f[k]), pct(f[k], len(mv))] for k, lab in [("step_subh", "Sub-hourly"), ("step_hourly", "Hourly"), ("step_daily", "Daily"), ("step_static", "Seasonal or static"), ("step_nr", "Not stated")]]
    rows += [["**Two-way physical feedbacks represented**", "", ""]] + [[lab, str(f[k]), pct(f[k], len(mv))] for k, lab in [("fb_none", "None"), ("fb_albedo", "Ground or crop albedo and bifacial gain"), ("fb_shade", "Shade, microclimate, and crop growth or water use"), ("fb_waterenergy", "Water balance or irrigation energy and PV energy"), ("fb_cool", "Crop cooling of modules"), ("fb_rain", "Rainfall redistribution by panels")]]
    SUP["model_structure"] = {"title": "Validation and Model Structure in the Studies Charted From Full Text", "header": ["Category", "Studies", "%"], "rows": rows,
        "note": f"Studies charted from full text that develop or use a virtual model (n = {len(mv)}). Fields coded from the full text with the protocol in Supplementary Material S4. Categories within the first and last blocks are multi-valued."}
_fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fieldmap_codes.json")
if os.path.exists(_fp):
    FMC = [v for v in json.load(open(_fp, encoding="utf-8")).values() if v["is_field_measurement"] == "yes"]
    f["n_fieldrec"] = len(FMC); f["fi_multi"] = sum(1 for v in FMC if v["duration"] == "more_than_one_season"); f["fi_arid"] = sum(1 for v in FMC if "B" in v["koppen_main"])
    f["fi_shared"] = sum(1 for v in FMC if v["data_shared"] == "yes"); f["fi_noclass"] = sum(1 for v in FMC if v["koppen_main"] == ["NR"])
    for v, lab in [("light_par", "par"), ("microclimate", "micro"), ("soil_moisture_or_water", "soil"), ("crop_yield", "yield"), ("crop_physiology_or_quality", "phys"), ("pv_output", "pv"), ("module_temperature", "modt")]:
        f[f"fi_{lab}"] = sum(1 for v2 in FMC if v in v2["variables_measured"])
    f["fi_full_set"] = sum(1 for v in FMC if all(x in v["variables_measured"] for x in ["light_par", "microclimate", "pv_output"]) and any(x in v["variables_measured"] for x in ["crop_yield", "crop_physiology_or_quality"]))
    rows = [[v["rid"], "; ".join(v["country"]), v["site"], "; ".join(v["koppen_main"]), v["configuration"], v["crop_or_livestock"], "; ".join(v["variables_measured"]), v["duration"], v["data_shared"]] for v in FMC]
    SUP["field_inventory"] = {"header": ["Record ID", "Country", "Site", "Köppen main class", "Configuration", "Crop or livestock", "Variables measured", "Duration", "Data shared"], "rows": rows}


# ---------- 9f. networked deployment, functions of shadows and twins, studies using the term ----------
f["n_any_networked"] = sum(1 for s in F if any(d in s["deployment"] for d in ONLINE_DEP)); f["pct_any_networked"] = pct(f["n_any_networked"], N)
f["n_offline_and_networked"] = sum(1 for s in F if "offline_desktop_or_server" in s["deployment"] and any(d in s["deployment"] for d in ONLINE_DEP))
_st = [s for s in F if s["dt_maturity"] in ("digital_shadow", "digital_twin")]
for fn, lab in [("prediction", "pred"), ("optimization_control", "opt"), ("monitoring_state_estimation", "mon")]:
    f[f"n_st_{lab}"] = sum(1 for s in _st if fn in s["dt_functions"])
_dt = [s for s in F if s.get("dt_term_used") == "yes"]
f["n_dt_term"] = len(_dt); f["n_dt_term_model"] = sum(1 for s in _dt if s["dt_maturity"] == "digital_model"); f["n_dt_term_na"] = sum(1 for s in _dt if s["dt_maturity"] == "NA")
f["dt_term_cites"] = "".join("{" + s["rid"] + "}" for s in sorted(_dt, key=lambda s: s.get("year") or 0))
SUP.setdefault("named_subsets", {"header": [], "rows": []})["rows"] += [["Uses the term digital twin", s["sid"], s.get("year"), "; ".join(s.get("country") or []), "; ".join(s["av_configuration"]), s["text_basis"], s["title"]] for s in _dt]
_kp = [s for s in F if s.get("mena") == "yes" and any(c in ("Saudi Arabia", "United Arab Emirates", "Qatar", "Kuwait", "Oman", "Bahrain") for c in (s.get("country") or []))]
f["n_gcc5"] = len(_kp); f["gcc_cites"] = "".join("{" + s["rid"] + "}" for s in _kp)


f["n_bwh"] = sum(1 for s in Bg if any((k or "").strip()[:3] == "BWh" for k in (s.get("koppen_subclass") or [])))
f["n_exp_inelig"] = round(int(f["pct_rech_excl"]) / 100 * len(abS)) if "pct_rech_excl" in f else 0
f["n_sim_site"] = sum(1 for s in site if s["study_type"] == "simulation_modeling"); f["pct_sim_site"] = pct(f["n_sim_site"], len(site))


_pp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preprint_ft.json")
_PRE = json.load(open(_pp)) if os.path.exists(_pp) else {}
f["n_preprint_ft"] = sum(1 for s in F if s["rid"] in _PRE and s["text_basis"] == "full_text")
f["preprint_cites"] = "".join("{" + s["rid"] + "}" for s in F if s["rid"] in _PRE and s["text_basis"] == "full_text")


# ---------- 9g. full-text core: full-text columns in Tables 6, 8, 9 and representativeness of the full-text subset ----------
import ast as _ast
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_tables.py"), encoding="utf-8").read()
_a = _src.index("LAB = {"); _b = _src.index("\n}\n", _a) + 2
_LAB = _ast.literal_eval(_src[_a + 6:_b].strip())
_REV = {v: k for k, v in _LAB.items()}
_BLOCKF = {"Data type": "data_types", "Sensing modality": "sensing_modalities", "Finest temporal resolution": "temporal_resolution", "Data duration": "data_duration",
           "Deployment": "deployment", "Real-time operation": "real_time", "Decision timescale": "decision_timescale", "Digital twin level, as designed": "dt_maturity",
           "Digital twin level, as demonstrated": "_demo", "Implementation status": "implementation_status", "Model updating from measurements": "data_assimilation",
           "Validation setting": "validation_setting", "Köppen-Geiger main class": "koppen_main", "Arid focus": None, "MENA site": None, "Most frequent countries": "country", "Arid subclasses": None}
_DEMO = {"None demonstrated": "none_demonstrated"}
def _has(s, field, key):
    v = s.get(field)
    return key in v if isinstance(v, list) else v == key
_nf = len(ftS)
for tk in ["T9_data", "T10_deployment", "T7_climate"]:
    if tk not in T: continue
    t = T[tk]; cur = None; newrows = []
    for r in t["rows"]:
        lab = r[0]
        if lab.startswith("**"):
            title = lab.strip("*"); cur = _BLOCKF.get(title, "?")
            if title == "Data or code shared publicly":
                n = sum(1 for s in ftS if s["data_or_code_available"] == "yes_public"); newrows.append(r + [str(n), pct(n, _nf)]); continue
            newrows.append(r + ["", ""]); continue
        n = ""
        if cur and cur != "?":
            key = _DEMO.get(lab) or _REV.get(lab) or ({"Not reported or not site-specific": "NR", "A, tropical": "A", "B, arid and semi-arid": "B", "C, temperate": "C", "D, continental": "D", "E, polar": "E"}.get(lab)) or lab
            if cur == "country":
                n = sum(1 for s in ftS if lab in (s.get("country") or []))
            else:
                n = sum(1 for s in ftS if _has(s, cur, key))
        newrows.append(r + ([str(n), pct(n, _nf)] if n != "" else ["", ""]))
    t["rows"] = newrows
    t["header"] = [t["header"][0], f"All studies (n = {N})", "%", f"Full text (n = {_nf})", "%"]
    t["widths"] = [4.2, 1.2, 0.8, 1.2, 0.8]
    t["note"] = t["note"] + f" The last two columns give the counts among the {_nf} studies charted from full text, which are the better guide for fields that abstracts rarely report (Table 5)."
    if tk == "T10_deployment" and "n_mech_model" in f:
        _vmL = sum(1 for s in ftS if s["dt_maturity"] != "NA")
        t["note"] += f" In the full-text core, {_vmL} studies have a virtual model by the level coding and {f['n_mech_model']} by the full-text model-structure coding (Supplementary Table S5.3); the two codings differ for {abs(_vmL - f['n_mech_model'])} studies."
# representativeness of the full-text subset
def _share(G, fn): return pct(sum(1 for s in G if fn(s)), len(G))
f["ftr_sim_ft"] = _share(ftS, lambda s: s["study_type"] == "simulation_modeling"); f["ftr_sim_abs"] = _share(abS, lambda s: s["study_type"] == "simulation_modeling")
f["ftr_recent_ft"] = _share(ftS, lambda s: (s.get("year") or 0) >= 2024); f["ftr_recent_abs"] = _share(abS, lambda s: (s.get("year") or 0) >= 2024)
f["ftr_conf_ft"] = _share(ftS, lambda s: s.get("venue_kind") == "conference"); f["ftr_conf_abs"] = _share(abS, lambda s: s.get("venue_kind") == "conference")
f["ftr_arid_ft"] = _share([s for s in ftS if s["koppen_main"] != ["NR"]], lambda s: "B" in s["koppen_main"]); f["ftr_arid_abs"] = _share([s for s in abS if s["koppen_main"] != ["NR"]], lambda s: "B" in s["koppen_main"])
f["ftr_op_ft"] = _share(ftS, lambda s: "operation" in s["decision_stage"]); f["ftr_op_abs"] = _share(abS, lambda s: "operation" in s["decision_stage"])
f["ftr_ieee_ft"] = _share(ftS, lambda s: (s.get("doi") or "").startswith("10.1109")); f["ftr_ieee_abs"] = _share(abS, lambda s: (s.get("doi") or "").startswith("10.1109"))
f["ftr_els_ft"] = _share(ftS, lambda s: (s.get("doi") or "").startswith("10.1016")); f["ftr_els_abs"] = _share(abS, lambda s: (s.get("doi") or "").startswith("10.1016"))
f["ftr_mdpi_ft"] = _share(ftS, lambda s: (s.get("doi") or "").startswith("10.3390")); f["ftr_mdpi_abs"] = _share(abS, lambda s: (s.get("doi") or "").startswith("10.3390"))
# full-text core headline facts
f["ftc_dm"] = sum(1 for s in ftS if s["dt_maturity"] == "digital_model"); f["ftc_vm"] = sum(1 for s in ftS if s["dt_maturity"] != "NA")
f["ftc_st"] = sum(1 for s in ftS if s["dt_maturity"] in ("digital_shadow", "digital_twin")); f["ftc_spec"] = sum(1 for s in ftS if s.get("physical_counterpart") == "specific_installation")
f["ftc_op"] = sum(1 for s in ftS if "operation" in s["decision_stage"]); f["pct_ftc_op"] = pct(f["ftc_op"], len(ftS))
f["ftc_class"] = sum(1 for s in ftS if s["koppen_main"] != ["NR"]); f["ftc_arid"] = sum(1 for s in ftS if "B" in s["koppen_main"])
f["ftc_temperate"] = sum(1 for s in ftS if "C" in s["koppen_main"])
f["ftc_networked"] = sum(1 for s in ftS if any(d in s["deployment"] for d in ONLINE_DEP)); f["pct_ftc_networked"] = pct(f["ftc_networked"], len(ftS))


# ---------- 9h. reliability of the full-text model-structure coding (independent second coder) ----------
_mb = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mechB_codes.json")
if os.path.exists(_mb) and os.path.exists(_mp):
    MB = json.load(open(_mb, encoding="utf-8")); MC2 = json.load(open(_mp, encoding="utf-8"))
    _r = [r for r in MB if r in MC2 and r in FM]
    _ks = []; _rows = []
    for fld in ["validation_independent", "validation_duration", "goodness_of_fit_reported", "crop_representation", "model_time_step", "operational_benefit_measured", "governance_or_security", "compute_footprint"]:
        pp = [(MC2[r][fld], MB[r][fld]) for r in _r]; k = kap(pp); _ks.append(k)
        _rows.append([fld, len(pp), f"{100 * sum(a == b for a, b in pp) / len(pp):.0f}%", f"{k:.2f}"])
    for fld in ["validated_subsystems", "feedbacks_represented"]:
        pp = [("none" in MC2[r][fld], "none" in MB[r][fld]) for r in _r]; k = kap(pp); _ks.append(k)
        jac = sum(len(set(MC2[r][fld]) & set(MB[r][fld])) / len(set(MC2[r][fld]) | set(MB[r][fld])) for r in _r) / len(_r)
        _rows.append([fld + " (any vs none; mean Jaccard)", len(pp), f"{100 * sum(a == b for a, b in pp) / len(pp):.0f}%; J = {jac:.2f}", f"{k:.2f}"])
    f["n_mechB"] = len(_r); f["kappa_mech_min"] = f"{min(_ks):.2f}"; f["kappa_mech_max"] = f"{max(_ks):.2f}"
    SUP["mech_agreement"] = {"header": ["Field", "Studies", "Raw agreement", "Cohen's kappa"], "rows": _rows}
_tc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ttl_check.json"); _te = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ttl_elig.json")
if os.path.exists(_tc) and os.path.exists(_te):
    TC = json.load(open(_tc, encoding="utf-8")); TE = json.load(open(_te, encoding="utf-8"))
    f["n_ttl_sample"] = len(TC); f["n_ttl_fw"] = sum(1 for v in TC.values() if v["decision"] == "FORWARD"); f["n_ttl_elig"] = sum(1 for v in TE.values() if v["eligible"] == "INCLUDE")


# ---------- 9i. readiness funnel (full-text core) and quote fidelity ----------
if os.path.exists(_mp):
    _MC = json.load(open(_mp, encoding="utf-8"))
    _core = [s for s in ftS if s["rid"] in _MC and "NA" not in _MC[s["rid"]]["validated_subsystems"]]
    _val = [s for s in _core if "none" not in _MC[s["rid"]]["validated_subsystems"]]
    _cpl = [s for s in _val if s.get("coupling") == "two_way_or_integrated" or "none" not in _MC[s["rid"]]["feedbacks_represented"]]
    _live = [s for s in _cpl if s["dt_maturity"] in ("digital_shadow", "digital_twin") or (s.get("audit_input") == "yes")]
    f["rf_model"] = len(_core); f["rf_val"] = len(_val); f["rf_cpl"] = len(_cpl); f["rf_live"] = len(_live)
    f["rf_live_word"] = "none" if len(_live) == 0 else str(len(_live))
    f["rf_val_live"] = sum(1 for s in _val if s["dt_maturity"] in ("digital_shadow", "digital_twin"))
_qc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quote_check.json")
if os.path.exists(_qc):
    Q = json.load(open(_qc, encoding="utf-8")); f["n_quotes"] = Q["n_quotes"]; f["n_quotes_ok"] = Q["n_quotes_ok"]; f["n_st_quotes"] = Q["n_st_quotes"]; f["n_st_quotes_ok"] = Q["n_st_quotes_ok"]


_xm = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xmodel_check.json")
if os.path.exists(_xm):
    XM = json.load(open(_xm, encoding="utf-8"))
    f["xm_n_scr"] = XM["screening"]["n"]; f["xm_n_cod"] = XM["eligibility"]["n"]; f["xm_n_inc"] = XM["level"]["n"]
    _kk = [v["kappa"] for v in XM.values()]; f["xm_kappa_min"] = f"{min(_kk):.2f}"; f["xm_kappa_max"] = f"{max(_kk):.2f}"
    for k, v in XM.items(): f[f"xm_{k}_kappa"] = f"{v['kappa']:.2f}"; f[f"xm_{k}_agree"] = v["agree"]
    SUP["xmodel"] = {"header": ["Decision", "Records", "Agreement", "Cohen's kappa"], "rows": [[k, v["n"], f"{v['agree']}/{v['n']}", f"{v['kappa']:.2f}"] for k, v in XM.items()]}


# ---------- 9j. readiness by decision (nested, capability-based), reweighting, demonstrated-level kappa ----------
if os.path.exists(_mp):
    _MC = json.load(open(_mp, encoding="utf-8"))
    _core = [s for s in ftS if s["rid"] in _MC and "NA" not in _MC[s["rid"]]["validated_subsystems"]]
    _V = lambda s: set(_MC[s["rid"]]["validated_subsystems"]) - {"none"}
    _fb = lambda s: s.get("coupling") == "two_way_or_integrated" or "none" not in _MC[s["rid"]]["feedbacks_represented"]
    _ln = lambda s: s.get("coupling") in ("one_way", "two_way_or_integrated") or _fb(s)
    _sp = lambda s: s.get("physical_counterpart") == "specific_installation"
    _des = lambda s: s["dt_maturity"] in ("digital_shadow", "digital_twin")
    _ind = lambda s: _MC[s["rid"]]["validation_independent"] == "yes"
    _TS = {"trk": {"sub_hourly", "hourly"}, "irr": {"sub_hourly", "hourly", "daily"}, "cln": {"sub_hourly", "hourly", "daily"}}
    _DEC = [("Tracking and shading control", "Light, PV output, crop", "A light or crop output, and PV output", lambda s: {"light_shading", "pv_energy", "crop"} <= set(s["subsystems"]), lambda v: bool(v & {"crop", "light_shading", "microclimate"}) and "pv_energy" in v, "trk"),
            ("Irrigation scheduling", "Water, crop", "A water or crop output", lambda s: {"water", "crop"} <= set(s["subsystems"]), lambda v: bool(v & {"water", "crop"}), "irr"),
            ("Module cleaning", "Soiling, PV output", "PV output or soiling", lambda s: {"soiling", "pv_energy"} <= set(s["subsystems"]), lambda v: bool(v & {"pv_energy", "soiling", "other"}), "cln")]
    _rows = []; _U = {k: set() for k in "abceg"}; _readyD = {}
    for lab, subs, outs, need, vok, key in _DEC:
        a = [s for s in _core if need(s)]; b = [s for s in a if vok(_V(s))]; c = [s for s in b if _ln(s)]; e = [s for s in c if _sp(s)]; g = [s for s in e if _des(s)]
        for nm, L in zip("abceg", [a, b, c, e, g]): f[f"rd_{key}_{nm}"] = len(L); _U[nm] |= {s["rid"] for s in L}
        f[f"rd_{key}_cites"] = "".join("{" + s["rid"] + "}" for s in e); f[f"rd_{key}_ts"] = sum(_MC[s["rid"]]["model_time_step"] in _TS[key] for s in e)
        _readyD.update({s["rid"]: key for s in e})
        _rows.append([lab, subs, outs, len(a), len(b), len(c), len(e), len(g)])
    _rows.append(["Any of the three decisions", "", "", len(_U["a"]), len(_U["b"]), len(_U["c"]), len(_U["e"]), len(_U["g"])])
    for nm in "abceg": f[f"rd_any_{nm}"] = len(_U[nm])
    _ready = [s for s in _core if s["rid"] in _U["e"]]
    f["rd_ready_cites"] = "".join("{" + s["rid"] + "}" for s in _ready)
    f["rd_ready_fb"] = sum(map(_fb, _ready)); f["rd_ready_indep"] = sum(map(_ind, _ready)); f["rd_ready_ts"] = sum(_MC[s["rid"]]["model_time_step"] in _TS[_readyD[s["rid"]]] for s in _ready)
    f["rd_ready_op"] = sum("operation" in s["decision_stage"] for s in _ready); f["rd_ready_arid"] = sum("B" in s["koppen_main"] for s in _ready)
    _ar = [s for s in _core if "B" in s["koppen_main"]]
    f["rd_arid_models"] = len(_ar); f["rd_arid_a"] = sum(s["rid"] in _U["a"] for s in _ar); f["rd_arid_b"] = sum(s["rid"] in _U["b"] for s in _ar); f["rd_arid_e"] = sum(s["rid"] in _U["e"] for s in _ar)
    f["rd_val_any"] = sum(1 for s in _core if _V(s)); f["rd_val_indep"] = sum(1 for s in _core if _V(s) and _ind(s))
    _conn = [s for s in _core if _des(s)]
    f["rd_conn"] = len(_conn); f["rd_conn_val"] = sum(1 for s in _conn if _V(s)); f["rd_conn_cpl"] = sum(1 for s in _conn if _fb(s)); f["rd_conn_cites"] = "".join("{" + s["rid"] + "}" for s in _conn)
    f["rd_conn_demo"] = sum(1 for s in _conn if s.get("_demo") in ("digital_shadow", "digital_twin"))
    _pv = 1 - f["rd_val_any"] / len(_core); f["rd_conn_p_noval"] = f"{_pv ** len(_conn):.2f}"
    # strict rule: every traded-off output validated with an error statistic, linked, specific installation, independent validation data, adequate time step
    _adjp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adjudications_readiness.json")
    _ADJ = json.load(open(_adjp, encoding="utf-8")) if os.path.exists(_adjp) else {}
    _gof = lambda s: _MC[s["rid"]]["goodness_of_fit_reported"] == "yes" and not (_ADJ.get(s["rid"], {}).get("condition", "").startswith("every traded-off"))
    _ind = lambda s: _MC[s["rid"]]["validation_independent"] == "yes" and not (_ADJ.get(s["rid"], {}).get("condition", "").startswith("validated on data independent"))
    f["n_adj_readiness"] = len(_ADJ)
    SUP["adjudications"] = {"header": ["Record ID", "Condition", "Result", "Reason"], "rows": [[k, v["condition"], v["result"], v["reason"]] for k, v in _ADJ.items()]}
    _VALL = {"trk": lambda v: "crop" in v and "pv_energy" in v, "irr": lambda v: "water" in v and "crop" in v, "cln": lambda v: "pv_energy" in v and "soiling" in v}
    _SU = {k: set() for k in "abceit"}; _srows = []
    _base = {"trk": f["rd_trk_e"], "irr": f["rd_irr_e"], "cln": f["rd_cln_e"]}
    for lab, subs, outs, need, vok, key in _DEC:
        a = [s for s in _core if need(s)]; b = [s for s in a if _VALL[key](_V(s)) and _gof(s)]; c = [s for s in b if _ln(s)]; e = [s for s in c if _sp(s)]
        i_ = [s for s in e if _ind(s)]; t_ = [s for s in i_ if _MC[s["rid"]]["model_time_step"] in _TS[key]]
        for nm, L in zip("abceit", [a, b, c, e, i_, t_]): f[f"rs_{key}_{nm}"] = len(L); _SU[nm] |= {s["rid"] for s in L}
        f[f"rs_{key}_vall"] = sum(1 for s in a if _VALL[key](_V(s)))
        _srows.append([lab, subs, len(a), len(b), len(c), len(e), len(i_), len(t_), _base[key]])
    _clnA = [s for s in _core if {"soiling", "pv_energy"} <= set(s["subsystems"])]
    f["rs_cln_pvonly_ready"] = sum(1 for s in _clnA if "pv_energy" in _V(s) and _MC[s["rid"]]["goodness_of_fit_reported"] == "yes" and _ln(s) and _sp(s) and (_MC[s["rid"]]["validation_independent"] == "yes" or s["rid"] == "R1200") and _MC[s["rid"]]["model_time_step"] in _TS["cln"])
    _srows.append(["Any of the three decisions", "", len(_SU["a"]), len(_SU["b"]), len(_SU["c"]), len(_SU["e"]), len(_SU["i"]), len(_SU["t"]), f["rd_any_e"]])
    for nm in "abceit": f[f"rs_any_{nm}"] = len(_SU[nm])
    f["rs_any_cites"] = "".join("{" + r + "}" for r in sorted(_SU["e"]))
    T["T15_readiness"] = {"caption": "Table 15 Readiness by Decision: Full-Text Models That Meet Each Successive Condition of the Strict Rule",
        "header": ["Decision", "Subsystems the decision trades off", "Model covers those subsystems", "Every traded-off output validated, with an error statistic", "Also links the subsystems in one model", "Also of a specific installation", "Also validated on data independent of calibration", "Also a time step fine enough for the decision (ready)", "For comparison: meets the base rule"],
        "widths": [1.3, 1.0, 0.9, 1.1, 0.9, 0.9, 1.0, 1.0, 0.9], "rows": _srows,
        "note": (f"Full-text core, {len(_core)} studies with a virtual model. Each column counts the studies in the previous column that also meet the stated condition, so each row nests; the 'any' row counts studies that meet the conditions for at least one decision. "
                 "Readiness is judged from the model's capability, whatever decision the study itself addresses. "
                 "Every traded-off output validated = crop and PV output for tracking and shading control; water and crop for irrigation; PV output and soiling loss for cleaning; each compared with field or laboratory measurements with a reported error statistic. "
                 "Links the subsystems = one-way or two-way coupling, or a physical feedback represented within one integrated model. "
                 "Time step fine enough = hourly or finer for tracking, daily or finer for irrigation and cleaning. "
                 "Base rule = covers the subsystems, at least one decision output validated against any measurements, linked, and of a specific installation (S5, Section Q). "
                 f"No model at any stage is designed to receive installation data automatically ({f['rd_any_g']}). "
                 "A recode of all candidates from the original PDFs, including tables and figures, also found no ready model after adjudication (S2, sheets 'PDF recheck' and 'PDF recheck summary').")}
    # arid contrasts restricted to studies of a specific, existing installation (removes simulated locations)
    _siteR = [s for s in ftS if s["koppen_main"] != ["NR"] and s.get("physical_counterpart") == "specific_installation"]
    _BR = [s for s in _siteR if "B" in s["koppen_main"]]; _NR = [s for s in _siteR if "B" not in s["koppen_main"]]
    f["n_BsiteR"] = len(_BR); f["n_otherR"] = len(_NR)
    f["n_arid_inst"] = len(_BR); f["arid_inst_cites"] = "".join("{" + s["rid"] + "}" for s in _BR)
    SUP["arid_installations"] = {"header": ["Record ID", "Title", "Country", "Köppen", "Study type", "Subsystems", "Measured data", "Soiling modeled", "Water modeled"],
        "rows": [[s["rid"], s["title"], ", ".join(s["country"]) if isinstance(s["country"], list) else s["country"], ", ".join(s.get("koppen_subclass") or s["koppen_main"]), s["study_type"], ", ".join(s["subsystems"]), "yes" if meas(s) else "no", "yes" if "soiling" in s["subsystems"] else "no", "yes" if "water" in s["subsystems"] else "no"] for s in _BR]}

    for k, (lab, fn) in IND.items():
        a = sum(fn(s) for s in _BR); c = sum(fn(s) for s in _NR)
        if _BR and _NR: f[f"c5r_{k}_pct"] = pct(a, len(_BR)); f[f"c5r_{k}_pct0"] = pct(c, len(_NR)); f[f"c5r_{k}_diff"] = ndiff(a, len(_BR), c, len(_NR))
_rw = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reweight.json")
if os.path.exists(_rw):
    RW = json.load(open(_rw, encoding="utf-8"))
    f["rw_ess"] = RW["ess"]; f["rw_max_shift"] = RW["max_shift"]; f["rw_trim_pct"] = RW.get("trim_pct", 95)
    f["rw_var_max"] = RW.get("variant_max_shift", ""); f["rw_n_lib"] = RW.get("n_lib", "")
    if "variants" in RW: SUP["reweight_variants"] = {"header": ["Variant"] + list(next(iter(RW["variants"].values())).keys()), "rows": [[k] + [f"{x}%" for x in d.values()] for k, d in RW["variants"].items()]}
    _nm = {"AI use": "ai", "Multi-season measured data": "ms", "Operational decisions": "op", "Real-time operation demonstrated": "rt", "Model compared with no measurements": "vnone", "Model validated and coupled": "vc"}
    for k, v in RW["ind"].items(): f[f"rw_{_nm[k]}"] = v["rw"]; f[f"rw_{_nm[k]}_ci"] = f"{v['lo']} to {v['hi']}"; f[f"rw_{_nm[k]}_raw"] = v["raw"]
    SUP["reweight"] = {"header": ["Indicator (full-text core)", "Studies", "Unweighted, n (%)", "Reweighted to the corpus, % (95% bootstrap CI)"], "rows": RW["rows"]}
    kd = RW["kappa"]["audit_designed"]; km = RW["kappa"]["audit_demonstrated"]
    f["audit_kappa_ci"] = f"{kd[1]:.2f} to {kd[2]:.2f}"; f["audit_kappa_demo"] = f"{km[0]:.2f}"; f["audit_kappa_demo_ci"] = f"{km[1]:.2f} to {km[2]:.2f}"


# ---------- 9k. external human reference, recheck, Korean sensitivity ----------
_AD = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(_AD, "ext_ref.json")):
    XR = json.load(open(os.path.join(_AD, "ext_ref.json"), encoding="utf-8")); _S = XR["summary"]
    _ft, _ab = _S["validation_pooled_ft"], _S["validation_pooled_abs"]
    f["xr_n_ft"] = _ft["n"]; f["xr_agree_ft"] = _ft["agree"]; f["xr_sens_ft"] = _ft["sens"].replace("/", " of "); f["xr_ppv_ft"] = _ft["ppv"].replace("/", " of ")
    f["xr_n_abs"] = _ab["n"]; f["xr_agree_abs"] = _ab["agree"]; f["xr_sens_abs"] = _ab["sens"].replace("/", " of ")
    f["xr_loc_agree"] = _S["pillai arid"]["country_agree"].replace("/", " of ")
    f["xr_retrieved"] = _S["n_cited_unique"]; f["xr_cited"] = _S["n_cited_unique"] + _S["n_not_retrieved"]; f["xr_included"] = _S["n_cited_included"]
    _rows = []
    for r in XR["rows"]:
        if r["rid"] is None and (r["ref_title"] or "").startswith("UNRESOLVED"): continue
        _rows.append([r["source"].split()[0].capitalize(), r.get("ref_no"), r.get("ref_title"), r.get("rid") or "not retrieved", r["status"], r.get("their_code"), (r.get("their_text") or "")[:300],
                      r.get("our_code") or (", ".join(r["our_country"]) if isinstance(r.get("our_country"), list) else (r.get("our_country") or "")), r.get("our_text_basis", "")])
    _rcp = os.path.join(_AD, "xr_recheck.json")
    if os.path.exists(_rcp):
        RC = json.load(open(_rcp, encoding="utf-8"))
        f["xr_recheck_n"] = len(RC); f["xr_recheck_confirmed"] = sum(1 for d in RC.values() if d["A"]["decision"] == d["B"]["decision"] == "EXCLUDE")
        f["xr_recheck_wrong"] = sum(1 for d in RC.values() if "INCLUDE" in (d["A"]["decision"], d["B"]["decision"]))
        f["xr_recheck_undecided"] = f["xr_recheck_n"] - f["xr_recheck_confirmed"] - f["xr_recheck_wrong"]
        for row in _rows:
            d = RC.get(row[3])
            row.append("" if not d else f"run A {d['A']['decision']} ({d['A']['criterion']}); run B {d['B']['decision']} ({d['B']['criterion']})")
    SUP["ext_ref"] = {"header": ["Review", "Ref. no. in review", "Cited study", "Record ID", "Status in this review", "Review's code", "Review's own words", "This review's code", "Text basis", "Blind recheck of exclusion"], "rows": _rows}
_kp = os.path.join(_AD, "korean_audit.json")
if os.path.exists(_kp):
    KR = json.load(open(_kp, encoding="utf-8"))
    f["kr_n"] = len(KR); f["kr_elig"] = sum(k["eligible_apart_from_language"] == "yes" for k in KR)
    f["kr_des_shadow"] = sum(k["designed_level"] in ("digital_shadow", "digital_twin") for k in KR); f["kr_demo_shadow"] = sum(k["demonstrated_level"] in ("digital_shadow", "digital_twin") for k in KR)
    f["kr_shadow_cites"] = "".join("{" + k["rid"] + "}" for k in KR if k["designed_level"] in ("digital_shadow", "digital_twin"))
    SUP["korean"] = {"header": ["Record ID", "Eligible apart from language", "Designed level", "Demonstrated level", "Implementation", "Automated input evidence (original and translation)", "Justification"],
                     "rows": [[k["rid"], k["eligible_apart_from_language"], k["designed_level"], k["demonstrated_level"], k["implementation_status"], k.get("automated_input_evidence", ""), k["justification"]] for k in KR]}


_rpp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_pool.json")
if os.path.exists(_rpp):
    RP = json.load(open(_rpp, encoding="utf-8")); _RR = {r["rid"]: r for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search", "records_v2_auto.json"), encoding="utf-8"))}
    _TOP = {"modeling_simulation", "ai_ml", "monitoring_sensing_iot", "digital_twin", "arid_or_mena"}
    f["rp_n"] = len(RP); f["rp_av"] = sum(r["agrivoltaic_focus"] in ("yes", "partly") for r in RP)
    f["rp_topic"] = sum(1 for r in RP if r["agrivoltaic_focus"] in ("yes", "partly") and set(r["topics"]) & _TOP)
    f["rp_twin"] = sum(r["codes_twin_levels"] in ("yes", "other_maturity_scale") for r in RP); f["rp_dt"] = sum("digital_twin" in r["topics"] for r in RP)
    f["rp_mena"] = sum("arid_or_mena" in r["topics"] for r in RP)
    SUP["review_pool"] = {"header": ["Record ID", "Title", "Year", "DOI", "Agrivoltaic focus", "Topics", "Codes studies by twin level", "Reason"],
                          "rows": [[r["rid"], _RR[r["rid"]].get("title"), _RR[r["rid"]].get("year"), _RR[r["rid"]].get("doi") or "", r["agrivoltaic_focus"], ", ".join(r["topics"]), r["codes_twin_levels"], r["reason"]] for r in RP]}


f["ft_vs_fieldlab"] = sum(1 for s in ftS if s["validation_setting"].startswith("field") or s["validation_setting"] == "laboratory_or_prototype")
_me = [s for s in F if s.get("mena") in ("yes", True)]
if _me:
    f["me_n"] = len(_me); f["me_sim"] = sum(s["study_type"] == "simulation_modeling" for s in _me); f["me_fexp"] = sum(s["study_type"] == "field_experiment_with_model" for s in _me)
    f["me_ft"] = sum(s["text_basis"] == "full_text" for s in _me); f["me_meas"] = sum(meas(s) for s in _me); f["me_ai"] = sum(s["ai_used"] == "yes" for s in _me)
    f["me_op"] = sum("operation" in s["decision_stage"] for s in _me); f["me_water"] = sum("water" in s["subsystems"] for s in _me); f["me_soil"] = sum("soiling" in s["subsystems"] for s in _me)
    f["me_ghouse"] = sum("pv_greenhouse" in (s["av_configuration"] if isinstance(s["av_configuration"], list) else [s["av_configuration"]]) for s in _me)
    f["me_hw"] = sum(s["implementation_status"] in ("prototype_or_testbed", "operating_installation") for s in _me); f["me_st"] = sum(s["dt_maturity"] in ("digital_shadow", "digital_twin") for s in _me)


_t1x = os.path.join(os.path.dirname(os.path.abspath(__file__)), "table1_extra.json")
if os.path.exists(_t1x):
    SUP["t1_extra"] = {"header": ["Review key", "Monitoring guidance", "Evidence", "Techno-economics", "Evidence"], "rows": [[r["key"], r["monitoring_guidance"], r["monitoring_evidence"], r["techno_economics"], r["techno_evidence"]] for r in json.load(open(_t1x, encoding="utf-8"))]}


_yrs = [(int(s["year"]), 1 if s["ai_used"] == "yes" else 0) for s in F if s.get("year")]
if _yrs:
    import math as _m
    _n = len(_yrs); _xm = sum(y for y, _ in _yrs) / _n; _p = sum(z for _, z in _yrs) / _n
    _T = sum((y - _xm) * z for y, z in _yrs); _VT = _p * (1 - _p) * sum((y - _xm) ** 2 for y, _ in _yrs)
    f["ai_trend_p"] = f"{_m.erfc(abs(_T / _m.sqrt(_VT)) / _m.sqrt(2)):.3f}"
_st8 = [s for s in F if s["dt_maturity"] in ("digital_shadow", "digital_twin")]
f["st_nexus"] = sum(1 for s in _st8 if set(s["subsystems"]) & {"pv_energy", "light_shading"} and "crop" in s["subsystems"]); f["st_pvlight"] = sum(1 for s in _st8 if set(s["subsystems"]) & {"pv_energy", "light_shading"})
f["n_rescued_incl"] = sum(1 for s in F if s.get("title_rescued"))


_prp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_recheck.json")
if os.path.exists(_prp):
    PR = json.load(open(_prp, encoding="utf-8")); _ag = {k: v for k, v in PR["agreement"].items() if k != "water validated"}
    f["pr_n"] = PR["n_recoded"]; f["pr_more"] = PR["pdf_more_validation"]; f["pr_less"] = PR["pdf_less_validation"]
    f["pr_agree_min"] = round(100 * min(v["agree"] for v in _ag.values()) / PR["n_recoded"]); f["pr_agree_max"] = round(100 * max(v["agree"] for v in PR["agreement"].values()) / PR["n_recoded"])
    f["pr_kappa_min"] = f"{min(v['kappa'] for v in _ag.values()):.2f}"; f["pr_kappa_max"] = f"{max(v['kappa'] for v in _ag.values()):.2f}"
    f["pr_kappa_link"] = f"{PR['agreement']['subsystems linked']['kappa']:.2f}"
    f["pr_ready_raw"] = PR["pdf_unadjudicated"]["any_ready"]; f["pr_ready"] = PR["pdf"]["any_ready"]; f["pr_base"] = PR["pdf"]["any_base"]
    f["pr_adj_cites"] = "".join("{" + r + "}" for r in PR["adjudicated"])
    _d = PR["pdf"]["drop_one"]; _k = list(_d.keys())
    f["pr_drop_val"] = _d[_k[0]]; f["pr_drop_ind"] = _d[_k[3]]; f["pr_drop_other"] = max(_d[_k[1]], _d[_k[2]], _d[_k[4]])
    _mg = PR["pdf"]["marginal"]; f["pr_marg_val"] = _mg[_k[0]]; f["pr_marg_ind"] = _mg[_k[3]]; f["pr_pairs"] = sum(PR["pdf"]["cand"].values())
    _rows = [["Text-based codes", PR["text"]["any_ready"], PR["text"]["any_base"]] + [PR["text"]["marginal"][k] for k in _k] + [PR["text"]["drop_one"][k] for k in _k],
             ["PDF recode, before adjudication", PR["pdf_unadjudicated"]["any_ready"], PR["pdf_unadjudicated"]["any_base"]] + [PR["pdf_unadjudicated"]["marginal"][k] for k in _k] + [PR["pdf_unadjudicated"]["drop_one"][k] for k in _k],
             ["PDF recode, adjudicated", PR["pdf"]["any_ready"], PR["pdf"]["any_base"]] + [PR["pdf"]["marginal"][k] for k in _k] + [PR["pdf"]["drop_one"][k] for k in _k]]
    SUP["pdf_recheck_summary"] = {"header": ["Coding", "Ready (strict rule)", "Meets the base rule"] + [f"Marginal: {k}" for k in _k] + [f"Ready if '{k}' is dropped" for k in _k], "rows": _rows}
    SUP["pdf_recheck"] = {"header": ["Record ID", "Title", "Validated outputs (text coding)", "Validated outputs (PDF recode)", "Outputs with an error statistic (PDF)", "Independent validation (PDF)", "Subsystems linked (PDF)", "Specific installation (PDF)", "Time step (PDF)", "Evidence (PDF)", "Recode basis"], "rows": PR["rows"]}
    f["pr_n_layout"] = PR.get("n_layout", 0); f["pr_n_rendered"] = PR.get("n_rendered", PR["n_recoded"])


_lr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search", "r2_rids.json")
if os.path.exists(_lr):
    _LR = json.load(open(_lr)); _Fr = {s["rid"] for s in F}
    f["n_lib_requested"] = 40; f["n_lib_obtained"] = len(_LR); f["n_lib_excluded"] = sum(1 for r in _LR if r not in _Fr)
    f["n_lib_risk"] = sum(1 for s in F if s["rid"] in _LR and s.get("twin_audited"))
    f["demo_twin_cites"] = "".join("{" + s["rid"] + "}" for s in F if s["dt_maturity"] == "digital_twin" and s.get("_demo") == "digital_twin")
    f["demo_shadow_cites"] = "".join("{" + s["rid"] + "}" for s in F if s.get("_demo") == "digital_shadow")
    f["borderline_twin_cites"] = "{R1384}"


# ---- additional analyses ----
if os.path.exists(_mp):
    _MCr = json.load(open(_mp, encoding="utf-8"))
    _coreM = [s for s in ftS if s["rid"] in _MCr and "NA" not in _MCr[s["rid"]]["validated_subsystems"]]
    _vs = lambda s: s["validation_setting"].startswith("field") or s["validation_setting"] == "laboratory_or_prototype"
    _mv = lambda s: s["rid"] in _MCr and bool(set(_MCr[s["rid"]]["validated_subsystems"]) - {"none", "NA"})
    f["vr_core"] = len(ftS); f["vr_vs"] = sum(map(_vs, ftS)); f["vr_mech"] = sum(map(_mv, ftS))
    f["vr_both"] = sum(1 for s in ftS if _vs(s) and _mv(s)); f["vr_vs_only"] = sum(1 for s in ftS if _vs(s) and not _mv(s)); f["vr_mech_only"] = sum(1 for s in ftS if _mv(s) and not _vs(s))
    f["vr_vs_nomodel"] = sum(1 for s in ftS if _vs(s) and (s["rid"] not in _MCr or "NA" in _MCr[s["rid"]]["validated_subsystems"]))
    SUP["validation_reconciliation"] = {"header": ["Full-text core", "Validated outputs in the model coding: yes", "Validated outputs in the model coding: no or no model"],
        "rows": [["Validation setting field or laboratory", f["vr_both"], f["vr_vs_only"]], ["Validation setting none or software only", f["vr_mech_only"], len(ftS) - f["vr_both"] - f["vr_vs_only"] - f["vr_mech_only"]]]}
_st10 = [s for s in F if s["dt_maturity"] in ("digital_shadow", "digital_twin")]
f["st_update"] = sum(1 for s in _st10 if s.get("data_assimilation") == "sequential_updating")
f["st_single"] = sum(1 for s in _st10 if len(set(s["subsystems"]) - {"economics"}) <= 1)
f["st_multi"] = len(_st10) - f["st_single"]
f["st_ft"] = sum(1 for s in _st10 if s["text_basis"] == "full_text")
f["st_core_model"] = f.get("rd_conn", 0); f["st_ft_nomodel"] = f["st_ft"] - f["st_core_model"]
_prp2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_recheck.json")
if os.path.exists(_prp2):
    _PR = json.load(open(_prp2, encoding="utf-8")); _mg = _PR["text"]["marginal"]; _kk = list(_mg.keys())
    f["rm_pairs"] = sum(_PR["text"]["cand"].values()); f["rm_val"] = _mg[_kk[0]]; f["rm_link"] = _mg[_kk[1]]; f["rm_spec"] = _mg[_kk[2]]; f["rm_ind"] = _mg[_kk[3]]; f["rm_ts"] = _mg[_kk[4]]
    _ag = _PR["agreement"]
    SUP["readiness_marginal"] = {"header": ["Condition (decision-candidate pairs)", "Pairs meeting it (text-based coding)", "Agreement with the PDF recode (field)", "Cohen's kappa"],
        "rows": [[_kk[0], _mg[_kk[0]], "error statistic reported", _ag["error statistic reported"]["kappa"]], [_kk[1], _mg[_kk[1]], "subsystems linked", _ag["subsystems linked"]["kappa"]],
                 [_kk[2], _mg[_kk[2]], "specific installation", _ag["specific installation"]["kappa"]], [_kk[3], _mg[_kk[3]], "independent validation", _ag["independent validation"]["kappa"]], [_kk[4], _mg[_kk[4]], "", ""]]}
_xr2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ext_ref.json")
if os.path.exists(_xr2):
    _XS = json.load(open(_xr2, encoding="utf-8"))
    _rws = [r for r in _XS["rows"] if r.get("status") == "included" and r.get("their_code") in ("field", "none", "software") and r.get("our_code")]
    _seen = {}
    for r in _rws: _seen.setdefault(r["rid"], r)
    _tab = []
    for basis in ("full_text", "abstract_only"):
        g = [r for r in _seen.values() if r.get("our_text_basis") == basis]
        mm = lambda x: "measured" if x == "field" else "not"
        a = sum(1 for r in g if mm(r["their_code"]) == "measured" and mm(r["our_code"]) == "measured"); b = sum(1 for r in g if mm(r["their_code"]) == "measured" and mm(r["our_code"]) != "measured")
        c = sum(1 for r in g if mm(r["their_code"]) != "measured" and mm(r["our_code"]) == "measured"); d = sum(1 for r in g if mm(r["their_code"]) != "measured" and mm(r["our_code"]) != "measured")
        _tab += [[basis.replace("_", " "), "Published review: validated against measurements", a, b], [basis.replace("_", " "), "Published review: not validated against measurements", c, d]]
    SUP["external_2x2"] = {"header": ["This review's text basis", "Published review's code", "This review: validated against measurements", "This review: not validated"], "rows": _tab}


_nep = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nonenglish_screen.json")
if os.path.exists(_nep):
    NE = json.load(open(_nep, encoding="utf-8")); _RRn = {r["rid"]: r for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search", "records_v2_auto.json"), encoding="utf-8"))}
    f["ne_n"] = NE["n"]; f["ne_elig"] = len(NE["both"]); f["ne_st"] = len(NE["st"]); f["ne_arid"] = len(NE["arid"])
    SUP["nonenglish"] = {"header": ["Record ID", "Title", "Year", "Run A", "Run B", "Possible shadow or twin", "Arid site", "Reason (run A)"],
        "rows": [[r, _RRn[r].get("title"), _RRn[r].get("year"), d.get("A", {}).get("decision", ""), d.get("B", {}).get("decision", ""), "yes" if r in NE["st"] else "no", "yes" if r in NE["arid"] else "no", d.get("A", {}).get("reason", "")] for r, d in NE["codes"].items()]}


_hcp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ra_check_results.json"); _hca = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hc_adjudications.json")
if os.path.exists(_hcp):
    HC = json.load(open(_hcp, encoding="utf-8")); _A = HC["partA"]; _names = {"Q1": "In scope", "Q2": "AI used", "Q3": "Model level", "Q4": "Model compared with measurements", "Q5": "Decisions addressed", "Q6": "Arid site"}
    f["hc_n"] = _A["Q1"][0]; _k = [v[2] for q, v in _A.items() if q != "Q1" and v[2] is not None]
    f["hc_kappa_min"] = f"{min(_k):.2f}"; f["hc_kappa_max"] = f"{max(_k):.2f}"
    for q, v in _A.items(): f[f"hc_{q.lower()}_agree"] = v[1]; f[f"hc_{q.lower()}_n"] = v[0]
    _pb = [x[1] for x in HC["partB"]]; f["hc_b_n"] = len(_pb); f["hc_b_agree"] = _pb.count("Agree"); f["hc_b_dis"] = _pb.count("Disagree"); f["hc_b_cant"] = len(_pb) - f["hc_b_agree"] - f["hc_b_dis"]
    _L = json.load(open(_hca, encoding="utf-8")) if os.path.exists(_hca) else []
    f["hc_changes"] = sum(1 for x in _L if x["change"] != "none"); f["hc_kept"] = sum(1 for x in _L if x["change"] == "none")
    SUP["hc_check"] = {"header": ["Question", "Studies compared", "Agreement", "Cohen's kappa"], "rows": [[_names[q], v[0], f"{v[1]}/{v[0]}", v[2] if v[2] is not None else "n/a"] for q, v in _A.items()]}
    SUP["hc_adjudications"] = {"header": ["Record ID", "Part", "Change made", "Reason"], "rows": [[x["rid"], x["part"], json.dumps(x["change"], ensure_ascii=False) if x["change"] != "none" else "none (review's code kept)", x["reason"]] for x in _L]}


_FA0 = {}
try:
    _FA0 = json.load(open(sys.argv[3], encoding="utf-8")) if os.path.exists(sys.argv[3]) else {}
except Exception:
    _FA0 = {}
def _g(k, d=""):
    return f.get(k, _FA0.get(k, d))
SUP["reliability_summary"] = {"header": ["Check", "Who or what", "Items", "Agreement or result"], "rows": [
    ["Title screening, two passes", "Two independent runs of Claude Opus 5.5", "all titles", f"kappa {_g('k_title')}"],
    ["Title-and-abstract screening, two passes", "Two independent runs of Claude Opus 5.5", "all screened abstracts", f"kappa {_g('k_abs')}"],
    ["Charting, double-coded sample", "Two independent runs of Claude Opus 5.5", f"{_g('n_double_sample')} reports", f"kappa {_g('kappa_min')} to {_g('kappa_max')} across {_g('n_kappa_fields')} fields (PABAK {_g('pabak_min')} to {_g('pabak_max')})"],
    ["Designed level, double coding", "Two independent runs of Claude Opus 5.5", f"{_g('twin_double_n')} studies", f"kappa {_g('twin_kappa')}"],
    ["Level audit of the risk set", "Two independent audit runs of Claude Opus 5.5", f"{_g('n_risk')} studies", f"kappa {_g('audit_kappa')} designed ({_g('audit_kappa_ci')}), {_g('audit_kappa_demo')} demonstrated ({_g('audit_kappa_demo_ci')})"],
    ["Model structure and validation, second run", "Second run of Claude Opus 5.5", f"{_g('n_mechB')} studies", f"kappa {_g('kappa_mech_min')} to {_g('kappa_mech_max')}"],
    ["Cross-model check", "Claude Sonnet 5.5 against the review's codes", f"{_g('xm_n_scr')} screening and {_g('xm_n_cod')} coding decisions", f"kappa {_g('xm_kappa_min')} to {_g('xm_kappa_max')}"],
    ["Readiness candidates recoded from the PDFs", "Claude Sonnet 5.5 against the text-based coding", f"{_g('pr_n')} candidates", f"kappa {_g('pr_kappa_min')} to {_g('pr_kappa_max')}"],
    ["Quotation check", "Script searching the source texts", f"{_g('n_quotes')} quotations", f"{_g('n_quotes_ok')} found verbatim"],
    ["Published human coding (validation)", "Codes tabulated in three published reviews", f"{_g('xr_n_ft')} full-text and {_g('xr_n_abs')} abstract-coded studies", f"{_g('xr_agree_ft')} and {_g('xr_agree_abs')} agree"],
    ["First author's check, Part A", "First author, by hand, without the review's codes", f"{_g('hc_n')} studies, 6 questions", f"scope {_g('hc_q1_agree')} of {_g('hc_q1_n')}; kappa {_g('hc_kappa_min')} to {_g('hc_kappa_max')} for the other questions"],
    ["First author's check, Part B", "First author, by hand, with page-cited quotations", f"{_g('hc_b_n')} decisive codes", f"{_g('hc_b_agree')} confirmed, {_g('hc_b_dis')} disputed, {_g('hc_b_cant')} could not be judged; {_g('hc_changes')} codes corrected after adjudication"]]}


# ---- additional analyses ----
import math as _mm
def _wilson_upper(k, n, z=1.96):
    if n == 0: return 1.0
    ph = k / n; den = 1 + z * z / n; c = ph + z * z / (2 * n); r = z * _mm.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return (c + r) / den
if os.path.exists(_mp):
    _MCq = json.load(open(_mp, encoding="utf-8"))
    _coreq = [s for s in ftS if s["rid"] in _MCq and "NA" not in _MCq[s["rid"]]["validated_subsystems"]]
    _Vq = lambda s: set(_MCq[s["rid"]]["validated_subsystems"]) - {"none"}
    _need = {"trk": ({"light_shading", "pv_energy", "crop"}, {"crop", "pv_energy"}, {"sub_hourly", "hourly"}), "irr": ({"water", "crop"}, {"water", "crop"}, {"sub_hourly", "hourly", "daily"}), "cln": ({"soiling", "pv_energy"}, {"pv_energy", "soiling"}, {"sub_hourly", "hourly", "daily"})}
    _adjq = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adjudications_readiness.json"); _ADJq = json.load(open(_adjq, encoding="utf-8")) if os.path.exists(_adjq) else {}
    _cand = [s for s in _coreq if any(n <= set(s["subsystems"]) for n, _, _ in _need.values())]
    def _meets(s, cond):
        for k, (n, outs, ts) in _need.items():
            if not n <= set(s["subsystems"]): continue
            if cond == "val" and outs <= _Vq(s) and _MCq[s["rid"]]["goodness_of_fit_reported"] == "yes" and not _ADJq.get(s["rid"], {}).get("condition", "").startswith("every traded-off"): return True
            if cond == "ts" and _MCq[s["rid"]]["model_time_step"] in ts: return True
        return False
    f["rmm_cand"] = len(_cand); f["rmm_val"] = sum(_meets(s, "val") for s in _cand)
    f["rmm_link"] = sum(1 for s in _cand if s.get("coupling") in ("one_way", "two_way_or_integrated") or "none" not in _MCq[s["rid"]]["feedbacks_represented"])
    f["rmm_spec"] = sum(1 for s in _cand if s.get("physical_counterpart") == "specific_installation")
    f["rmm_ind"] = sum(1 for s in _cand if _MCq[s["rid"]]["validation_independent"] == "yes" and not _ADJq.get(s["rid"], {}).get("condition", "").startswith("validated on data independent")); f["rmm_ts"] = sum(_meets(s, "ts") for s in _cand)
    f["ready_upper_all"] = f"{100 * _wilson_upper(0, len(_cand)):.0f}"; f["ready_upper_cln"] = f"{100 * _wilson_upper(0, f.get('rs_cln_a', 0) or 1):.0f}"
    f["ready_upper_irr"] = f"{100 * _wilson_upper(0, f.get('rs_irr_a', 0) or 1):.0f}"; f["ready_upper_trk"] = f"{100 * _wilson_upper(0, f.get('rs_trk_a', 0) or 1):.0f}"
    f["n_ben_measured"] = sum(1 for s in ftS if s["rid"] in _MCq and _MCq[s["rid"]].get("operational_benefit_measured") == "yes")
    f["ben_cites"] = "".join("{" + s["rid"] + "}" for s in ftS if s["rid"] in _MCq and _MCq[s["rid"]].get("operational_benefit_measured") == "yes")
# Holm adjustment of the Table 11 Fisher p-values
_pv = [(lab, float(str(pv).replace("<", "").replace("=", "").strip() or 1)) for lab, pv in pvals if str(pv).strip() not in ("", "–")]
_pv.sort(key=lambda x: x[1]); _m = len(_pv); _surv = []
for i, (lab, pv) in enumerate(_pv):
    if pv * (_m - i) < 0.05: _surv.append(lab)
    else: break
f["holm_n"] = len(_surv); f["holm_rows"] = "; ".join(x.lower() for x in _surv) if _surv else "none"; f["holm_m"] = _m
_prq = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_recheck.json")
if os.path.exists(_prq):
    _A = json.load(open(_prq, encoding="utf-8"))["agreement"]
    f["pr_kappa_ind"] = f"{_A['independent validation']['kappa']:.2f}"; f["pr_kappa_gof"] = f"{_A['error statistic reported']['kappa']:.2f}"


# ---- additional analyses ----
import random as _rnd, re
# (a) calibration by set: set 1 (studies verified because an open-access full text existed, independently of their abstract codes) versus set 2 (selected partly on abstract features)
_c1 = [(a, b) for a, b, k in pairs if k == 1]; _c2 = [(a, b) for a, b, k in pairs if k == 2]
_rows_set = []
for name, fn in FIELDS.items():
    r = [name]
    for P_ in (_c1, _c2):
        full = sum(fn(a) for a, _ in P_); both = sum(1 for a, b in P_ if fn(a) and fn(b))
        r.append(f"{both}/{full} ({pct(both, full)}%)" if full else "–")
    _rows_set.append(r)
SUP["calibration_by_set"] = {"header": ["Field", f"Sensitivity, set 1 (n = {len(_c1)})", f"Sensitivity, set 2 (n = {len(_c2)})"], "rows": _rows_set}
def _sens(P_, fn):
    full = sum(fn(a) for a, _ in P_); both = sum(1 for a, b in P_ if fn(a) and fn(b)); return both, full
for key, lab in [("rt", "Real-time operation demonstrated"), ("fv", "Field validation"), ("ai", "AI used")]:
    if lab in FIELDS:
        b1, n1 = _sens(_c1, FIELDS[lab]); b2, n2 = _sens(_c2, FIELDS[lab])
        f[f"cal1_{key}_sens"] = f"{b1} of {n1}"; f[f"cal2_{key}_sens"] = f"{b2} of {n2}"
f["cal_set1_n"] = len(_c1); f["cal_set2_n"] = len(_c2)
# (b) cluster-robust intervals for Table 11 (first-author clusters, core)
def _fa(s): return s["authors"][0].split()[-1].lower() if s.get("authors") else s["rid"]
_grp = {}
for s in op6: _grp.setdefault(_fa(s), []).append((s, 1))
for s in des6: _grp.setdefault(_fa(s), []).append((s, 0))
_keys = list(_grp); _rg = _rnd.Random(20261126); _cl_rows = []; _changed = 0
for lab, fn in INDO.items():
    a = sum(fn(s) for s in op6); c = sum(fn(s) for s in des6)
    if not (a + c): continue
    diffs = []
    for _ in range(1000):
        samp = [x for k in (_rg.choice(_keys) for _ in _keys) for x in _grp[k]]
        o = [s for s, g in samp if g == 1]; d = [s for s, g in samp if g == 0]
        if o and d: diffs.append(sum(fn(s) for s in o) / len(o) - sum(fn(s) for s in d) / len(d))
    diffs.sort(); lo = diffs[int(0.025 * len(diffs))]; hi = diffs[int(0.975 * len(diffs)) - 1]
    nd = ndiff(a, len(op6), c, len(des6)); m = re.match(r"([+−-]?\d+) \(([+−-]?\d+) to ([+−-]?\d+)\)", nd)
    g = lambda x: -int(x[1:]) if x.startswith("−") else int(x.replace("+", ""))
    sig_n = m and (g(m.group(2)) > 0 or g(m.group(3)) < 0); sig_c = lo > 0 or hi < 0
    _changed += (bool(sig_n) != bool(sig_c))
    _cl_rows.append([lab, nd, f"{100 * lo:+.0f} to {100 * hi:+.0f}".replace("-", "−"), "yes" if sig_n else "no", "yes" if sig_c else "no"])
SUP["cluster_robust"] = {"header": ["Indicator (full-text core)", "Difference, percentage points (Newcombe 95% CI)", "Cluster bootstrap 95% CI (first-author clusters)", "Interval excludes zero (Newcombe)", "Interval excludes zero (cluster)"], "rows": _cl_rows}
f["cl_changed"] = _changed; f["cl_n"] = len(_cl_rows); f["cl_clusters"] = len(_keys)
# (c) arid contrasts stratified by study type, within the full-text core
_simF = [s for s in siteF if s["study_type"] == "simulation_modeling"]; _nsF = [s for s in siteF if s["study_type"] != "simulation_modeling"]
for key, lab in [("meas", "meas"), ("fv", "fv")]:
    fn = IND[lab][1] if lab in IND else None
    if not fn: continue
    for nm, G in (("sim", _simF), ("nonsim", _nsF)):
        A_ = [s for s in G if "B" in s["koppen_main"]]; N_ = [s for s in G if "B" not in s["koppen_main"]]
        f[f"c5s_{key}_{nm}_n"] = f"{len(A_)} and {len(N_)}"
        if A_ and N_: f[f"c5s_{key}_{nm}_diff"] = ndiff(sum(fn(s) for s in A_), len(A_), sum(fn(s) for s in N_), len(N_))
f["n_simF_arid"] = sum(1 for s in _simF if "B" in s["koppen_main"]); f["n_nsF_arid"] = sum(1 for s in _nsF if "B" in s["koppen_main"])

# ---------- 10. miscellaneous reconciliations ----------
f["n_validation_multi"] = sum(s["validation_setting"] == "field_measurements_multi_site" for s in F)
f["n_calibrated"] = sum(s.get("data_assimilation") in ("calibration_only", "sequential_updating") for s in F); f["pct_calibrated"] = pct(f["n_calibrated"], N)
f["n_calibrated_nomeas"] = sum(1 for s in F if s.get("data_assimilation") in ("calibration_only", "sequential_updating") and not meas(s))
def _yr(s):
    y = s.get("year")
    if not y:
        pdt = (RECS.get(s["rid"], {}).get("pub_date") or "")[:4]
        y = int(pdt) if pdt.isdigit() else None
    return y
bins = {"up to 2021": lambda y: y is not None and y <= 2021, "from 2022 to 2023": lambda y: y in (2022, 2023), "from 2024 to 2026": lambda y: y is not None and y >= 2024}
abp = {k: [sum(1 for s in F if fn(_yr(s)) and s["ai_used"] == "yes"), sum(1 for s in F if fn(_yr(s)))] for k, fn in bins.items()}
f["n_noyear"] = sum(1 for s in F if _yr(s) is None)
f["ai_period_sentence2"] = "The share of studies using AI rose from " + ", to ".join(f"{v[0]} of {v[1]} {k} ({pct(*v)}%)" for k, v in abp.items() if v[1]) + "."
f["n_2026"] = sum(1 for s in F if s.get("year") == 2026)
cc = collections.Counter(c.strip() for s in F for c in set(s.get("country") or []) if c.strip() and c.strip() not in ("NR", "none", "NA"))
top = cc.most_common(); cut = top[9][1] if len(top) >= 10 else 0
f["top_countries2"] = join([f"{c} ({n})" for c, n in top if n >= cut])
json.dump(f, open(SUPP_OUT.replace(".json", "_facts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
_coll = {k: (FA[k], f[k]) for k in f if k in FA and str(FA[k]) != str(f[k])}
print("COLLISIONS", {k: v for k, v in _coll.items()})
FA.update(f)
json.dump(FA, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(T, open(sys.argv[5], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(SUP, open(SUPP_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("v5 facts", len(f)); print({k: f[k] for k in ["n_des_shadow", "n_des_twin", "n_demo_shadow", "n_demo_shadow_op", "n_demo_twin", "n_risk", "n_risk_ft", "n_risk_ftchg", "audit_kappa", "cal_n", "n_ft_now", "pct_ft_now", "corr_ai", "corr_ai_ci", "corr_fv", "corr_fv_ci", "power_ai", "n_Bsite", "n_class", "pct_Bsite_of_class", "op_cluster_same_dir", "op_cluster_tested", "kappa_min", "kappa_max"]})
