"""Created on Jan 24 02:32:18 2026 — refactored Mar 27 2026"""

import os

import matplotlib.pyplot as plt

from amati_helpers import (
    amati_relationship_dirirsa2019,
    plot_grbs_over_amati_relationship,
    plot_unknown_redshift_grb,
)
from src.grb_research import find_project_root
from src.grb_research.grb_constants import TICK_FONT_SIZE, LEGEND_TITLE_FONT_SIZE, LEGEND_FONT_SIZE, LABEL_FONT_SIZE
from src.grb_research.grb_core import prepare_grbs

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

grb_list = ["080916C", "110721A", "110731A", "150210A"]
gc, grb_list_long, grb_objs, grb_best = prepare_grbs(grb_list, result_file, get_best=True)

# Known redshifts for the first three GRBs; GRB150210A has no known redshift.
redshifts = [4.35, 0.3826, 2.83]

# T90 marker per GRB — the only per-GRB marker dimension.
# GRB150210A's T90 marker is included so EpisodeMarkerResolver can be
# constructed consistently for the unknown-redshift panel.
t90_markers = ["o", "d", "X", "D"]

# ---------------------------------------------------------------------------
# Sampling config
# ---------------------------------------------------------------------------

n_sample = 10_000 if os.cpu_count() > 10 else 2_500
n_grid = 500
n_seed = 12345

# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

f, ax = plt.subplots(2, 2, figsize=(12, 10), sharex=True, sharey=True)
ax = ax.flatten()

amati_kw = dict(x_lim=(180, 3e4), y_lim=(1e51, 1.2e54), num_points=n_grid, use_average=True)
for a in ax:
    amati_relationship_dirirsa2019(**amati_kw, axis=a)

# ---------------------------------------------------------------------------
# Known-redshift GRBs — one per subplot
# ---------------------------------------------------------------------------

for i, a in enumerate(ax[:-1]):
    plot_grbs_over_amati_relationship(
        best_model_list=[grb_best[i]],
        redshift_list=[redshifts[i]],
        t90_marker_list=[t90_markers[i]],
        n_grid=n_grid,
        n_sample=n_sample,
        seed_number=n_seed,
        axis=a,
    )
    a.legend(loc="best", ncols=3, title=f"GRB{grb_list[i]}",
             fontsize=LEGEND_FONT_SIZE, title_fontsize=LEGEND_TITLE_FONT_SIZE)

# ---------------------------------------------------------------------------
# Unknown-redshift GRB (GRB150210A) — redshift locus across z = 1, 3, 5, 7
# ---------------------------------------------------------------------------

for m in grb_best[-1]:
    plot_unknown_redshift_grb(
        models=[m],
        t90_marker=t90_markers[-1],
        z_values=(1, 3, 5, 7),
        n_grid=n_grid,
        n_sample=n_sample,
        seed_number=n_seed,
        axis=ax[-1],
    )

ax[-1].legend(loc="best", ncols=3, title=f"GRB{grb_list[-1]}",
              fontsize=LEGEND_FONT_SIZE, title_fontsize=LEGEND_TITLE_FONT_SIZE)

# ---------------------------------------------------------------------------
# Shared axis labels and export
# ---------------------------------------------------------------------------

for a in ax[2:]:
    a.set_xlabel(r"$E_{i,\mathrm{peak}}$ [keV]", fontsize=LABEL_FONT_SIZE)
    a.tick_params(axis="both", labelsize=TICK_FONT_SIZE)
for a in ax[::2]:
    a.set_ylabel(r"$E_\mathrm{iso}$ [erg]", fontsize=LABEL_FONT_SIZE)
    a.tick_params(axis="both", labelsize=TICK_FONT_SIZE)

plt.tight_layout()
# plt.show()
for fmt in ("png", "pdf"):
    plt.savefig(f"./amati_relationship.{fmt}", dpi=600)
plt.close()
