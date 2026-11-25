import json, re, unicodedata, sys
oa = json.load(open("oa_raw.json", encoding="utf-8"))
s2 = json.load(open("s2_raw.json", encoding="utf-8"))
def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "").lower()
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"[^a-z0-9]+", "", t)
def abstract_from_inv(inv):
    if not inv: return ""
    pos = {}
    for w, ps in inv.items():
        for p in ps: pos[p] = w
    return " ".join(pos[i] for i in sorted(pos))
recs = {}   # key -> record
def key_for(doi, title):
    if doi: return "doi:" + doi.lower().replace("https://doi.org/", "")
    return "t:" + norm_title(title)
counts = {}
for qn, block in oa.items():
    counts[("OpenAlex", qn)] = len(block["records"])
    for r in block["records"]:
        doi = (r.get("doi") or "").replace("https://doi.org/", "").lower() or None
        k = key_for(doi, r.get("title"))
        pl = r.get("primary_location") or {}
        src = (pl.get("source") or {})
        e = recs.setdefault(k, {"key": k, "doi": doi, "sources": set(), "queries": set()})
        e["sources"].add("OpenAlex"); e["queries"].add(qn)
        e.setdefault("title", r.get("title"))
        e.setdefault("year", r.get("publication_year"))
        e.setdefault("pub_date", r.get("publication_date"))
        e["oa_type"] = r.get("type")
        e.setdefault("venue", src.get("display_name"))
        e["venue_type"] = src.get("type")
        e.setdefault("authors", [a.get("author", {}).get("display_name") for a in r.get("authorships", [])])
        ab = abstract_from_inv(r.get("abstract_inverted_index"))
        if ab and len(ab) > len(e.get("abstract") or ""): e["abstract"] = ab
        e["openalex_id"] = r.get("id")
        e["language"] = r.get("language")
        bo = r.get("best_oa_location") or {}
        if bo.get("pdf_url"): e["oa_pdf"] = bo.get("pdf_url")
        e["biblio"] = r.get("biblio")
for qn, block in s2.items():
    counts[("SemanticScholar", qn)] = len(block["records"])
    for r in block["records"]:
        doi = ((r.get("externalIds") or {}).get("DOI") or "").lower() or None
        k = key_for(doi, r.get("title"))
        if k not in recs and not doi:
            pass
        # try title match against existing when DOI missing
        if k not in recs:
            nt = norm_title(r.get("title"))
            for kk, ee in recs.items():
                if norm_title(ee.get("title")) == nt and nt:
                    k = kk; break
        e = recs.setdefault(k, {"key": k, "doi": doi, "sources": set(), "queries": set()})
        e["sources"].add("SemanticScholar"); e["queries"].add(qn)
        e.setdefault("title", r.get("title")); e.setdefault("year", r.get("year")); e.setdefault("pub_date", r.get("publicationDate"))
        e.setdefault("venue", r.get("venue")); e["s2_types"] = r.get("publicationTypes")
        e.setdefault("authors", [a.get("name") for a in r.get("authors", [])])
        ab = r.get("abstract") or ""
        if ab and len(ab) > len(e.get("abstract") or ""): e["abstract"] = ab
        e["s2_id"] = r.get("paperId")
        if (r.get("openAccessPdf") or {}).get("url") and not e.get("oa_pdf"): e["oa_pdf"] = r["openAccessPdf"]["url"]
# second-pass title dedupe (records with and without DOI, or DOI variants)
by_title = {}
for k, e in list(recs.items()):
    nt = norm_title(e.get("title"))
    if not nt: continue
    if nt in by_title and by_title[nt] != k:
        a = recs[by_title[nt]]
        GOOD = ("article", "conference-paper", "review")
        if e.get("oa_type") in GOOD and a.get("oa_type") not in GOOD:
            # keep the published version: swap roles
            recs[k] = e; del recs[by_title[nt]]
            e["sources"] = set(e["sources"]) | set(a["sources"]); e["queries"] = set(e["queries"]) | set(a["queries"])
            if len(a.get("abstract") or "") > len(e.get("abstract") or ""): e["abstract"] = a["abstract"]
            e.setdefault("dup_keys", []).append(a["key"]); by_title[nt] = k
            continue
        a["sources"] |= e["sources"]; a["queries"] |= e["queries"]
        if len(e.get("abstract") or "") > len(a.get("abstract") or ""): a["abstract"] = e["abstract"]
        a.setdefault("dup_keys", []).append(k)
        del recs[k]
    else:
        by_title[nt] = k
out = []
for i, (k, e) in enumerate(sorted(recs.items(), key=lambda kv: ((kv[1].get("year") or 0), kv[1].get("title") or ""))):
    e["sources"] = sorted(e["sources"]); e["queries"] = sorted(e["queries"])
    e["rid"] = f"R{i+1:04d}"
    out.append(e)
json.dump(out, open("records_merged.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("per source/query:", {f"{a}|{b}": n for (a, b), n in counts.items()})
print("total raw:", sum(counts.values()), "unique:", len(out))
print("with abstract:", sum(1 for e in out if len(e.get("abstract") or "") > 100))
from collections import Counter
print(Counter(tuple(e["sources"]) for e in out))
print(Counter(e.get("oa_type") for e in out))
print("no title:", sum(1 for e in out if not e.get("title")))
