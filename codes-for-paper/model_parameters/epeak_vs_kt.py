"""Created on Apr 01 14:02:04 2026"""

import json

import matplotlib.pyplot as plt
import numpy as np

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
grb_name = ["080916C", "140206B", "131014A", "231129C"]

with open(result_file, "r") as f:
    data = json.load(f)

grb = GRBCatalog.from_iterable(grb_list=grb_name, data=data, name_mapping=short_to_long)
grb_full_name = [short_to_long[i] for i in grb_name]

# -- Fetch models (manual specification) --------------------------------------

models_080916C = [
    grb[grb_full_name[0]].get_model("SBPL_BB", interval=EpisodeTypes.T90),
    grb[grb_full_name[0]].get_model("BAND_BB", interval=EpisodeTypes.EX0),
    grb[grb_full_name[0]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=1),
    grb[grb_full_name[0]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=2),
    grb[grb_full_name[0]].get_model("SBPL_BB", interval=EpisodeTypes.TR, tr_index=3),
]
bb_status_080916C = ["full", "full", "full", "kT_only", "full"]

models_140206B = [
    grb[grb_full_name[1]].get_model("BAND_BB", EpisodeTypes.T90),
    grb[grb_full_name[1]].get_model("BAND_BB", interval=EpisodeTypes.EX0),
    grb[grb_full_name[1]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=1),
    grb[grb_full_name[1]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=2),
    grb[grb_full_name[1]].get_model("CPL_BB", interval=EpisodeTypes.TR, tr_index=4),
]

bb_status_140206B = ["full", "full", "full", "full", "full"]

models_131014A = [
    grb[grb_full_name[2]].get_model("BAND_BB", EpisodeTypes.T90),
    grb[grb_full_name[2]].get_model("BAND_BB", interval=EpisodeTypes.EX0),
    grb[grb_full_name[2]].get_model("BAND_BB", interval=EpisodeTypes.TR, tr_index=1),
    grb[grb_full_name[2]].get_model("SBPL_BB", interval=EpisodeTypes.TR, tr_index=2),
    grb[grb_full_name[2]].get_model("BAND_BB", interval=EpisodeTypes.EX1),
]
bb_status_131014A = ["full", "full", "full", "full", "full"]

models_231129C = [
    grb[grb_full_name[3]].get_model("SBPL_BB", EpisodeTypes.T90),
    grb[grb_full_name[3]].get_model("SBPL_BB", EpisodeTypes.EX0),
    grb[grb_full_name[3]].get_model("SBPL_BB", EpisodeTypes.TR, tr_index=1),
    grb[grb_full_name[3]].get_model("SBPL_BB", EpisodeTypes.TR, tr_index=2),
    grb[grb_full_name[3]],
]

# -- Extract kT / E_peak -----------------------------------------------------

kt_080916C, ep_080916C, mkr_080916C, clr_080916C, lbl_080916C = extract_kt_epeak_from_models(models_080916C)

kt_140206B, ep_140206B, mkr_140206B, clr_140206B, lbl_140206B = extract_kt_epeak_from_models(models_140206B)
kt_131014A, ep_131014A, mkr_131014A, clr_131014A, lbl_131014A = extract_kt_epeak_from_models(models_131014A)
# -- Plot ---------------------------------------------------------------------

f, ax = plt.subplots(4, 1, figsize=(6, 8))

ax = np.array(ax).flatten()

grb_panels = [
    (ax[0], kt_080916C, ep_080916C, mkr_080916C, clr_080916C, lbl_080916C, bb_status_080916C),
    (ax[1], kt_140206B, ep_140206B, mkr_140206B, clr_140206B, lbl_140206B, bb_status_140206B),
    (ax[2], kt_131014A, ep_131014A, mkr_131014A, clr_131014A, lbl_131014A, bb_status_131014A),
]

for a, kt, ep, mkrs, clrs, lbls, status_list in grb_panels:
    for kt_i, ep_i, mkr, clr, lbl, status in zip(kt, ep, mkrs, clrs, lbls, status_list):
        a.errorbar(
            kt_i[1],
            ep_i[1],
            xerr=[[kt_i[0]], [kt_i[2]]],
            yerr=[[ep_i[0]], [ep_i[2]]],
            fmt=mkr,
            mfc="w" if status == "kT_only" else None,
            ms=8,
            capsize=5,
            color=clr,
            linestyle="--" if status == "kT_only" else "-",
            label=lbl,
        )

# -- ODR fits -----------------------------------------------------------------

# GRB 080916C: fit "full" points only
full_mask_080916C = [s == "full" for s in bb_status_080916C]
fit_and_plot_odr(kt_080916C, ep_080916C, ax[0], mask=full_mask_080916C)

fit_and_plot_odr(kt_140206B, ep_140206B, ax[2])

fit_and_plot_odr(kt_131014A, ep_131014A, ax[2])

ax[-1].set_xlabel("kT [keV]", fontsize=LABEL_FONT_SIZE)
[a.set_ylabel(r"$E_\text{peak}$ [keV]", fontsize=LABEL_FONT_SIZE) for a in ax]
[
    a.legend(fontsize=LEGEND_FONT_SIZE, title=f"GRB{grb_name[i]}", title_fontsize=LEGEND_TITLE_FONT_SIZE)
    for i, a in enumerate(ax)
]
[a.grid(True, which="both", alpha=0.5, ls="--") for a in ax]
f.tight_layout()

plt.show()
# for ext in ["png", "pdf"]:
#     plt.savefig(f"epeak_vs_kt.{ext}", dpi=300)
# plt.close()
