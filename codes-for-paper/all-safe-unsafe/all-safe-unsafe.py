"""Created on Feb 09 16:18:36 2026"""

import json
import matplotlib.pyplot as plt
from src.grb_research import find_project_root, GRBCatalog
from src.grb_research.grb_constants import MODEL_ORDER, short_to_long

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"
grb_name = ["080916C", "110721A", "110731A", "150210A"]

with open(result_file, "r") as f:
    data = json.load(f)

grb = GRBCatalog.from_iterable(grb_list=grb_name, data=data, name_mapping=short_to_long)

f, ax = plt.subplots(2, 2, figsize=(10, 8), sharex=True, sharey=True)
ax = ax.flatten()

colors = ['blue', 'green', 'red', 'orange']  # Different color for each GRB
MODEL_ORDER_R = [i.replace("_", "+") for i in MODEL_ORDER]

for index, value in enumerate(grb.grb_list):
    dict_ = value.get_model_count(separate=True)
    safe = dict_["SAFE"]
    unsafe = dict_["UNSAFE"]

    # Create data for bar chart
    safe_counts = [safe.get(model, 0) for model in MODEL_ORDER]
    unsafe_counts = [unsafe.get(model, 0) for model in MODEL_ORDER]

    # X positions for bars
    x_positions = list(range(len(MODEL_ORDER)))

    # Plot bars with different hatches and colors
    # Plot SAFE data first (solid fill)
    ax[index].bar(x_positions,
                  safe_counts,
                  label='SAFE',
                  color=colors[index],
                  alpha=0.7,
                  edgecolor='black',
                  linewidth=0.5)

    # Plot UNSAFE data on top (with hatch)
    ax[index].bar(x_positions,
                  unsafe_counts,
                  label='UNSAFE',
                  color=colors[index],
                  hatch='///',
                  alpha=0.5,
                  edgecolor='black',
                  linewidth=0.5,
                  bottom=safe_counts)

    # Set tick positions and labels
    ax[index].set_xticks(x_positions)
    ax[index].set_xticklabels(MODEL_ORDER_R)
    ax[index].legend(loc='best', title=f'GRB{grb_name[index]}', ncol=2, shadow=True)

[v.tick_params('x', rotation=90, labelsize=12) for v in ax]
[v.tick_params('y', labelsize=12) for v in ax]
ax[0].set_ylim(top=10.5)
plt.tight_layout()
# plt.show()
[plt.savefig(f"./all-safe-unsafe.{i}", dpi=600) for i in ["png", "pdf"]]
plt.close()

