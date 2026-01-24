"""Created on Jan 10 00:09:45 2026"""

import json

from src.grb_research import find_project_root, GRB, ModelSet
from src.grb_research.grb_calculations import plot_best_models
from src.grb_research.grb_constants import short_to_long

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

grb_name = "110721A"

with open(result_file, "r") as f:
    grb110721a_data = json.load(f)[short_to_long[grb_name]]

grb110721a = GRB.from_dictionary(grb_name, grb110721a_data)
grb110721a_best: ModelSet = grb110721a.get_all_best_models()

is_ex = sum([i.interval.is_ex for i in grb110721a_best])
if is_ex == 2:
    grb110721a_best[-1], grb110721a_best[-2] = grb110721a_best[-2], grb110721a_best[-1]

plot_best_models(grb110721a_best, 2, 2, grb_name, (8, 6))
