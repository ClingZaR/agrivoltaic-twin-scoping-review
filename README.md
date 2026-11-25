# Are Agrivoltaic Models Ready for Digital Twins? Data and code

Data, protocols, and analysis code for the scoping review *Are Agrivoltaic Models Ready for Digital Twins? A Scoping Review of Modeling, Data, AI, and Computing Studies, with Implications for Arid Regions* (Nabulsi, Abu Talib, Ghenai, Nasir, Bettayeb, and Dakalbab; manuscript submitted for publication).

The repository holds every screening and charting decision behind the review, the protocols used to make them, and the code that turns them into the statistics, tables, and figure reported in the manuscript and its supplementary material.

## Reproduce the analysis

Tested with Python 3.15.

```
pip install -r requirements.txt
python run_analysis.py
```

`run_analysis.py` runs every step from the coded decisions to the reported results and writes them to `analysis/`:

| Output | Contents |
|---|---|
| `analysis/facts_v5.json`, `analysis/supp_v5b_facts.json` | Every number quoted in the manuscript and supplementary material |
| `analysis/tables_v5.json`, `analysis/supp_v5b.json` | The manuscript tables and the supplementary tables |
| `analysis/figs_v5/fig1_prisma.png` | The PRISMA flow diagram |
| `analysis/final_v5.json`, `analysis/final_v5_excluded.json` | Final codes for the 594 included studies, and the reason for each full-text exclusion |
| `analysis/screening_v5.json` | Title and title-and-abstract decisions of both screening passes for all 3,273 records |

These outputs are also committed, so they can be inspected without running anything.

## Folders

| Folder | Contents |
|---|---|
| `search/` | Search strings, raw result counts, all 3,273 deduplicated records (bibliographic metadata and automatic exclusions), the outputs of both screening passes at each stage with their reasons, and the scripts used to run the searches |
| `analysis/` | Every charting run and its adjudications, the model-structure and validation coding, the level audit, the cross-model check, the recoding of readiness candidates from the PDFs, the comparison with published human coding, the first author's manual check, and the analysis code |
| `protocols/` | Eligibility criteria, charting codebook, title-screening instructions, and the charting output schema |
| `fulltext/` | The retrieval log for open-access full texts (sources and status only; no texts) |
| `supplementary/` | Supplementary Material S1 to S5 as submitted |

Main data files in `analysis/`:

| File | Contents |
|---|---|
| `charts_all.json` | All charting runs: `A` (primary charting), `B` (double-coded sample), `ABS` (abstract-based coding of studies later charted from full text), `ADJ` and `ADJ_ABS` (adjudications), `FTX_BLIND` (blind full-text eligibility), `AUDIT_META` (level audit summary) |
| `blind_abstract_runs.json` | Blind abstract-based coding of the first calibration set |
| `mech_codes.json`, `mechB_codes.json` | Model structure and validation coding, first and second runs |
| `audit3.json`, `risk_set.json` | Audit of the digital twin level for the risk set |
| `xmodel_check.json`, `pdf_recheck.json` | Cross-model check; recoding of readiness candidates from the PDFs |
| `ext_ref.json`, `xr_recheck.json` | Comparison with per-study codes tabulated in published reviews |
| `ra_check_results.json`, `hc_adjudications.json` | The first author's manual check against the original publications, and the resulting corrections |
| `adjudications_readiness.json` | Adjudicated readiness codes |

## How the decisions were made

The searches were run on 24 November 2026 in Scopus, OpenAlex, and Semantic Scholar. As described in Sections 3.5 and 3.6 of the manuscript, screening, charting, and the audits were carried out by runs of two large language models (Claude Opus 5.5 and Claude Sonnet 5.5, Anthropic). Each run followed the written protocols in `protocols/` and Supplementary Material S4 and gave a reason or quoted evidence for every decision. The files here are the parsed outputs of those runs, one record per decision. The first author reviewed the decisions and checked a sample by hand against the original publications; that check and its corrections are in `ra_check_results.json` and `hc_adjudications.json`. Supplementary Material S4, Section S, lists who or what performed each step.

## What is not included, and why

- **Abstracts and full texts.** These are under publisher copyright. Every record keeps its DOI, so the texts can be retrieved from the publishers. Instead, the records carry `has_abstract` and `ta_flags`, the results of the two title-and-abstract text searches the analysis uses, so the reported numbers reproduce exactly.
- **Full Scopus exports.** Scopus terms do not allow redistribution, so only bibliographic fields are kept.
- **Run logs and PDFs.** `ext_ref.py`, `pdf_recheck.py`, `apply_hc_check.py`, and the search scripts are included to document how their outputs were produced. Rerunning them needs the original run logs, PDFs, or index access, so their outputs are included instead.

## Licence

Data and documentation: [CC BY 4.0](LICENSE-DATA.md). Code: [MIT](LICENSE).

## Citation

See `CITATION.cff`. Please also cite the article once it is published.
