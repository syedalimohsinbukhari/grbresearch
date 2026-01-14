"""Created on Jan 04 18:46:18 2026"""

import json

import numpy as np
from scipy.integrate import simpson

from src.grb_research import find_project_root, SpectralModels
from src.grb_research.grb_calculations import mcmc_e_iso_sampler, mcmc_spectra_sampler
from src.grb_research.grb_constants import kev_to_erg, short_to_long
from src.grb_research.grb_core import GRBCatalog

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

with open(result_file, "r") as f:
    example_data = json.load(f)

grb_list = ["080916C", "110721A", "110731A", "150210A"]
grb_list_long = [short_to_long[i] for i in grb_list]

gc = GRBCatalog.from_iterable(grb_list=grb_list, data=example_data, name_mapping=short_to_long)

grb080916c = gc.get_grb(grb_list_long[0])

grb080916c_best = grb080916c.get_all_best_models()
model_to_evaluate = grb080916c_best[0]

sp = SpectralModels(model_to_evaluate, "energy").get_values()

x = np.logspace(np.log10(8), np.log10(30_000), 1_000)

# pp = mcmc_spectra_sampler(model_to_evaluate, e_range=(1, 7), n_samples=1000, n_grid=1000)
# pq = np.array([simpson(x * i, x=x) * model_to_evaluate.interval.duration * kev_to_erg for i in pp])

# print(np.mean(pq), np.median(pq), np.percentile(pq, 84), sep=', ')

n_iterations = 100

q = mcmc_e_iso_sampler(model_to_evaluate, z=4.35, n_samples=1000, n_grid=1000)
# q = np.array(q)
print(np.percentile(q, [16, 50, 84]))
q = np.array(q)

# q_arr = q[~np.any(q < 0, axis=1)]
