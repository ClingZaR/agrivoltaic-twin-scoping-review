"""Inverse-probability reweighting of the full-text core to the whole corpus (publisher group, venue kind, year bin),
plus bootstrap CIs for the agreement statistics. Writes reweight.json."""
import json, os, random, math
import numpy as np
AN = os.path.dirname(os.path.abspath(__file__))
F = json.load(open(os.path.join(AN, "final_v5.json"), encoding="utf-8"))
M = json.load(open(os.path.join(AN, "mech_codes.json"), encoding="utf-8"))
def pub(s):
    d = (s.get("doi") or "").lower()
    for p, n in [("10.3390", "MDPI"), ("10.1016", "Elsevier"), ("10.1109", "IEEE"), ("10.1007", "Springer"), ("10.1063", "AIP")]:
        if d.startswith(p): return n
    return "other"
EUR = {"Italy", "Germany", "France", "Spain", "Sweden", "Netherlands", "Belgium", "Switzerland", "Austria", "Portugal", "Greece", "Denmark", "Norway", "Finland", "Ireland", "United Kingdom", "Poland", "Czech Republic", "Hungary", "Romania", "Croatia", "Slovenia", "Slovakia", "Serbia", "Lithuania", "Latvia", "Estonia", "Bulgaria", "Cyprus", "Malta", "Ukraine", "Turkey"}
MENA = {"Egypt", "Saudi Arabia", "United Arab Emirates", "Qatar", "Oman", "Kuwait", "Bahrain", "Jordan", "Israel", "Morocco", "Algeria", "Tunisia", "Libya", "Iran", "Iraq", "Lebanon", "Syria", "Palestine", "Yemen"}
SAS = {"India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal"}
def region(s):
    c = s.get("country") or []; c = c if isinstance(c, list) else [c]
    if any(x in MENA for x in c): return "MENA"
    if any(x in SAS for x in c): return "South Asia"
    if any(x in EUR for x in c): return "Europe"
    if not c or c == ["NR"]: return "NR"
    return "other"
def ybin(s):
    y = int(s.get("year") or 2022)
    return "<=2020" if y <= 2020 else ("2021-2023" if y <= 2023 else ">=2024")
levels = {"reg": ["Europe", "MENA", "South Asia", "other", "NR"], "pub": ["MDPI", "Elsevier", "IEEE", "Springer", "AIP", "other"], "kind": ["journal", "conference"], "y": ["<=2020", "2021-2023", ">=2024"]}
def x(s):
    v = [1.0]
    v += [1.0 if pub(s) == l else 0.0 for l in levels["pub"][1:]]
    v += [1.0 if (s.get("venue_kind") or "journal") == "conference" else 0.0]
    v += [1.0 if region(s) == l else 0.0 for l in levels["reg"][1:]]
    v += [1.0 if ybin(s) == l else 0.0 for l in levels["y"][1:]]
    return v
X = np.array([x(s) for s in F]); yv = np.array([1.0 if s["text_basis"] == "full_text" else 0.0 for s in F])
b = np.zeros(X.shape[1])
for _ in range(200):  # ridge-penalized logistic regression by Newton steps
    p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p)
    H = X.T @ (X * W[:, None]) + 0.1 * np.eye(len(b)); g = X.T @ (yv - p) - 0.1 * b
    step = np.linalg.solve(H, g); b += step
    if np.max(np.abs(step)) < 1e-8: break
p = 1 / (1 + np.exp(-X @ b))
ft = [i for i, s in enumerate(F) if s["text_basis"] == "full_text"]
_raw = np.array([1 / p[i] for i in ft]); _cap = float(np.percentile(_raw, 95)); TRIM = int((_raw > _cap).sum())
w = {F[i]["rid"]: min(1 / p[i], _cap) for i in ft}
ws = np.array([w[F[i]["rid"]] for i in ft]); ess = ws.sum() ** 2 / (ws ** 2).sum()
FT = [F[i] for i in ft]
MEAS = ["in_situ_environmental_sensors", "soil_sensors", "pv_monitoring", "plant_sensors_or_manual_crop_sampling", "imaging_rgb_multispectral_thermal", "satellite", "uav", "iot_wireless_network"]
meas = lambda s: any(m in s["sensing_modalities"] for m in MEAS)
def V(s): return set(M.get(s["rid"], {}).get("validated_subsystems", ["NA"])) - {"none"}
model = lambda s: s["rid"] in M and "NA" not in M[s["rid"]]["validated_subsystems"]
IND = {
    "AI use": (lambda s: True, lambda s: s["ai_used"] == "yes"),
    "Multi-season measured data": (lambda s: True, lambda s: s.get("data_duration") == "multi_season_or_multi_year" and meas(s)),
    "Operational decisions": (lambda s: True, lambda s: "operation" in s["decision_stage"]),
    "Real-time operation demonstrated": (lambda s: True, lambda s: s.get("real_time") == "real_time_operation_demonstrated"),
    "Model compared with no measurements": (model, lambda s: not V(s)),
    "Model validated and coupled": (model, lambda s: bool(V(s)) and (s["coupling"] == "two_way_or_integrated" or "none" not in M[s["rid"]]["feedbacks_represented"])),
}
rng = np.random.default_rng(20261125)
rows = []; out = {}
for name, (den, num) in IND.items():
    S = [s for s in FT if den(s)]; n = len(S); k = sum(num(s) for s in S)
    wv = np.array([w[s["rid"]] for s in S]); yy = np.array([1.0 if num(s) else 0.0 for s in S])
    est = (wv * yy).sum() / wv.sum()
    bs = []
    for _ in range(2000):
        ix = rng.integers(0, n, n); bs.append((wv[ix] * yy[ix]).sum() / wv[ix].sum())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    rows.append([name, n, f"{k} ({100 * k / n:.0f}%)", f"{100 * est:.0f}% ({100 * lo:.0f} to {100 * hi:.0f})"])
    out[name] = {"n": n, "k": k, "raw": round(100 * k / n), "rw": round(100 * est), "lo": round(100 * lo), "hi": round(100 * hi)}
