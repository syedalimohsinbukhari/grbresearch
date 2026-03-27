"""Created on Jan 24 02:32:18 2026"""

import os

import matplotlib.pyplot as plt
import numpy as np

from src.grb_research import find_project_root, ModelSet
from src.grb_research.grb_calculations import amati_relationship_dirirsia2019, plot_grbs_over_amati_relationship
from src.grb_research.grb_core import prepare_grbs

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

grb_list = ["080916C", "110721A", "110731A", "150210A"]
gc, grb_list_long, grb_objs, grb_best = prepare_grbs(grb_list, result_file, get_best=True)

z = [4.35, 0.3826, 2.83]
marker = ["o", "d", "X"]

n_sample = 10_000 if os.cpu_count() > 10 else 2_500
n_grid = 500
n_seed = 12345

f, ax = plt.subplots(2, 2, figsize=(12, 10), sharex=True, sharey=True)
ax = ax.flatten()

[
    amati_relationship_dirirsia2019(x_lim=(180, 3e4), y_lim=(1e51, 1.2e54), num_points=n_grid, use_average=True, axis=i)
    for i in ax
]

[
    plot_grbs_over_amati_relationship(
        best_model_list=[grb_best[i]],
        redshift_list=[z[i]],
        marker_list=[marker[i]],
        n_grid=n_grid,
        n_sample=n_sample,
        seed_number=n_seed,
        axis=v,
    )
    for i, v in enumerate(ax[:-1])
]

# hack for GRB150210A (grb with no known redshift)
# I'm basically forcing the markers to be there using teh unknown_redshift keyword
z = [1, 3, 5, 7]

T90_MARKER = ["D"]
TR_MARKERS = range(4, 12)
EX_MARKERS = ["*", "p"]

markers = T90_MARKER + [EX_MARKERS[0]] + list(TR_MARKERS)

epeak, eiso = [], []
color = []

for idx in range(len(grb_best[-1])):
    best = ModelSet([grb_best[-1][idx]])
    for z_ in z:
        p = plot_grbs_over_amati_relationship(
            [best],
            [z_],
            [markers[idx]],
            n_grid=n_grid,
            n_sample=n_sample,
            seed_number=n_seed,
            axis=ax[-1],
            unknown_redshift=True,
        )
        epeak.append(p[0])
        eiso.append(p[1])
        color.append(p[2])

epeak, eiso, color = np.array(epeak), np.array(eiso), np.array(color, dtype=str)
epeak = epeak.reshape(len(grb_best[-1]), -1)
eiso = eiso.reshape(len(grb_best[-1]), -1)
color = color.reshape(len(grb_best[-1]), -1)[:, 0]

for idx, (ep, ei) in enumerate(zip(epeak, eiso)):
    plt.plot(ep, ei, ls="--", color=color[idx], alpha=0.5)

handles, labels = ax[-1].get_legend_handles_labels()
ax[-1].legend(handles[::4], labels[::4], loc="best", ncols=3, title=f"GRB{grb_list[-1]}")

[v.legend(loc="best", ncols=3, title=f"GRB{grb_list[i]}") for i, v in enumerate(ax[:-1])]

plt.tight_layout()
plt.show()
