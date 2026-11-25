"""Fill missing abstracts for a list of record IDs from Crossref (by DOI). Usage: enrich.py rids.json"""
import json, sys, time, re, urllib.request, urllib.parse, os
R = json.load(open("records_v2_auto.json", encoding="utf-8"))
cache_p = "crossref_abstracts.json"
cache = json.load(open(cache_p, encoding="utf-8")) if os.path.exists(cache_p) else {}
want = set(json.load(open(sys.argv[1])))
n_new = 0
for r in R:
    if r["rid"] not in want or len(r.get("abstract") or "") >= 100 or not r.get("doi"): continue
    d = r["doi"]
    if d not in cache:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(d)
        ab = ""
        for i in range(4):
            try:
                m = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "review-reference-check"}), timeout=40))["message"]
                ab = m.get("abstract") or ""
                break
            except urllib.error.HTTPError as e:
                if e.code == 404: break
                time.sleep(2)
            except Exception:
                time.sleep(2)
        ab = re.sub(r"<[^>]+>", " ", ab); ab = re.sub(r"\s+", " ", ab).strip()
        ab = re.sub(r"^(Abstract|ABSTRACT)\s*", "", ab)
        cache[d] = ab; time.sleep(0.25)
    if cache[d]:
        r["abstract"] = cache[d]; r["abstract_source"] = "Crossref"; n_new += 1
json.dump(cache, open(cache_p, "w", encoding="utf-8"), ensure_ascii=False)
json.dump(R, open("records_v2_auto.json", "w", encoding="utf-8"), ensure_ascii=False)
print("filled", n_new)
