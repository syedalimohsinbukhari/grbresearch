"""Created on Dec 17 13:22:15 2025"""

import json

import matplotlib.pyplot as plt
import numpy as np

from src.grb_research import short_to_long
from src.grb_research.grb_core import GRBCatalog
from src.grb_research.grb_model import ModelSet
from src.grb_research.grb_sed import SpectralModels
from src.grb_research.seds import plot_double_model

# Example data with multiple interval types
with open("./../results.json", "r") as f:
    example_data = json.load(f)

grb_list = ['080916C', '110721A', '110731A', '150210A']
grb_list_long = [short_to_long[i] for i in grb_list]

kev_to_erg = 1.60218e-9

gc = GRBCatalog.from_iterable(grb_list=grb_list, data=example_data, name_mapping=short_to_long)
grb080916c = gc.get_grb(grb_list_long[-1])
grb080916c_best = ModelSet([i.models.best for i in grb080916c.intervals])

x = np.logspace(1, 7, 5_000)

m_name = 'cpl_pl'

pl_bb = grb080916c.intervals.t90.models.get(m_name)
print(grb080916c.intervals.t90.models.get(m_name))

model_instance = SpectralModels(x,
                                pl_bb,
                                grb080916c.intervals[0],
                                model_type='counts')

q = model_instance.get_values(with_errors=True)

p2 = np.vstack([np.array(q[0]), np.array(q[1]).reshape(1, -1)])

plot_double_model(x, p2.tolist(), m_name)
plt.ylim(bottom=1, top=1e3)
plt.show()
