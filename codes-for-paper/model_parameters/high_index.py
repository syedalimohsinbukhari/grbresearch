"""Created on Dec 17 13:22:15 2025"""

from typing import Tuple

import numpy as np
from matplotlib import pyplot as plt

from utils import (
    extract_parameter,
    find_project_root,
    prepare_grbs,
    LEGEND_FONT_SIZE,
    TICK_FONT_SIZE,
    LABEL_FONT_SIZE,
    ModelSet,
    plot_per_episode,
    save_value_error_as_parquet,
)


def extract_high_index(model_collection: ModelSet) -> Tuple[np.typing.ArrayLike, np.typing.ArrayLike]:
    """
    Extract high (beta) spectral index values and errors based on model type.

    Rules:
    - BAND / SBPL and their derivatives:
        extract parameter where 'index2' is in the name
    - CPL_PL / CPL_PL_BB:
        extract parameter where 'add_index_pl' is in the name
    - CPL only:
        append np.nan (no high-energy index)
    """

    values = []
    errors = []

    sbpl_band_models = {"band", "band_bb", "band_pl_bb", "sbpl", "sbpl_bb", "sbpl_pl_bb"}
    cpl_pl_models = {"cpl_pl_bb"}

    for model in model_collection:
        m_name = model.name.lower()

        # --- BAND / SBPL family ---
        if m_name in sbpl_band_models:
            result = extract_parameter(model, "index2")
            if result is not None:
                values.append(result[0])
                errors.append(result[1])

        # --- CPL + PL family ---
        elif m_name in cpl_pl_models:
            result = extract_parameter(model, "add_index_pl")
            if result is not None:
                values.append(result[0])
                errors.append(result[1])

        # --- Pure CPL ---
        elif m_name == "cpl":
            values.append(np.nan)
            errors.append(np.nan)

    return np.asarray(values), np.asarray(errors)


grb_list = ["080916C", "110721A", "140206B", "131014A"]

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

_, grb_list_long, grb_objs, grb_best = prepare_grbs(grb_list, result_file, get_best=True)

start_080916, end_080916, diff_080916, midpoint_080916 = grb_objs[0].intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)
start_110721, end_110721, diff_110721, midpoint_110721 = grb_objs[1].intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)
start_110731, end_110731, diff_110731, midpoint_110731 = grb_objs[2].intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)
start_150210, end_150210, diff_150210, midpoint_150210 = grb_objs[3].intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)

start_110731 = start_110731[:-1]
end_110731 = end_110731[:-1]
diff_110731 = diff_110731[:-1]
midpoint_110731 = midpoint_110731[:-1]

ep_value_080916c, ep_error_080916c = extract_high_index(grb_best[0])
ep_value_110721a, ep_error_110721a = extract_high_index(grb_best[1])
ep_value_110731a, ep_error_110731a = extract_high_index(grb_best[2])
ep_value_150210a, ep_error_150210a = extract_high_index(grb_best[3])

_, ax = plt.subplots(4, 1, figsize=(6, 12))  # , sharey=True)

plot_per_episode(
    values=ep_value_080916c,
    errors=ep_error_080916c,
    m_name=grb_list[0],
    start=start_080916,
    end=end_080916,
    difference=diff_080916,
    midpoints=midpoint_080916,
    axes=ax[0],
    special_counter=[i.interval.is_sp for i in grb_best[0]],
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
    special_counter=[i.interval.is_sp for i in grb_best[1]],
)

plot_per_episode(
    values=ep_value_110731a,
    errors=ep_error_110731a,
    m_name=grb_list[2],
    start=start_110731,
    end=end_110731,
    difference=diff_110731,
    midpoints=midpoint_110731,
    axes=ax[2],
    special_counter=[i.interval.is_sp for i in grb_best[2]],
)

plot_per_episode(
    values=ep_value_150210a,
    errors=ep_error_150210a,
    m_name=grb_list[3],
    start=start_150210,
    end=end_150210,
    difference=diff_150210,
    midpoints=midpoint_150210,
    axes=ax[3],
    special_counter=[i.interval.is_sp for i in grb_best[3]],
)

[i.grid(True, which="both", alpha=0.5, ls="--") for i in ax]
[i.set_xlabel("Time [s]", fontsize=LABEL_FONT_SIZE) for i in ax]
[i.set_ylabel(r"Higher Index [$\beta$]", fontsize=LABEL_FONT_SIZE) for i in ax]
plt.xticks(fontsize=TICK_FONT_SIZE)
plt.yticks(fontsize=TICK_FONT_SIZE)
[i.legend(loc="lower right", frameon=False, fontsize=LEGEND_FONT_SIZE) for i in ax]
plt.tight_layout()
# plt.show()
[
    plt.savefig(f"./high_index_best__all.{i}", dpi=600)
    for i in ["png", "pdf"]
]
plt.close()

######################################################################################################################
# SAVE THE VALUES
######################################################################################################################


list_of_values = [ep_value_080916c, ep_value_110721a, ep_value_110731a, ep_value_150210a]
list_of_errors = [ep_error_080916c, ep_error_110721a, ep_error_110731a, ep_error_150210a]
list_of_names = [[i.name for i in j if i.name != 'PL'] for j in grb_best]

save_value_error_as_parquet(
    grb_names=grb_list_long,
    list_of_values=list_of_values,
    list_of_errors=list_of_errors,
    list_of_names=list_of_names,
    filename="high_index.parquet",
)
