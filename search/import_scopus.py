"""Merge Scopus CSV export(s) into records_v2_auto.json. Usage: import_scopus.py <csv> [<csv> ...]"""
import csv, json, sys, re, unicodedata, collections
csv.field_size_limit(10**8)
R = json.load(open("records_v2_auto.json", encoding="utf-8"))
def nt(t):
    t = unicodedata.normalize("NFKD", t or "").lower(); t = re.sub(r"<[^>]+>", " ", t); return re.sub(r"[^a-z0-9]+", "", t)
by_doi = {r["doi"]: r for r in R if r.get("doi")}
by_t = {nt(r.get("title")): r for r in R if r.get("title")}
rows = []
for p in sys.argv[1:]:
    with open(p, encoding="utf-8-sig", newline="") as f:
        rows += list(csv.DictReader(f))
def col(row, *names):
    for n in names:
        for k in row:
            if k.strip().lower() == n.lower(): return (row[k] or "").strip()
    return ""
SC_EXCL = {"review": "E4 review", "conference review": "E5 conference review", "book chapter": "E5 book chapter", "book": "E5 book",
           "editorial": "E4 editorial", "note": "E4 note", "letter": "E4 letter", "erratum": "E5 erratum", "short survey": "E4 short survey",
           "data paper": "E5 data paper", "retracted": "E5 retracted", "undefined": None}
stats = collections.Counter(); next_id = max(int(r["rid"][1:]) for r in R) + 1; seen_eid = set()
for row in rows:
    eid = col(row, "EID")
    if eid in seen_eid: stats["dup within export"] += 1; continue
    seen_eid.add(eid)
    doi = col(row, "DOI").lower() or None; title = col(row, "Title"); ab = col(row, "Abstract")
    if ab.startswith("[No abstract available]"): ab = ""
    ab = re.sub(r"\s*©.*$", "", ab).strip()
    dtype = col(row, "Document Type"); lang = col(row, "Language of Original Document")
    r = (by_doi.get(doi) if doi else None) or by_t.get(nt(title))
    if r:
        stats["matched"] += 1
        r.setdefault("sources", []); 
        if "Scopus" not in r["sources"]: r["sources"].append("Scopus")
        r.setdefault("queries", []).append("Scopus_S1_av")
        r["scopus_type"] = dtype; r["scopus_eid"] = eid
        if ab and len(ab) > len(r.get("abstract") or "") and len(r.get("abstract") or "") < 100:
            r["abstract"] = ab; r["abstract_source"] = "Scopus"; stats["abstract added"] += 1
        elif ab and not r.get("abstract_scopus"):
            r["abstract_scopus"] = ab
    else:
        stats["new"] += 1
        rid = f"R{next_id:04d}"; next_id += 1
        reason = SC_EXCL.get(dtype.lower())
        if not reason and lang and "english" not in lang.lower(): reason = "E6 not English"
        rec = {"rid": rid, "key": "doi:" + doi if doi else "t:" + nt(title), "doi": doi, "title": title, "year": int(col(row, "Year") or 0) or None,
               "venue": col(row, "Source title"), "authors": [a.strip() for a in col(row, "Authors").split(";") if a.strip()],
               "abstract": ab, "abstract_source": "Scopus" if ab else None, "sources": ["Scopus"], "queries": ["Scopus_S1_av"],
               "scopus_type": dtype, "scopus_eid": eid, "oa_type": None, "auto_exclusion": reason, "round": 2}
        R.append(rec)
        if doi: by_doi[doi] = rec
        by_t[nt(title)] = rec
json.dump(R, open("records_v2_auto.json", "w", encoding="utf-8"), ensure_ascii=False)
print(dict(stats), "rows", len(rows))
