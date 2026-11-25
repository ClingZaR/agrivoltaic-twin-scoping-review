import json, sys, re
def load(journal):
    if journal.endswith(".json"):
        return json.load(open(journal, encoding="utf-8"))
    started, results = {}, {}
    for line in open(journal, encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") == "started": started[d["agentId"]] = d.get("label")
        if d.get("type") == "result":
            results[d.get("agentId")] = d
    out = {}
    for aid, d in results.items():
        lab = started.get(aid) or d.get("label")
        val = d.get("value", d.get("result"))
        if isinstance(val, str):
            try: val = json.loads(val)
            except Exception: pass
        out[lab] = val
    return out
if __name__ == "__main__":
    o = load(sys.argv[1]); k = list(o)[:2]
    print(len(o), k); print(str(o[k[0]])[:400])
