"""Created on Oct 11 07:37:36 2025"""

import matplotlib.pyplot as plt
import numpy as np
from uncertainties import correlated_values, unumpy

import src.grb_research.seds as grb_seds
from src.grb_research.core import flattened_json, query_data
from src.grb_research.grb_constants import model_n_pars, short_to_long

BEST_MODEL_FUNCTION_DICT = {
    "CPL": grb_seds.cutoff_powerlaw,
    "BAND": grb_seds.band_function,
    "SBPL": grb_seds.smoothly_broken_power_law,
}
data = flattened_json()

grb_name = short_to_long["150210A"]
grb150210A_data = data.query(f"GRB == '{grb_name}'")
grb150210A_data.reset_index(drop=True, inplace=True)
BEST_MODELS = ["SBPL", "CPL", "CPL", "SBPL", "BAND", "BAND", "CPL"]
ep_names = [r"T$_{90}$", "EX-A", "I", "II", "III", "IV", "V"]
ep_colors = ["k", "C6", "tab:red", "tab:green", "tab:blue", "tab:orange", "maroon"]
styles = ["-", "-.", "--", "--", "--", "--", "--"]
unique_epochs = grb150210A_data["epoch"].unique()

use_ergs = True
factor = 1.60217662e-9 if use_ergs else 1.0

f, ax = plt.subplots(figsize=(10, 8))

x = np.logspace(1, 7, 10_000)


def uncertainty_dissection(x_array, uncertainty_values, multiplicative_factor=1.0):
    y_nom = unumpy.nominal_values(uncertainty_values)
    y_err = unumpy.std_devs(uncertainty_values)

    y = y_nom * multiplicative_factor * x_array**2
    y_upper = (y_nom + y_err) * multiplicative_factor * x_array**2
    y_lower = (y_nom - y_err) * multiplicative_factor * x_array**2

    return y_nom, y_err, (y, y_upper, y_lower)


for index, episode in enumerate(unique_epochs):
    pq = query_data(data=grb150210A_data, grb_name=grb_name, m_name=BEST_MODELS[index], epoch=episode)
    n_pars = model_n_pars[BEST_MODELS[index].lower()]
    vals = pq["value"].iloc[:n_pars].to_numpy()
    cov = np.array(pq["value"].iloc[-2])
    vals_U = correlated_values(nom_values=vals, covariance_mat=cov)

    m_v = BEST_MODEL_FUNCTION_DICT[BEST_MODELS[index]](x, *list(vals_U))
    y_norm, y_err, (y_plot, y_upper, y_lower) = uncertainty_dissection(x, m_v, factor)

    color = ep_colors[index]
    plot_label = f"{ep_names[index]}: {BEST_MODELS[index]}"
    ax.loglog(x, y_plot, styles[index], color=color, label=plot_label)
    ax.fill_between(x=x, y1=y_lower, y2=y_upper, color=color, alpha=0.25)

plt.grid(True, ls="--", color="gray", alpha=0.25, zorder=0)
plt.ylim([1e-9, 4e-5])
plt.xlim([10, 1e7])
plt.xlabel("Energy [keV]")
plt.ylabel("Flux (erg cm$^{-2}$ s$^{-1}$)")
plt.legend(loc="best")
plt.tight_layout()
[plt.savefig(f"GRB150210A_BEST_BUTTERFLY_PLOTS.{i}", dpi=600) for i in ["pdf", "png"]]
plt.close()
