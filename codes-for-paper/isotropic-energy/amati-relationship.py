"""Created on Jan 14 09:59:36 2026"""

import json

import matplotlib.pyplot as plt
import numpy as np

from src.grb_research import find_project_root, GRBCatalog, SpectralModels
from src.grb_research.grb_constants import short_to_long

PROJECT_ROOT = find_project_root()

with open(f"{PROJECT_ROOT}/results.json", "r") as f:
    example_data = json.load(f)

grb_list = ["080916C", "110721A", "110731A", "150210A"]
grb_list_long = [short_to_long[i] for i in grb_list]

gc = GRBCatalog.from_iterable(grb_list=grb_list, data=example_data, name_mapping=short_to_long)

grb080916c = gc.get_grb(grb_list_long[0])
grb080916c_best = grb080916c.get_all_best_models()
#
# print(grb080916c.get_model('band', EpisodeTypes.T90))

working_model = grb080916c_best[0]

sp = SpectralModels(working_model, "nfn").get_values(in_ergs=True)

x = np.logspace(1, 7, 10000)

plt.loglog(x, sp[0][0], 'r--')
plt.loglog(x, sp[0][1], 'b--')
plt.loglog(x, sp[1], 'k')
# plt.ylim(bottom=1, top=1e3)
plt.show()
