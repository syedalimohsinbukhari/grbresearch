"""Created on Dec 17 13:22:15 2025"""

import json

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

from src.grb_research import find_project_root
from src.grb_research.grb_atomic import ParameterSet
from src.grb_research.grb_constants import short_to_long, LABEL_FONT_SIZE, TICK_FONT_SIZE, LEGEND_FONT_SIZE
from src.grb_research.grb_core import GRBCatalog
from src.grb_research.grb_model import ModelSet
from src.grb_research.grb_utils import break_e_to_e_peak, plot_per_episode, save_value_error_as_parquet

rng = np.random.default_rng(42)


def extract_peak_energy(best_model: ModelSet) -> tuple[npt.ArrayLike, npt.ArrayLike, npt.ArrayLike]:
    value, error1, error2 = [], [], []
    for model in best_model:
        if "SBPL" in model.name:
            par_dist = ParameterSet(model.parameters).get_populated_values(
                cov_matrix=model.covariance_matrix_value, size=5_000, rng=rng
            )
            idx = (5, 8, 6) if model.name == "SBPL_PL" else (2, 5, 3)
            peak_energy = break_e_to_e_peak(
                index1_sbpl=par_dist[:, idx[0]], index2_sbpl=par_dist[:, idx[1]], break_energy_sbpl=par_dist[:, idx[2]]
            )
            pp2 = np.nanpercentile(peak_energy, [16, 50, 84], axis=0)
            value.append(pp2[1])
            error1.append(pp2[2] - pp2[1])
            error2.append(pp2[1] - pp2[0])
        else:
            for p in model.parameters:
                if "e_peak" in p.name:
                    value.append(p.value)
                    error1.append(p.error)
                    error2.append(p.error)

    return np.array(value), np.array(error1), np.array(error2)


SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

with open(result_file, "r") as f:
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

ep_value_080916c, ep_error1_080916c, ep_error2_080916c = extract_peak_energy(grb080916c_best)
ep_value_110721a, ep_error1_110721a, ep_error2_110721a = extract_peak_energy(grb110721a_best)
ep_value_110731a, ep_error1_110731a, ep_error2_110731a = extract_peak_energy(grb110731a_best)
ep_value_150210a, ep_error1_150210a, ep_error2_150210a = extract_peak_energy(grb150210a_best)

_, ax = plt.subplots(4, 1, figsize=(5.5, 12))

plot_per_episode(
    values=ep_value_080916c,
    errors=[ep_error1_080916c, ep_error2_080916c],
    m_name=grb_list[0],
    start=start_080916,
    end=end_080916,
    difference=diff_080916,
    midpoints=midpoint_080916,
    axes=ax[0],
    special_counter=[i.interval.is_sp for i in grb080916c_best],
)

plot_per_episode(
    values=ep_value_110721a,
    errors=[ep_error1_110721a, ep_error2_110721a],
    m_name=grb_list[1],
    start=start_110721,
    end=end_110721,
    difference=diff_110721,
    midpoints=midpoint_110721,
    axes=ax[1],
    special_counter=[i.interval.is_sp for i in grb110721a_best],
)

plot_per_episode(
    values=ep_value_110731a,
    errors=[ep_error2_110731a, ep_error1_110731a],
    m_name=grb_list[2],
    start=start_110731,
    end=end_110731,
    difference=diff_110731,
    midpoints=midpoint_110731,
    axes=ax[2],
    special_counter=[i.interval.is_sp for i in grb110731a_best],
)

plot_per_episode(
    values=ep_value_150210a,
    errors=[ep_error1_150210a, ep_error2_150210a],
    m_name=grb_list[3],
    start=start_150210,
    end=end_150210,
    difference=diff_150210,
    midpoints=midpoint_150210,
    axes=ax[3],
    special_counter=[i.interval.is_sp for i in grb150210a_best],
)

[i.grid(True, which="both", alpha=0.5, ls="--") for i in ax]
[i.set_xlabel("Time [s]", fontsize=LABEL_FONT_SIZE) for i in ax]
[i.set_ylabel("Energy [keV]", fontsize=LABEL_FONT_SIZE) for i in ax]
plt.xticks(fontsize=TICK_FONT_SIZE)
plt.yticks(fontsize=TICK_FONT_SIZE)
[i.legend(loc="upper center", frameon=False, fontsize=LEGEND_FONT_SIZE) for i in ax]
plt.tight_layout()
# plt.show()
[plt.savefig(f"./peak_energy_best__all.{i}", dpi=600) for i in ["png", "pdf"]]
plt.close()

######################################################################################################################
# SAVE THE VALUES
######################################################################################################################


list_of_values = [ep_value_080916c, ep_value_110721a, ep_value_110731a, ep_value_150210a]
list_of_errors1 = [ep_error1_080916c, ep_error1_110721a, ep_error1_110731a, ep_error1_150210a]
list_of_errors2 = [ep_error2_080916c, ep_error2_110721a, ep_error2_110731a, ep_error2_150210a]
list_of_names = [[i.name for i in j] for j in [grb080916c_best, grb110721a_best, grb110731a_best, grb150210a_best]]

save_value_error_as_parquet(
    grb_names=grb_list_long,
    list_of_values=list_of_values,
    list_of_errors=(list_of_errors1, list_of_errors2),
    list_of_names=list_of_names,
    filename="peak_energy.parquet",
    asym_errs=True,
)