mx = max(abs(v["rw"] - v["raw"]) for v in out.values())
# bootstrap CIs for kappa
def kap(pp):
    n = len(pp); po = sum(a == b for a, b in pp) / n; cs = set(a for a, _ in pp) | set(b for _, b in pp)
    pe = sum((sum(a == c for a, _ in pp) / n) * (sum(b == c for _, b in pp) / n) for c in cs)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")
def kci(pp, B=2000):
    r = random.Random(7); ks = []
    for _ in range(B):
        q = [pp[r.randrange(len(pp))] for _ in pp]; k = kap(q)
        if not math.isnan(k): ks.append(k)
    ks.sort(); return ks[int(0.025 * len(ks))], ks[int(0.975 * len(ks)) - 1]
aud = [s for s in F if s.get("twin_audited")]
dpp = [(s["audit_d1"], s["audit_d2"]) for s in aud]; mpp = [(s["audit_m1"], s["audit_m2"]) for s in aud]
K = {"audit_designed": (kap(dpp),) + kci(dpp), "audit_demonstrated": (kap(mpp),) + kci(mpp)}
json.dump({"rows": rows, "ind": out, "ess": round(float(ess)), "trimmed": TRIM, "trim_pct": 95, "max_shift": int(mx), "n_ft": len(FT),
           "kappa": {k: [round(v, 2) for v in t] for k, t in K.items()}, "n_audit": len(aud),
           "audit_demo_agree": sum(a == b for a, b in mpp), "audit_des_agree": sum(a == b for a, b in dpp)},
          open(os.path.join(AN, "reweight.json"), "w"), indent=1)
for r in rows: print(r)
print("ESS", round(float(ess)), "max shift", mx, "kappa", K)

# ---- additional analyses ----
LIB = set(json.load(open(os.path.join(AN, "..", "search", "r2_rids.json")))) if os.path.exists(os.path.join(AN, "..", "search", "r2_rids.json")) else set()
def fit(Xm, yv):
    bb = np.zeros(Xm.shape[1])
    for _ in range(200):
        pp = 1 / (1 + np.exp(-Xm @ bb)); W = pp * (1 - pp)
        H = Xm.T @ (Xm * W[:, None]) + 0.1 * np.eye(len(bb)); g = Xm.T @ (yv - pp) - 0.1 * bb
        st = np.linalg.solve(H, g); bb += st
        if np.max(np.abs(st)) < 1e-8: break
    return 1 / (1 + np.exp(-Xm @ bb))
def shares(FTs, wmap):
    out2 = {}
    for name, (den, num) in IND.items():
        S_ = [s for s in FTs if den(s)]
        if not S_: continue
        wv = np.array([wmap[s["rid"]] for s in S_]); yy = np.array([1.0 if num(s) else 0.0 for s in S_])
        out2[name] = round(100 * (wv * yy).sum() / wv.sum())
    return out2
VARIANTS = {}
Xr = np.column_stack([X, np.array([1.0 if s.get("twin_audited") else 0.0 for s in F])]); pr_ = fit(Xr, yv)
rawr = np.array([1 / pr_[i] for i in ft]); capr = float(np.percentile(rawr, 95)); wr = {F[i]["rid"]: min(1 / pr_[i], capr) for i in ft}
VARIANTS["with risk-set covariate"] = shares(FT, wr)
keep = [i for i, s in enumerate(F) if s["rid"] not in LIB]; Xk = X[keep]; yk = yv[keep]; pk = fit(Xk, yk)
ftk = [j for j, i in enumerate(keep) if F[i]["text_basis"] == "full_text"]
rawk = np.array([1 / pk[j] for j in ftk]); capk = float(np.percentile(rawk, 95)); wk = {F[keep[j]]["rid"]: min(1 / pk[j], capk) for j in ftk}
FTk = [F[keep[j]] for j in ftk]
VARIANTS["without library-obtained studies"] = shares(FTk, wk)
VARIANTS["without library-obtained studies, unweighted"] = shares(FTk, {s["rid"]: 1.0 for s in FTk})
base = {k: v["rw"] for k, v in out.items()}
R = json.load(open(os.path.join(AN, "reweight.json")))
R["variants"] = VARIANTS; R["variant_max_shift"] = int(max(abs(VARIANTS[v][k] - base[k]) for v in VARIANTS for k in VARIANTS[v] if k in base)); R["n_lib"] = len(LIB & {s["rid"] for s in FT})
json.dump(R, open(os.path.join(AN, "reweight.json"), "w"), indent=1)
print("variants", VARIANTS, "max shift vs main reweighting", R["variant_max_shift"])
