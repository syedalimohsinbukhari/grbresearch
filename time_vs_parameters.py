"""Created on Oct 05 17:03:28 2025"""

from typing import Any, Tuple

import numpy as np
from matplotlib import pyplot as plt
from pymultifit.distributions.backend import line
from pymultifit.fitters import ExponentialFitter
from pymultifit.fitters.backend import BaseFitter
from pymultifit.fitters.others import LineFitter

import src.grb_research.core as grb_core
from src.grb_research import grb_constants

data = grb_core.flattened_json()

grb_name = grb_constants.short_to_long["150210A"]
m_name = "CPL"
a_name = m_name + "_BB"
N_CONST = 4

df_band = grb_core.query_data(data=data, grb_name=grb_name, m_name=a_name)

unique_epochs, n_par, m_labels, epoch = grb_core.grb_characteristics(
    grb_df=df_band, model_name=m_name, epoch_difference=True
)

start, end, diff, mid = [v for _, v in epoch.items()]

e_peak_df = df_band.query(f"param == 'e_peak_{m_name.lower()}'")
e_peak_df.reset_index(drop=True, inplace=True)

e_peak_df.reset_index(drop=True, inplace=True)

x, x_err, y, y_err = mid, diff, e_peak_df["value"].to_numpy(), e_peak_df["error"].to_numpy()
x_red, x_err_red, y_red, y_err_red = x[1:], x_err[1:], y[1:], y_err[1:]


def powerlaw(t, amp, gamma, offset):
    return amp * np.power(t, -gamma) + offset


class PLWithOffSet(BaseFitter):

    def __init__(self, x_values, y_values, max_iterations=1000):
        super().__init__(x_values, y_values, max_iterations)
        self.n_par = 3

    @staticmethod
    def fitter(x: np.ndarray, params: Tuple[float, Any]):
        return powerlaw(x, *params)


f, ax = plt.subplots()

grb_core.two_scatter(start, end, x, y, x_err, y_err, plot_axis=ax, x_time=True, remove_extra=True)

print(x_red, y_red)

pl_f = LineFitter(x_red, y_red)
pl_f.fit([(1, 1)])

ex_f = ExponentialFitter(x_red, y_red)

x_smooth = np.linspace(x.min(), x.max(), 10_000)
y_smooth = line(x_smooth, *pl_f.params)

ax.plot(x_smooth, y_smooth, "k--", label=f"{', '.join([f'{i:.3g}' for i in pl_f.params])}")

ax.grid(True, alpha=0.25, ls="--", zorder=0)
plt.legend(loc="best")
plt.ylabel(r"$E_\text{peak}$ [keV]")
plt.xlabel("Time since burst [s]")
plt.tight_layout()

plt.show()
