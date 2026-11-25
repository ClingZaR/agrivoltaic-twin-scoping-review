import json, re, collections
R = json.load(open("records_v2.json", encoding="utf-8"))
AUTO_TYPE = {"preprint": "E5 preprint", "dissertation": "E5 thesis", "book-chapter": "E5 book chapter", "book": "E5 book",
             "conference-abstract": "E5 conference abstract", "dataset": "E5 dataset", "report": "E5 report", "editorial": "E4 editorial",
             "software": "E5 software", "erratum": "E5 erratum", "peer-review": "E5 peer-review report", "paratext": "E5 paratext",
             "data-paper": "E5 data paper", "reference-entry": "E5 reference entry", "review": "E4 review", "letter": "E4 letter",
             "retraction": "E5 retraction", "standard": "E5 standard", "grant": "E5 grant", "supplementary-materials": "E5 supplementary", "other": None}
log = collections.Counter(); kept = []
for r in R:
    reason = None
    if not r.get("title"): reason = "E6 no record"
    t = r.get("oa_type")
    if not reason and t in AUTO_TYPE and AUTO_TYPE[t]: reason = AUTO_TYPE[t]
    if not reason and t is None:
        st = r.get("s2_types") or []
        pass  # S2 "Review" labels are not used for automatic exclusion
    if not reason and r.get("language") and r["language"] != "en": reason = "E6 not English"
    if not reason and (r.get("year") or 0) > 2026: reason = "E5 out of range"
    r["auto_exclusion"] = reason
    log[reason or "to screen"] += 1
    if not reason: kept.append(r)
json.dump(R, open("records_v2_auto.json", "w", encoding="utf-8"), ensure_ascii=False)
print(log.most_common())
print("to screen:", len(kept), " with abstract:", sum(1 for r in kept if len(r.get("abstract") or "") > 100))
