"""Created on Mar 04 10:48:03 2026"""

from src.grb_research import find_project_root
from src.grb_research.grb_core import prepare_grbs, GRB

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

grb_list = ["080916C", "110721A", "110731A", "150210A"]
gc, grb_list_long, grb_objs, grb_best = prepare_grbs(grb_list, result_file, get_best=True)

grb080916c: GRB = gc.get_grb(grb_list_long[3])
print(grb080916c.get_model("BAND_BB"))
