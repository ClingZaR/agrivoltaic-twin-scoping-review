"""Two-column PRISMA 2020 style flow diagram (databases and citation searching). Usage: prisma_fig.py counts.json out.png"""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
c = json.load(open(sys.argv[1], encoding="utf-8"))
plt.rcParams["font.family"] = "Arial"
fig, ax = plt.subplots(figsize=(7.6, 8.6), dpi=200); ax.set_xlim(-8, 100); ax.set_ylim(14, 122); ax.axis("off")
def box(x, y, w, h, text, fs=6.4, bold=False, fc="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", lw=0.8, ec="black", fc=fc))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)
def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="black", mutation_scale=7))
for (y0, y1, lab) in [(103, 121, "Identification"), (40, 101, "Screening"), (16, 31, "Included")]:
    ax.add_patch(FancyBboxPatch((-7, y0), 5.5, y1 - y0, boxstyle="square,pad=0", lw=0.6, ec="black", fc="#dfe8f3"))
    ax.text(-4.25, (y0 + y1) / 2, lab, rotation=90, ha="center", va="center", fontsize=7, fontweight="bold")
ax.text(19, 123.5, "Identification via databases", ha="center", fontsize=7, fontweight="bold")
ax.text(86, 123.5, "Identification via other methods", ha="center", fontsize=7, fontweight="bold")
L, W = 0, 38; MX, MW = 41, 30; RX, RW = 74, 25
# databases column
box(L, 105, W, 16, c["db_identified_text"])
box(MX, 105, MW, 16, c["db_removed_text"], fs=6.0)
arrow(L + W, 113, MX, 113)
box(L, 91, W, 8, f"Records screened by title\n(n = {c['title_screened']:,})")
box(MX, 91, MW, 8, f"Records excluded (n = {c['title_excluded']:,})\n{c.get('rescreened', 0):,} with abstracts re-screened;\n{c.get('rescued', 0)} forwarded to eligibility", fs=6.0)
arrow(L + W / 2, 105, L + W / 2, 99); arrow(L + W, 95, MX, 95)
box(L, 77, W, 8, f"Records screened by title and abstract\n(n = {c['abstract_screened']:,})")
box(MX, 73, MW, 15, c["abstract_excluded_text"], fs=5.8)
arrow(L + W / 2, 91, L + W / 2, 85); arrow(L + W, 81, MX, 81)
box(L, 63, W, 8, f"Reports sought for eligibility\nassessment (n = {c['db_sought']:,}), including\n{c.get('rescued', 0)} from the title-stage re-screen", fs=6.0)
box(MX, 63, MW, 8, f"Reports not retrieved: no abstract\nand no accessible full text (n = {c['db_not_retrieved']:,})", fs=5.8)
arrow(L + W / 2, 77, L + W / 2, 71); arrow(L + W, 67, MX, 67)
box(L, 47, W, 10, f"Reports assessed for eligibility\n(n = {c['db_assessed']:,}; full text {c['db_assessed_full']:,})")
box(MX, 41, MW, 18, c["db_excluded_text"], fs=5.8)
arrow(L + W / 2, 63, L + W / 2, 57); arrow(L + W, 52, MX, 52)
# citation column
box(RX, 105, RW, 16, f"Records identified from\ncitation searching of eight\nrelated reviews (n = {c['cit_identified']})\n\nExcluded automatically:\npreprints (n = {c['cit_auto']})", fs=6.0)
box(RX, 63, RW, 8, f"Reports sought for eligibility\nassessment (n = {c['cit_sought']})", fs=6.0)
arrow(RX + RW / 2, 105, RX + RW / 2, 71)
box(RX, 54, RW, 6, f"Not retrieved (n = {c['cit_not_retrieved']})", fs=6.0)
arrow(RX + RW / 2, 63, RX + RW / 2, 60)
box(RX, 41, RW, 10, f"Reports assessed (n = {c['cit_assessed']})\n" + c["cit_excluded_text"].replace("Reports excluded", "Excluded"), fs=5.6)
arrow(RX + RW / 2, 54, RX + RW / 2, 51)
# included
import os as _os
_fp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "final_v5.json")
_nft = sum(1 for s in json.load(open(_fp, encoding="utf-8")) if s["text_basis"] == "full_text") if _os.path.exists(_fp) else None
_sub = (f"\n{_nft} charted from full text (primary analysis set);\n{c['included'] - _nft} from title and abstract") if _nft else ""
box(L, 16.5, W, 12, f"Studies (reports) included in the review\n(n = {c['included']:,})" + _sub, fc="#f3f3f3", fs=6.4)
arrow(L + W / 2, 47, L + W / 2, 28)
ax.annotate("", xy=(L + W, 23), xytext=(RX + RW / 2, 41), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="black", mutation_scale=7, connectionstyle="angle,angleA=-90,angleB=0"))
ax.text(RX + RW / 2 + 1, 33, f"included (n = {c['cit_included']})", fontsize=5.8)
plt.savefig(sys.argv[2], bbox_inches="tight", facecolor="white"); print("saved")
