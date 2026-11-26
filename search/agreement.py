import json, sys, collections
C = json.load(open(sys.argv[1]))
A, B = C["A"], C["B"]
both = [r for r in B if r in A]
def kappa(pairs):
    n = len(pairs)
    if n == 0: return None, None
    cats = set(a for a, _ in pairs) | set(b for _, b in pairs)
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return po, ((po - pe) / (1 - pe) if pe < 1 else 1.0)
res = {"n_double": len(both)}
res["eligible"] = kappa([(A[r]["eligible"], B[r]["eligible"]) for r in both])
inc = [r for r in both if A[r]["eligible"] == "INCLUDE" and B[r]["eligible"] == "INCLUDE"]
res["n_both_included"] = len(inc)
for f in ["ai_used", "dt_maturity", "arid_focus", "mena", "validation_setting", "study_type", "dt_term_used", "real_time", "temporal_resolution"]:
    res[f] = kappa([(A[r][f], B[r][f]) for r in inc])
def jacc(a, b):
    a, b = set(a), set(b)
    return None if not a and not b else len(a & b) / len(a | b)
for f in ["dt_functions", "method_families", "data_types", "sensing_modalities", "deployment", "subsystems", "koppen_main", "decision_timescale"]:
    vals = [v for v in (jacc(A[r][f], B[r][f]) for r in inc) if v is not None]
    res[f + "_jaccard"] = sum(vals) / len(vals) if vals else None
res["eligibility_disagreements"] = [r for r in both if A[r]["eligible"] != B[r]["eligible"]]
json.dump(res, open(sys.argv[2], "w"), indent=1)
for k, v in res.items(): print(k, v if not isinstance(v, tuple) else (round(v[0], 3), round(v[1], 3)))
