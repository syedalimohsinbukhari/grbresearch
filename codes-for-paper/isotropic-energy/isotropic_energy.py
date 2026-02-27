"""Created on Jan 04 18:46:18 2026"""

import matplotlib.pyplot as plt

from src.grb_research import find_project_root
from src.grb_research.grb_calculations import (
    amati_relationship_dirirsia2019, plot_grbs_over_amati_relationship,
    plot_unknown_redshift_grb)
from src.grb_research.grb_core import prepare_grbs

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

grb_list = ["080916C", "110721A", "110731A", "150210A"]
gc, grb_list_long, grb_objs, grb_best = prepare_grbs(grb_list, result_file, get_best=True)

z = [4.35, 0.3826, 2.83]
marker = ["o", "v", "s"]

n_sample = 10_000
n_grid = 10_000
n_seed = 12345

plt.figure(figsize=(7, 6))
amati_relationship_dirirsia2019(x_lim=(100, 3e4), y_lim=(1e51, 2e54), num_points=n_grid)

plot_grbs_over_amati_relationship(
    grb_names=grb_list_long[:-1],
    best_model_list=grb_best[:-1],
    redshift_list=z,
    marker_list=marker,
    n_grid=n_grid,
    n_sample=n_sample,
    seed_number=n_seed,
)
[
    plot_unknown_redshift_grb(i, grb_list_long[-1], n_grid=n_grid, n_sample=n_sample, seed_number=n_seed)
    for i in grb_best[-1]
]
plt.grid(which="both", ls="--", lw=0.5, color="k", alpha=0.15)
plt.legend()
handles, labels = plt.gca().get_legend_handles_labels()
plt.gca().legend(handles[:4], labels[:4], ncols=2, loc="best", fontsize=12)
plt.tight_layout()
[plt.savefig(f"isotropic_energy.{i}", dpi=600) for i in ["png", "pdf"]]
plt.close()
# plt.show()
