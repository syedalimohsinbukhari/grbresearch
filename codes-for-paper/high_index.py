"""Created on Dec 17 13:22:15 2025"""

import json
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np

from src.grb_research.core import plot_per_episode
from src.grb_research.grb_constants import short_to_long
from src.grb_research.grb_core import GRBCatalog
from src.grb_research.grb_model import ModelSet

fs = 12

with open("./../results.json", "r") as f:
    example_data = json.load(f)

grb_list = ["080916C", "110721A", "110731A", "150210A"]
grb_list_long = [short_to_long[i] for i in grb_list]

gc = GRBCatalog.from_iterable(grb_list=grb_list, data=example_data, name_mapping=short_to_long)

grb080916c = gc.get_grb(grb_list_long[0])
grb110721a = gc.get_grb(grb_list_long[1])
grb110731a = gc.get_grb(grb_list_long[2])
grb150210a = gc.get_grb(grb_list_long[3])

grb080916c_best = grb080916c.get_all_best_models()
grb110721a_best = grb110721a.get_all_best_models()
grb110731a_best = grb110731a.get_all_best_models()
grb150210a_best = grb150210a.get_all_best_models()

start_080916, end_080916, diff_080916, midpoint_080916 = grb080916c.intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)
start_110721, end_110721, diff_110721, midpoint_110721 = grb110721a.intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)
start_110731, end_110731, diff_110731, midpoint_110731 = grb110731a.intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)
start_150210, end_150210, diff_150210, midpoint_150210 = grb150210a.intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)


def extract_peak_energy(best_model: ModelSet) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract peak energy proxy values and errors based on model type.

    Rules:
    - BAND / SBPL and their derivatives:
        extract parameter where 'index2' is in the name
    - CPL_PL / CPL_PL_BB:
        extract parameter where 'add_index_pl' is in the name
    - CPL only:
        append np.nan (no peak energy proxy)
    """

    values = []
    errors = []

    sbpl_band_models = {"band", "band_pl", "band_bb", "band_pl_bb", "sbpl", "sbpl_pl", "sbpl_bb", "sbpl_pl_bb"}

    cpl_pl_models = {"cpl_pl", "cpl_pl_bb"}

    for model in best_model:
        model_name = model.name.lower()

        # --- BAND / SBPL family ---
        if model_name in sbpl_band_models:
            param = next((p for p in model.parameters if "index2" in p.name), None)

            if param is not None:
                values.append(param.value)
                errors.append(param.error)

        # --- CPL + PL family ---
        elif model_name in cpl_pl_models:
            param = next((p for p in model.parameters if "add_index_pl" in p.name), None)

            if param is not None:
                values.append(param.value)
                errors.append(param.error)

        # --- Pure CPL ---
        elif model_name == "cpl":
            values.append(np.nan)
            errors.append(np.nan)

    return np.asarray(values), np.asarray(errors)


ep_value_080916c, ep_error_080916c = extract_peak_energy(grb080916c_best)
ep_value_110721a, ep_error_110721a = extract_peak_energy(grb110721a_best)
ep_value_110731a, ep_error_110731a = extract_peak_energy(grb110731a_best)
ep_value_150210a, ep_error_150210a = extract_peak_energy(grb150210a_best)

_, ax = plt.subplots(2, 1, figsize=(5.5, 6))
plot_per_episode(
    values=ep_value_080916c,
    errors=ep_error_080916c,
    m_name=grb_list[0],
    start=start_080916,
    end=end_080916,
    difference=diff_080916,
    midpoints=midpoint_080916,
    axes=ax[0],
)
plot_per_episode(
    values=ep_value_110721a,
    errors=ep_error_110721a,
    m_name=grb_list[1],
    start=start_110721,
    end=end_110721,
    difference=diff_110721,
    midpoints=midpoint_110721,
    axes=ax[1],
)

[i.grid(True, which="both", alpha=0.5, ls="--") for i in ax]
ax[-1].set_xlabel("Time [s]", fontsize=fs)
[i.set_ylabel(r"Higher Index [$\beta$]", fontsize=fs) for i in ax]
plt.xticks(fontsize=fs)
plt.yticks(fontsize=fs)
[i.legend(loc="upper right", frameon=False, fontsize=fs) for i in ax]
# plt.title("Peak Energy of GRB 150210A")
plt.tight_layout()
# plt.show()
[plt.savefig(f"./high_index__best__080916c_110721a.{i}", dpi=600) for i in ["png", "pdf"]]
plt.close()

_, ax = plt.subplots(2, 1, figsize=(5.5, 6))
plot_per_episode(
    values=ep_value_110731a,
    errors=ep_error_110731a,
    m_name=grb_list[2],
    start=start_110731,
    end=end_110731,
    difference=diff_110731,
    midpoints=midpoint_110731,
    axes=ax[0],
)
plot_per_episode(
    values=ep_value_150210a,
    errors=ep_error_150210a,
    m_name=grb_list[3],
    start=start_150210,
    end=end_150210,
    difference=diff_150210,
    midpoints=midpoint_150210,
    axes=ax[1],
)

[i.grid(True, which="both", alpha=0.5, ls="--") for i in ax]
ax[-1].set_xlabel("Time [s]", fontsize=fs)
[i.set_ylabel(r"Higher Index [$\beta$]", fontsize=fs) for i in ax]
plt.xticks(fontsize=fs)
plt.yticks(fontsize=fs)
[i.legend(loc="center right", frameon=False, fontsize=fs) for i in ax]
# plt.title("Peak Energy of GRB 150210A")
plt.tight_layout()
# plt.show()
[plt.savefig(f"./high_index__best__110731a_150210a.{i}", dpi=600) for i in ["png", "pdf"]]
plt.close()
