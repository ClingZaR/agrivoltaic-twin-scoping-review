"""Compute PRISMA-ScR flow numbers and screening record across all rounds.
Usage: flow.py charts_final.json final.json out_flow.json out_screening.json raw_counts.json"""
import json, sys, glob, collections
CH = json.load(open(sys.argv[1], encoding="utf-8")); FINAL = json.load(open(sys.argv[2], encoding="utf-8"))
RAW = json.load(open(sys.argv[5], encoding="utf-8"))  # list of [source, search, fields, date, n]
R = {r["rid"]: r for r in json.load(open("records_v2_auto.json", encoding="utf-8"))}
log = json.load(open("../fulltext/fetch_log.json"))
T, A = {}, {}
TA, TB, AA, AB = {}, {}, {}, {}
for f in sorted(glob.glob("title_r*_results.json")):
    d = json.load(open(f)); T.update(d["combined"]); TA.update(d["A"]); TB.update(d["B"])
for f in sorted(glob.glob("abs_r*_results.json")):
    d = json.load(open(f)); A.update(d["combined"]); AA.update({k: v["decision"] for k, v in d["A"].items()}); AB.update({k: v["decision"] for k, v in d["B"].items()})
def kappa(pairs):
    n = len(pairs); cats = set(a for a, _ in pairs) | set(b for _, b in pairs)
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return po, (po - pe) / (1 - pe)
tk = kappa([(TA[r][0], TB[r][0]) for r in T if r in TA and r in TB])
ak = kappa([(AA[r] == "EXCLUDE", AB[r] == "EXCLUDE") for r in A if r in AA and r in AB])
auto = collections.Counter(r["auto_exclusion"] for r in R.values() if r.get("auto_exclusion") and r.get("sources") != ["Citation searching"])
n_unique = sum(1 for r in R.values() if r.get("sources") != ["Citation searching"]); n_auto = sum(auto.values())
n_raw = sum(x[4] for x in RAW)
title_screened = [r for r in T]; title_excl = [r for r, v in T.items() if v["title_decision"] == "EXCLUDE"]
abs_screened = [r for r, v in T.items() if v["title_decision"] == "KEEP"]
abs_excl = [r for r in abs_screened if A.get(r, {}).get("abs_decision") == "EXCLUDE"]
sought_db = [r for r in abs_screened if A.get(r, {}).get("abs_decision") == "FULLTEXT"]
import os as _os
RS = json.load(open("title_rescreen.json", encoding="utf-8")) if _os.path.exists("title_rescreen.json") else {}
rescreened = [r for r in title_excl if r in RS]
rescued = [r for r in rescreened if RS[r]["decision"] == "FORWARD"]
sought_db = sought_db + rescued
cit = [rid for rid, r in R.items() if r.get("sources") == ["Citation searching"]]
cit_auto = [rid for rid in cit if R[rid].get("auto_exclusion")]
cit_sought = [rid for rid in cit if not R[rid].get("auto_exclusion")]
sought = sought_db + cit_sought
assessed = [r for r in sought if r in CH["A"]]
# not retrieved: sought but never charted (no abstract and no full text), or charted as E6 title-only
nr = [r for r in sought if r not in CH["A"]]
e6 = [r for r in assessed if (CH["ADJ"].get(r, {}).get("eligible") or CH["A"][r]["eligible"]) == "EXCLUDE" and CH["A"][r]["exclusion_code"] == "E6" and CH["A"][r]["text_basis"] == "title_only"]
not_retrieved = nr + e6
assessed = [r for r in assessed if r not in e6]
def final_elig(r):
    adj = CH["ADJ"].get(r, {})
    return adj.get("eligible") or CH["A"][r]["eligible"], adj.get("exclusion_code") if adj.get("eligible") else CH["A"][r]["exclusion_code"]
ft_ex = collections.Counter(final_elig(r)[1] for r in assessed if final_elig(r)[0] == "EXCLUDE")
inc = [r for r in assessed if final_elig(r)[0] == "INCLUDE"]
assert len(inc) == len(FINAL), (len(inc), len(FINAL))
full = sum(1 for r in assessed if CH["A"][r]["text_basis"] == "full_text")
abs_ex = collections.Counter((A[r].get("code") or "E2") for r in abs_excl)
NAMES = {"E1": "Not agrivoltaic, E1", "E2": "No enabler, E2", "E3": "Potential or siting, E3", "E4": "Review, E4", "E5": "Not full primary paper, E5", "E6": "Not English or not usable, E6"}
def lines(c):
    return "\n".join(f"{NAMES.get(k, k)} (n = {v:,})" for k, v in sorted(c.items(), key=lambda kv: -kv[1]))
