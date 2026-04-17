"""Created on Apr 01 14:02:04 2026"""

import json

import matplotlib.pyplot as plt

from utils import (
    extract_kt_epeak_from_models,
    fit_and_plot_odr,
    find_project_root,
    GRBCatalog,
    short_to_long,
    EpisodeTypes,
    LEGEND_FONT_SIZE,
    LABEL_FONT_SIZE,
    LEGEND_TITLE_FONT_SIZE,
)

# -- Load data ----------------------------------------------------------------

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"
grb_name = ["080916C", "110721A"]

with open(result_file, "r") as f:
    data = json.load(f)

grb = GRBCatalog.from_iterable(grb_list=grb_name, data=data, name_mapping=short_to_long)
grb_full_name = [short_to_long[i] for i in grb_name]

# -- Fetch models (manual specification) --------------------------------------

models_080916C = [
    grb[grb_full_name[0]].get_model("SBPL_BB", interval=EpisodeTypes.T90),
    grb[grb_full_name[0]].get_model("BAND_BB", interval=EpisodeTypes.EX0),
    grb[grb_full_name[0]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=0),
    grb[grb_full_name[0]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=1),
    grb[grb_full_name[0]].get_model("SBPL_BB", interval=EpisodeTypes.TR, tr_index=2),
]
bb_status_080916C = ["full", "full", "full", "kT_only", "full"]

models_110721A = [
    grb[grb_full_name[1]].get_model("BAND_BB", interval=EpisodeTypes.T90),
    grb[grb_full_name[1]].get_model("BAND_BB", interval=EpisodeTypes.EX0),
    grb[grb_full_name[1]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=0),
    grb[grb_full_name[1]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=1),
    grb[grb_full_name[1]].get_model("BAND_BB", interval=EpisodeTypes.SP, tr_index=0),
]
bb_status_110721A = ["full", "kT_only", "kT_only", "full", "full"]

# -- Extract kT / E_peak -----------------------------------------------------

kt_080916C, ep_080916C, mkr_080916C, clr_080916C, lbl_080916C = (
    extract_kt_epeak_from_models(models_080916C)
)
kt_110721A, ep_110721A, mkr_110721A, clr_110721A, lbl_110721A = (
    extract_kt_epeak_from_models(models_110721A)
)

# -- Plot ---------------------------------------------------------------------

f, ax = plt.subplots(2, 1, figsize=(6, 8), sharex=True)

grb_panels = [
    (ax[0], kt_080916C, ep_080916C, mkr_080916C, clr_080916C, lbl_080916C, bb_status_080916C),
    (ax[1], kt_110721A, ep_110721A, mkr_110721A, clr_110721A, lbl_110721A, bb_status_110721A),
]

for a, kt, ep, mkrs, clrs, lbls, status_list in grb_panels:
    for kt_i, ep_i, mkr, clr, lbl, status in zip(kt, ep, mkrs, clrs, lbls, status_list):
        a.errorbar(
            kt_i[1], ep_i[1],
            xerr=[[kt_i[0]], [kt_i[2]]],
            yerr=[[ep_i[0]], [ep_i[2]]],
            fmt=mkr,
            mfc="w" if status == "kT_only" else None,
            ms=8, capsize=5,
            color=clr,
            linestyle="--" if status == "kT_only" else "-",
            label=lbl,
        )

# -- ODR fits -----------------------------------------------------------------

# GRB 080916C: fit "full" points only
full_mask_080916C = [s == "full" for s in bb_status_080916C]
fit_and_plot_odr(kt_080916C, ep_080916C, ax[0], mask=full_mask_080916C)

# GRB 110721A: fit all points (dashed), then "full" points only (solid, different colour)
fit_and_plot_odr(kt_110721A, ep_110721A, ax[1])

full_mask_110721A = [s == "full" for s in bb_status_110721A]
fit_and_plot_odr(
    kt_110721A, ep_110721A, ax[1],
    mask=full_mask_110721A,
    color="#1B4F72", linestyle="-",
    annotation_xy=(0.05, 0.82),
    y_min_clip=500,
)

# -- Formatting ---------------------------------------------------------------

ax[1].set_xlabel("kT [keV]", fontsize=LABEL_FONT_SIZE)
[a.set_ylabel(r"$E_\text{peak}$ [keV]", fontsize=LABEL_FONT_SIZE) for a in ax]
[a.legend(fontsize=LEGEND_FONT_SIZE, title=f"GRB{grb_name[i]}",
          title_fontsize=LEGEND_TITLE_FONT_SIZE) for i, a in enumerate(ax)]
[a.grid(True, which="both", alpha=0.5, ls="--") for a in ax]
f.tight_layout()

for ext in ["png", "pdf"]:
    plt.savefig(f"epeak_vs_kt.{ext}", dpi=300)
plt.close()
