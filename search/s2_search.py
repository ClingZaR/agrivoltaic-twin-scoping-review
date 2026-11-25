import json, sys, time, urllib.request, urllib.parse, datetime
AV = ('agrivoltaic | agrivoltaics | "agri-voltaic" | "agri-voltaics" | "agri-photovoltaic" | "agri-photovoltaics" | '
      'agrophotovoltaic | agrophotovoltaics | "agro-photovoltaic" | "agro-photovoltaics" | agrovoltaic | agrovoltaics | '
      '"agro-voltaic" | "solar sharing" | "photovoltaic agriculture" | "solar agriculture" | "PV farming" | agrisolar | '
      '"solar grazing" | "photovoltaic greenhouse" | "photovoltaic greenhouses" | "PV greenhouse" | "PV greenhouses" | '
      '"dual-use solar" | "dual-use photovoltaic"')
E = ('"digital twin" | "digital twins" | "digital shadow" | "machine learning" | "deep learning" | "artificial intelligence" | '
     '"neural network" | "neural networks" | "reinforcement learning" | "random forest" | "support vector" | "gradient boosting" | '
     'XGBoost | LSTM | convolutional | "physics-informed" | "data-driven" | forecasting | forecast | "surrogate model" | metamodel | '
     '"genetic algorithm" | "particle swarm" | "Bayesian optimization" | "Internet of Things" | IoT | "sensor network" | '
     '"wireless sensor" | "edge computing" | "fog computing" | "cloud computing" | "decision support" | "remote sensing" | '
     'UAV | drone | satellite | "computer vision" | "ray tracing" | "ray-tracing" | "crop model" | "crop modeling" | '
     '"crop modelling" | "crop growth model" | "light model" | "radiation model" | "shading model" | "microclimate model" | '
     '"computational fluid dynamics" | CFD | "monitoring system" | "real-time monitoring" | "smart farming" | '
     '"precision agriculture" | "model predictive control" | "control strategy" | "optimization algorithm" | "optimisation algorithm"')
DT = '"digital twin" | "digital twins"'
PVAG = '(photovoltaic | "solar panel" | "solar panels" | "solar array" | PV) + (crop | crops | agriculture | agricultural | farm | farming | greenhouse)'
ARID = ('arid | "semi-arid" | desert | deserts | dryland | drylands | "hot climate" | MENA | "Middle East" | Gulf | UAE | "United Arab Emirates" | '
        'Saudi | Qatar | Oman | Kuwait | Bahrain | Egypt | Jordan | Morocco | Algeria | Tunisia | Libya | Israel | Iran | Iraq | Sahara | Sahel')
QUERIES = {
    "S1_av": f"{AV}",
    "Q1_main": f"({AV}) + ({E})",
    "Q2_dt_no_av_terms": f"({DT}) + {PVAG}",
    "Q3_arid": f"({AV}) + ({ARID})",
}
FIELDS = "title,abstract,year,publicationDate,venue,externalIds,publicationTypes,authors,isOpenAccess,openAccessPdf,journal"
def get(params):
    url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(params)
    for i in range(30):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "review-search-script"})
            return json.load(urllib.request.urlopen(req, timeout=90))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(3 + i); continue
            raise
    raise SystemExit("gave up")
out = {}
for name, q in [(k, QUERIES[k]) for k in (sys.argv[1:] or list(QUERIES))]:
    recs, token, total = [], None, None
    while True:
        p = {"query": q, "fields": FIELDS}
        if token: p["token"] = token
        d = get(p)
        total = d.get("total"); recs += d.get("data", [])
        token = d.get("token")
        print(name, "got", len(recs), "of", total, flush=True)
        if not token: break
        time.sleep(1.2)
    out[name] = {"query": q, "total_reported": total, "retrieved_utc": datetime.datetime.now(datetime.UTC).isoformat(), "records": recs}
json.dump(out, open("s2_raw_" + "_".join(sys.argv[1:] or ["all"]) + ".json", "w", encoding="utf-8"), ensure_ascii=False)
print({k: len(v["records"]) for k, v in out.items()})
