"""Created on Mar 16 12:27:51 2026"""

import matplotlib.pyplot as plt
import numpy as np
from plotez import plot_errorbar, ErrorPlotConfig
from pymultifit.fitters import LineFitter

from src.grb_research import find_project_root, ModelSet
from src.grb_research.grb_core import prepare_grbs, GRB

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

grb_list = ["080916C", "110721A", "110731A", "150210A"]
gc, grb_list_long, grb_objs, grb_best = prepare_grbs(grb_list, result_file, get_best=True)

grb080916c: GRB = gc.get_grb(grb_list_long[0])
band_bb: ModelSet = grb080916c.get_model("BAND_BB").good

bb_params = np.array([(j.value, j.error) for i in band_bb for j in i.parameters if j.name.endswith('bb')])
amp = bb_params[::2, :]
kt = bb_params[1::2, :]

x = np.arange(len(amp))
print(x)
amp_v, amp_e = amp.T / 1e-6
kt_v, kt_e = kt.T

kt_v, amp_v, kt_e, amp_e = zip(*sorted(zip(amp_v, kt_v, amp_e, kt_e)))

f, ax = plt.subplots()

ax = plot_errorbar(kt_v, x, kt_e, auto_label=True,
                   errorbar_config=ErrorPlotConfig(capsize=5, marker='o', markersize=5, markerfacecolor='k',
                                                   markeredgecolor='k'), axis=ax)
# l_fit = LineFitter(amp_v, x)
# l_fit.fit([(1, 1)])
# l_fit.plot_fit(show_individuals=True, axis=ax)
plt.show()
