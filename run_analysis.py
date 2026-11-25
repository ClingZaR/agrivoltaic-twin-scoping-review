"""Reproduce the review's analysis from the coded data in this repository.

Runs every step from the parsed screening and charting outputs to the statistics, tables, figure, and facts
reported in the manuscript and supplementary material. Usage: python run_analysis.py
Outputs are written to analysis/ (facts_v5.json, supp_v5b_facts.json, tables_v5.json, figs_v5/, and others)."""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
AN, SE = os.path.join(ROOT, "analysis"), os.path.join(ROOT, "search")
L = "v5"
CHARTS = os.path.join(AN, "charts_all.json")
RECORDS = os.path.join(SE, "records_v2_auto.json")
RAW_COUNTS = os.path.join(SE, "raw_counts_all.json")
BLIND = os.path.join(AN, "blind_abstract_runs.json")


def run(args, cwd):
    r = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        print(r.stdout[-2000:]); print(r.stderr[-4000:])
        raise SystemExit("step failed: " + args[0])
    print("ok:", args[0])


fin = f"final_{L}.json"
figdir = os.path.join(AN, f"figs_{L}"); os.makedirs(figdir, exist_ok=True)
run(["assemble.py", CHARTS, RECORDS, fin], AN)
run(["reweight.py"], AN)
run(["analyze.py", fin, f"stats_{L}.json"], AN)
run(["agreement.py", CHARTS, os.path.join(AN, f"agree_{L}.json")], SE)
run(["flow.py", CHARTS, os.path.join(AN, fin), os.path.join(AN, f"flow_{L}.json"), os.path.join(AN, f"screening_{L}.json"), RAW_COUNTS], SE)
run(["analyze_extra.py", fin, f"stats_{L}.json", f"screening_{L}.json", RECORDS], AN)
run(["calibration.py", fin, BLIND, f"stats_{L}.json"], AN)
FL = json.load(open(os.path.join(AN, f"flow_{L}.json"), encoding="utf-8"))
json.dump(FL["fig"], open(os.path.join(AN, f"flowfig_{L}.json"), "w", encoding="utf-8"))
run(["prisma_fig.py", f"flowfig_{L}.json", os.path.join(figdir, "fig1_prisma.png")], AN)
json.dump({k: v for k, v in FL.items() if k not in ("fig", "source_rows", "auto_reasons")},
          open(os.path.join(AN, f"flowfacts_{L}.json"), "w", encoding="utf-8"))
themes = os.path.join(AN, f"themes_{L}.json")
run(["facts.py", fin, f"stats_{L}.json", f"flowfacts_{L}.json", f"agree_{L}.json", themes, f"facts_{L}.json"], AN)
run(["phrases.py", f"facts_{L}.json", f"stats_{L}.json", fin, themes], AN)
run(["facts2.py", f"facts_{L}.json", f"stats_{L}.json", fin, CHARTS, os.path.join(SE, "recall_check.json")], AN)
run(["make_tables.py", fin, f"stats_{L}.json", f"facts_{L}.json", themes, os.path.join(AN, "tables_static.json"), f"tables_{L}.json", figdir], AN)
run(["v5.py", fin, f"stats_{L}.json", f"facts_{L}.json", CHARTS, f"tables_{L}.json", f"flow_{L}.json", os.path.join(SE, "recall_check.json"), f"supp_{L}b.json"], AN)
print("done: see analysis/facts_v5.json and analysis/supp_v5b_facts.json")
