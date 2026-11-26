"""Search-sensitivity check: variant strings (descriptive wording; PV-greenhouse synonyms) run in OpenAlex and Semantic Scholar,
deduplicated against the review's records. Writes sens_new.json (records not already in the review) and sens_log.json."""
import json, os, re, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "review-search-script"}
def get(url, tries=10):
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120))
        except Exception as e:
            err = e; time.sleep((20 if "429" in str(e) else 4) * (i + 1))
    raise err
V = {
 "V1_descriptive": '("under solar panels" OR "beneath solar panels" OR "below solar panels" OR "under photovoltaic panels" OR "beneath photovoltaic panels" OR "under PV panels" OR "beneath PV panels" OR "under photovoltaic modules" OR "under PV modules" OR "under solar arrays" OR "beneath solar arrays" OR "shade of solar panels" OR "shading of solar panels" OR "shading from solar panels" OR "photovoltaic shading" OR "PV shading") AND (crop OR crops OR farming OR agricultural OR agriculture OR grazing OR pasture OR vegetable OR vegetables)',
 "V2_greenhouse": '("greenhouse-integrated photovoltaic" OR "greenhouse integrated photovoltaic" OR "greenhouse-integrated photovoltaics" OR "photovoltaic-greenhouse" OR "PV-greenhouse" OR "solar PV greenhouse" OR "photovoltaic roof greenhouse" OR "greenhouse photovoltaic" OR "greenhouse photovoltaics" OR "semi-transparent photovoltaic greenhouse" OR "BIPV greenhouse" OR "photovoltaic panels on greenhouse" OR "solar panels on greenhouse") ',
 "V3_colocation": '("solar farm" OR "solar park" OR "photovoltaic plant" OR "photovoltaic power station" OR "PV plant" OR "PV power station") AND ("crop yield" OR "crop growth" OR "sheep grazing" OR "co-location" OR "colocation" OR "dual land use" OR "land sharing")',
}
SELECT = "id,doi,title,display_name,publication_year,type,language,primary_location,abstract_inverted_index"
def oa(q):
    out, cursor = [], "*"
    while cursor:
        params = {"filter": f"title_and_abstract.search:{q},to_publication_date:2026-11-24", "per-page": 200, "select": SELECT, "cursor": cursor}
        d = get("https://api.openalex.org/works?" + urllib.parse.urlencode(params))
        out += d["results"]; cursor = d["meta"].get("next_cursor") if d["results"] else None
        if len(out) > 4000: break
    return out
def s2(q):
    qq = q.replace(" OR ", " | ").replace(" AND ", " + ")
    out, token = [], None
    while True:
        p = {"query": qq, "fields": "title,abstract,year,externalIds,publicationTypes,venue", "year": "-2026"}
        if token: p["token"] = token
        d = get("https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(p)); time.sleep(3)
        out += d.get("data", []); token = d.get("token")
        if not token or len(out) > 4000: break
    return out
def norm(t): return re.sub(r"[^a-z0-9]", "", (t or "").lower())
def inv(ii):
    if not ii: return ""
    pos = sorted((p, w) for w, ps in ii.items() for p in ps); return " ".join(w for _, w in pos)
R = json.load(open(os.path.join(HERE, "records_v2_auto.json"), encoding="utf-8"))
have_doi = {(r.get("doi") or "").lower() for r in R if r.get("doi")}; have_t = {norm(r.get("title")) for r in R}
new, log = {}, {}
for k, q in V.items():
    a = oa(q); b = s2(q); log[k] = {"openalex": len(a), "semantic_scholar": len(b)}
    for w in a:
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower(); t = w.get("title") or w.get("display_name") or ""
        if (doi and doi in have_doi) or norm(t) in have_t: continue
        if (w.get("language") or "en") != "en" or w.get("type") not in ("article", "proceedings-article", "book-chapter", "preprint", "review", None): pass
        key = doi or norm(t)
        new.setdefault(key, {"doi": doi, "title": t, "year": w.get("publication_year"), "type": w.get("type"), "language": w.get("language"),
                             "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"), "abstract": inv(w.get("abstract_inverted_index")), "queries": []})["queries"].append(k + ":OA")
    for w in b:
        doi = ((w.get("externalIds") or {}).get("DOI") or "").lower(); t = w.get("title") or ""
        if (doi and doi in have_doi) or norm(t) in have_t: continue
        key = doi or norm(t)
        e = new.setdefault(key, {"doi": doi, "title": t, "year": w.get("year"), "type": ",".join(w.get("publicationTypes") or []), "language": "", "venue": w.get("venue"), "abstract": w.get("abstract") or "", "queries": []})
        e["queries"].append(k + ":S2")
        if not e.get("abstract") and w.get("abstract"): e["abstract"] = w["abstract"]
    log[k]["new_cumulative"] = len(new); print(k, log[k])
# same automatic exclusions as the review: document type, language, year, missing title
def auto(e):
    t = (e.get("type") or "").lower()
    if not e.get("title"): return "no title"
    if e.get("year") and e["year"] > 2026: return "year"
    if e.get("language") and e["language"] != "en": return "not English"
    if any(x in t for x in ("review", "editorial", "letter", "erratum", "paratext", "dataset", "book", "dissertation", "peer-review", "other")) and "article" not in t: return "document type"
    return ""
for e in new.values(): e["auto_exclusion"] = auto(e)
json.dump(list(new.values()), open(os.path.join(HERE, "sens_new.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
log["n_new"] = len(new); log["n_new_screenable"] = sum(1 for e in new.values() if not e["auto_exclusion"]); log["n_new_with_abstract"] = sum(1 for e in new.values() if not e["auto_exclusion"] and e.get("abstract"))
json.dump(log, open(os.path.join(HERE, "sens_log.json"), "w"), indent=1); print(log)
