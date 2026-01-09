"""Created on Sep 22 21:50:36 2025"""

import numpy as np
from matplotlib import pyplot as plt

import src.grb_research.core as grb_core
from src.grb_research.grb_constants import model_n_pars

# setting seed for reproducibility
np.random.seed(42)

data = grb_core.flattened_json()
grb_name = "GRB080916009"
m_name = "BAND"

p1 = grb_core.query_data(data, grb_name, m_name)

epochs = p1["epoch"].unique()

for ep in epochs:
    p1.query(f"epoch == '{ep}'")
    labs = model_n_pars[m_name.lower()]

    vals = p1.iloc[: len(labs)]["value"].to_numpy()
    cov_matrix = np.array(p1["value"][len(labs) + 4])

    (cov_filtered, names_filtered, mask) = grb_core.filter_covariance(cov_matrix=cov_matrix, param_names=labs)

    grb_core.plot_covariance_corner(means=vals[mask], cov_matrix=cov_filtered, param_names=names_filtered)

    [plt.savefig(f"./{m_name}_{ep}.{i}", dpi=600) for i in ["png", "pdf"]]
    plt.close()

# q_e_peak = data.query("model in ['BAND', 'BAND_BB'] and param == 'index2_band' and status == 'SAFE'")
# q_e_peak.reset_index(drop=True, inplace=True)
#
# wide_ = q_e_peak.pivot_table(index=['GRB', 'epoch'], columns="model", values=['value', 'error'])
# wide_.reset_index(drop=False, inplace=True)
#
# fig, ax = plt.subplots()
#
# for grb, subset in wide_.groupby("GRB"):
#     ax.errorbar(
#         subset["value"]["BAND"], subset["value"]["BAND_BB"],
#         xerr=subset["error"]["BAND"], yerr=subset["error"]["BAND_BB"],
#         ls="", marker="o", ms=5, capsize=5, label=grb
#     )
#
# plt.plot([wide_['value']['BAND'].min(), wide_['value']['BAND_BB'].max()],
#          [wide_['value']['BAND'].min(), wide_['value']['BAND_BB'].max()], 'k--')
# plt.grid(True, ls="--", alpha=0.5)
# ax.set_xlabel("BAND e_peak (keV)")
# ax.set_ylabel("BAND_BB e_peak (keV)")
# # plt.xscale('log')
# # plt.yscale('log')
# ax.legend(title="GRB")
# plt.tight_layout()
# plt.show()
