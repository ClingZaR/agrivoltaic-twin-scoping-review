import json, sys, collections
from parse_journal import load
J, rnd = sys.argv[1], sys.argv[2]
o = load(J); rids = json.load(open(f"abs_r{rnd}_rids.json"))
A, B = {}, {}
for lab, v in o.items():
    tgt = A if " A" in lab else B
    for d in (v or {}).get("decisions", []): tgt[d["rid"]] = d
print("missing A", sum(r not in A for r in rids), "missing B", sum(r not in B for r in rids))
both = [r for r in rids if r in A and r in B]
# kappa on 3 categories and on binary (exclude vs not)
def kappa(pairs, cats):
    n = len(pairs); po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return po, (po - pe) / (1 - pe)
p3 = [(A[r]["decision"], B[r]["decision"]) for r in both]
p2 = [(a == "EXCLUDE", b == "EXCLUDE") for a, b in p3]
print("3-cat agreement/kappa", kappa(p3, ["INCLUDE", "MAYBE", "EXCLUDE"]))
print("binary agreement/kappa", kappa(p2, [True, False]))
print("A", collections.Counter(a for a, _ in p3), "B", collections.Counter(b for _, b in p3))
res = {}
for r in rids:
    a, b = A.get(r), B.get(r)
    if a and b and a["decision"] == "EXCLUDE" and b["decision"] == "EXCLUDE":
        res[r] = {"abs_decision": "EXCLUDE", "code": min(a["code"] or "E9", b["code"] or "E9"), "codes": [a["code"], b["code"]]}
    else:
        ds = sorted([x["decision"] for x in (a, b) if x])
        res[r] = {"abs_decision": "FULLTEXT", "votes": ds, "enabler": [x.get("enabler") for x in (a, b) if x]}
c = collections.Counter(v["abs_decision"] for v in res.values())
print(c, collections.Counter(v.get("code") for v in res.values() if v["abs_decision"] == "EXCLUDE"))
print(collections.Counter(tuple(v["votes"]) for v in res.values() if v["abs_decision"] == "FULLTEXT"))
json.dump({"A": A, "B": B, "combined": res, "kappa3": kappa(p3, ["INCLUDE", "MAYBE", "EXCLUDE"]), "kappa2": kappa(p2, [True, False])}, open(f"abs_r{rnd}_results.json", "w"))
