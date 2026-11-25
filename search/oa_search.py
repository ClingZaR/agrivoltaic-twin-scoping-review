import json, sys, time, urllib.request, urllib.parse, datetime
def orj(terms): return "(" + " OR ".join(terms) + ")"
AV = orj(['agrivoltaic', 'agrivoltaics', '"agri-voltaic"', '"agri-voltaics"', '"agri-photovoltaic"', '"agri-photovoltaics"',
          'agrophotovoltaic', 'agrophotovoltaics', '"agro-photovoltaic"', '"agro-photovoltaics"', 'agrovoltaic', 'agrovoltaics',
          '"agro-voltaic"', '"solar sharing"', '"photovoltaic agriculture"', '"solar agriculture"', '"PV farming"', 'agrisolar',
          '"solar grazing"', '"photovoltaic greenhouse"', '"photovoltaic greenhouses"', '"PV greenhouse"', '"PV greenhouses"',
          '"dual-use solar"', '"dual-use photovoltaic"'])
E = orj(['"digital twin"', '"digital twins"', '"digital shadow"', '"machine learning"', '"deep learning"', '"artificial intelligence"',
         '"neural network"', '"neural networks"', '"reinforcement learning"', '"random forest"', '"support vector"', '"gradient boosting"',
         'XGBoost', 'LSTM', 'convolutional', '"physics-informed"', '"data-driven"', 'forecasting', 'forecast', '"surrogate model"', 'metamodel',
         '"genetic algorithm"', '"particle swarm"', '"Bayesian optimization"', '"Internet of Things"', 'IoT', '"sensor network"',
         '"wireless sensor"', '"edge computing"', '"fog computing"', '"cloud computing"', '"decision support"', '"remote sensing"',
         'UAV', 'drone', 'satellite', '"computer vision"', '"ray tracing"', '"ray-tracing"', '"crop model"', '"crop modeling"',
         '"crop modelling"', '"crop growth model"', '"light model"', '"radiation model"', '"shading model"', '"microclimate model"',
         '"computational fluid dynamics"', 'CFD', '"monitoring system"', '"real-time monitoring"', '"smart farming"',
         '"precision agriculture"', '"model predictive control"', '"control strategy"', '"optimization algorithm"', '"optimisation algorithm"'])
DT = orj(['"digital twin"', '"digital twins"'])
PVAG = orj(['photovoltaic', '"solar panel"', '"solar panels"', '"solar array"', 'PV']) + " AND " + orj(['crop', 'crops', 'agriculture', 'agricultural', 'farm', 'farming', 'greenhouse'])
ARID = orj(['arid', '"semi-arid"', 'desert', 'deserts', 'dryland', 'drylands', '"hot climate"', 'MENA', '"Middle East"', 'Gulf', 'UAE',
            '"United Arab Emirates"', 'Saudi', 'Qatar', 'Oman', 'Kuwait', 'Bahrain', 'Egypt', 'Jordan', 'Morocco', 'Algeria', 'Tunisia',
            'Libya', 'Israel', 'Iran', 'Iraq', 'Sahara', 'Sahel'])
QUERIES = {"Q1_main": f"{AV} AND {E}", "Q2_dt_no_av_terms": f"{DT} AND {PVAG}", "Q3_arid": f"{AV} AND {ARID}", "S1_av": AV}
SELECT = "id,doi,title,publication_year,publication_date,type,primary_location,authorships,abstract_inverted_index,open_access,best_oa_location,language,biblio,cited_by_count"
def get(params):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    for i in range(60):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "review-search-script"}), timeout=120))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            wait = 10
            try: wait = int(json.loads(body).get("retryAfter", 10)) + 2
            except Exception: pass
            print("  http", e.code, "wait", wait, body[:160], flush=True)
            if e.code == 400: raise SystemExit("bad request: " + body[:300])
            time.sleep(wait)
        except Exception as ex:
            print("  err", ex, flush=True); time.sleep(10)
    raise SystemExit("gave up")
if __name__ == "__main__":
    which = sys.argv[1:] or list(QUERIES)
    OUTFILE = "oa_raw_" + "_".join(which) + ".json"
    out = {}
    for name in which:
        q = QUERIES[name]
        def fetch_range(a, b):
            d = get({"filter": f"title_and_abstract.search:{q},from_publication_date:{a},to_publication_date:{b}", "per-page": 200, "select": SELECT})
            n = d["meta"]["count"]
            if n <= 200:
                print(name, a, b, n, flush=True); time.sleep(1.5)
                return d["results"]
            import datetime as dt
            da, db = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
            mid = da + (db - da) // 2
            return fetch_range(a, mid.isoformat()) + fetch_range((mid + dt.timedelta(days=1)).isoformat(), b)
        tot = get({"filter": f"title_and_abstract.search:{q}", "per-page": 1, "select": "id"})["meta"]["count"]
        recs = fetch_range("1900-01-01", "2014-12-31")
        for y in range(2015, 2028):
            recs += fetch_range(f"{y}-01-01", f"{y}-12-31")
        ids = {r["id"] for r in recs}
        print(name, "retrieved", len(recs), "unique", len(ids), "reported total", tot, flush=True)
        d = {"meta": {"count": tot}}
        out[name] = {"query": q, "count_reported": d["meta"]["count"], "retrieved_utc": datetime.datetime.now(datetime.UTC).isoformat(), "records": recs}
        json.dump(out, open(OUTFILE, "w", encoding="utf-8"), ensure_ascii=False)
    print({k: len(v["records"]) for k, v in out.items()})
