import json, sys, collections
from parse_journal import load
J = sys.argv[1]; rnd = sys.argv[2]
o = load(J)
rids = json.load(open(f"round{rnd}_rids.json"))
A, B = {}, {}
for lab, v in o.items():
    tgt = A if " A" in lab else B
    for d in (v or {}).get("decisions", []):
        tgt[d["rid"]] = (d["decision"], d["code"])
missA = [r for r in rids if r not in A]; missB = [r for r in rids if r not in B]
extra = [r for r in list(A) + list(B) if r not in set(rids)]
print("missing A", len(missA), "missing B", len(missB), "unknown ids", len(extra))
both = [r for r in rids if r in A and r in B]
n = len(both); a_k = sum(A[r][0] == "KEEP" for r in both); b_k = sum(B[r][0] == "KEEP" for r in both)
agree = sum(A[r][0] == B[r][0] for r in both)
po = agree / n; pe = (a_k / n) * (b_k / n) + (1 - a_k / n) * (1 - b_k / n)
kappa = (po - pe) / (1 - pe)
print(f"n={n} A keep={a_k} B keep={b_k} agreement={po:.3f} kappa={kappa:.3f}")
res = {}
for r in rids:
    da, db = A.get(r), B.get(r)
    if da is None or db is None:
        res[r] = {"title_decision": "KEEP", "note": "missing decision, kept"}
    elif da[0] == "EXCLUDE" and db[0] == "EXCLUDE":
        res[r] = {"title_decision": "EXCLUDE", "code": da[1] if da[1] == db[1] else min(da[1], db[1]), "codes": [da[1], db[1]]}
    else:
        res[r] = {"title_decision": "KEEP", "disagree": da[0] != db[0]}
c = collections.Counter(v["title_decision"] for v in res.values())
print(c, collections.Counter(v.get("code") for v in res.values() if v["title_decision"] == "EXCLUDE"))
json.dump({"A": A, "B": B, "combined": res, "kappa": kappa, "agreement": po, "n": n}, open(f"title_r{rnd}_results.json", "w"))
