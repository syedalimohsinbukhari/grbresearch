"""Created on Dec 21 08:05:57 2025"""

import json

from src.grb_research import short_to_long
from src.grb_research.grb_class import GRBCatalog

# Example data with multiple interval types
with open("./results.json", "r") as f:
    example_data = json.load(f)

grb_list = ['080916C', '110721A', '110731A', '150210A']

gc = GRBCatalog.from_iterable(grb_list=grb_list, data=example_data)
# print(gc)
grb110721a = gc[short_to_long[grb_list[1]]]
print(grb110721a.intervals.get_model('band'))

# print(grb110721a.intervals.get_model('band'))