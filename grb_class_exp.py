"""Created on Dec 21 08:05:57 2025"""

import json

from src.grb_research.grb_constants import short_to_long
from src.grb_research.grb_core import GRBCatalog

# Example data with multiple interval types
with open("./results.json", "r") as f:
    example_data = json.load(f)

grb_list = ["080916C", "110721A", "110731A", "150210A"]
grb_list_long = [short_to_long[i] for i in grb_list]

gc = GRBCatalog.from_iterable(grb_list=grb_list, data=example_data, name_mapping=short_to_long)
grb080916c = gc.get_grb(grb_list_long[0])