src_tot = collections.Counter()
for x in RAW: src_tot[x[0]] += x[4]
FL = {
 "n_raw": n_raw, "n_unique": n_unique, "n_dup": n_raw - n_unique, "n_auto": n_auto, "n_title_screened": len(title_screened), "n_title_excluded": len(title_excl),
 "n_abs_screened": len(abs_screened), "n_abs_excluded": len(abs_excl), "n_sought": len(sought), "n_not_retrieved": len(not_retrieved),
 "n_assessed": len(assessed), "n_assessed_full": full, "n_assessed_abs": len(assessed) - full, "n_ft_excluded": sum(ft_ex.values()),
 "k_title": f"{tk[1]:.2f}", "agree_title_pct": f"{100 * tk[0]:.0f}", "k_abs": f"{ak[1]:.2f}", "agree_abs_pct": f"{100 * ak[0]:.0f}",
 "auto_reasons": dict(auto.most_common()), "source_rows": RAW,
 "n_cit_identified": len(cit), "n_cit_auto": len(cit_auto), "n_cit_sought": len(cit_sought), "n_sought_db": len(sought_db),
 "n_rescreen": len(rescreened), "n_rescreen_fw": len(rescued), "n_rescreen_noabs": len(title_excl) - len(rescreened),
}
fig = {"identified_text": f"Records identified from databases (n = {n_raw:,})\n" + "\n".join(f"{s} (n = {n:,})" for s, n in src_tot.items()) + f"\nCitation searching (n = {len(cit)})",
       "removed_before_text": f"Records removed before screening\nDuplicates (n = {n_raw - n_unique:,})\nAutomatically excluded by document\ntype or language (n = {n_auto + len(cit_auto):,})",
       "title_screened": len(title_screened), "title_excluded": len(title_excl), "rescreened": len(rescreened), "rescued": len(rescued), "abstract_screened": len(abs_screened),
       "abstract_excluded_text": f"Records excluded (n = {len(abs_excl):,})\n" + lines(abs_ex), "sought": len(sought), "sought_note": f"including {len(cit_sought)} from citation searching", "not_retrieved": len(not_retrieved),
       "assessed": len(assessed), "assessed_full": full, "assessed_abs": len(assessed) - full,
       "ft_excluded_text": f"Reports excluded (n = {sum(ft_ex.values()):,})\n" + lines(ft_ex), "included": len(inc)}
NL = chr(10)
cit_set = set(cit_sought)
cit_nr = [r for r in not_retrieved if r in cit_set]; cit_ass = [r for r in assessed if r in cit_set]
cit_inc = [r for r in inc if r in cit_set]
db_nr = [r for r in not_retrieved if r not in cit_set]; db_ass = [r for r in assessed if r not in cit_set]
db_ex = collections.Counter(final_elig(r)[1] for r in db_ass if final_elig(r)[0] == "EXCLUDE")
cit_ex = collections.Counter(final_elig(r)[1] for r in cit_ass if final_elig(r)[0] == "EXCLUDE")
FL.update({"n_db_sought": len(sought_db), "n_db_not_retrieved": len(db_nr), "n_db_assessed": len(db_ass), "n_db_excluded": sum(db_ex.values()),
           "n_db_included": len(inc) - len(cit_inc), "n_cit_not_retrieved": len(cit_nr), "n_cit_assessed": len(cit_ass), "n_cit_excluded": sum(cit_ex.values()), "n_cit_included": len(cit_inc)})
fig.update({"db_sought": len(sought_db), "db_not_retrieved": len(db_nr), "db_assessed": len(db_ass),
            "db_assessed_full": sum(1 for r in db_ass if CH["A"][r]["text_basis"] == "full_text"),
            "db_excluded_text": f"Reports excluded (n = {sum(db_ex.values()):,})" + NL + lines(db_ex),
            "cit_identified": len(cit), "cit_auto": len(cit_auto), "cit_sought": len(cit_sought), "cit_not_retrieved": len(cit_nr), "cit_assessed": len(cit_ass),
            "cit_excluded_text": f"Reports excluded (n = {sum(cit_ex.values())})" + NL + lines(cit_ex), "cit_included": len(cit_inc),
            "db_identified_text": f"Records identified from databases (n = {n_raw:,})" + NL + NL.join(f"{s} (n = {n:,})" for s, n in src_tot.items()),
            "db_removed_text": f"Records removed before screening{NL}Duplicates (n = {n_raw - n_unique:,}){NL}Excluded automatically by document{NL}type or language (n = {n_auto:,})"})
FL["fig"] = fig
json.dump(FL, open(sys.argv[3], "w", encoding="utf-8"), indent=1)
dec = {}
for rid, r in R.items():
    d = {}
    if r.get("auto_exclusion"): d["final"] = "Excluded automatically: " + r["auto_exclusion"]
    if rid in TA: d["title_A"] = TA[rid][0] + (" " + TA[rid][1] if TA[rid][1] else ""); d["title_B"] = TB[rid][0] + (" " + TB[rid][1] if TB[rid][1] else ""); d["title_final"] = T[rid]["title_decision"]
    if rid in AA: d["abs_A"] = AA[rid]; d["abs_B"] = AB[rid]; d["abs_final"] = A[rid]["abs_decision"]
    if rid in RS: d["title_rescreen"] = RS[rid]["decision"]
    if rid in title_excl and rid not in rescued: d["final"] = "Excluded at title screening" + (" (confirmed at abstract re-screening)" if rid in RS else "")
    elif rid in abs_excl: d["final"] = "Excluded at title and abstract screening"
    elif rid in not_retrieved: d["final"] = "Not retrieved"
    elif rid in assessed:
        e = final_elig(rid); d["final"] = "Included" if e[0] == "INCLUDE" else f"Excluded at eligibility assessment ({e[1]})"
    dec[rid] = d
json.dump({"decisions": dec, "not_retrieved": not_retrieved}, open(sys.argv[4], "w", encoding="utf-8"))
print({k: v for k, v in FL.items() if k not in ("fig", "source_rows", "auto_reasons")})
