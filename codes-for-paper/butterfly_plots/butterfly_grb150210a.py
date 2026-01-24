"""Created on Jan 10 00:09:45 2026"""

import json

from src.grb_research import find_project_root, GRB, ModelSet
from src.grb_research.grb_calculations import plot_best_models
from src.grb_research.grb_constants import short_to_long

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

grb_name = "150210A"

with open(result_file, "r") as f:
    grb150210a_data = json.load(f)[short_to_long[grb_name]]

grb150210a = GRB.from_dictionary(grb_name, grb150210a_data)
grb150210a_best: ModelSet = grb150210a.get_all_best_models()

is_ex = sum([i.interval.is_ex for i in grb150210a_best])
if is_ex == 2:
    grb150210a_best[-1], grb150210a_best[-2] = grb150210a_best[-2], grb150210a_best[-1]

plot_best_models(grb150210a_best, 2, 4, grb_name, (15, 6))
