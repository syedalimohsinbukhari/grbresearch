"""Created on Sep 22 21:50:36 2025"""

import json

import numpy as np
from matplotlib import pyplot as plt

from src.grb_research.core import flatten_results, plot_covariance_corner, filter_covariance, PARAMETERS

with open("results.json", "r") as f:
    data = json.load(f)

data = flatten_results(res_total=data, include_covariance=True)

grb_name = 'GRB110721200'
epoch = '-0.384_9.088'
m_name = 'BAND'
status = 'SAFE'

p1 = data.query(f"GRB == '{grb_name}' and model == '{m_name}' and status == '{status}'")
p1.reset_index(drop=True, inplace=True)

p2 = p1.query(f"epoch == '{epoch}'")

labs = PARAMETERS[m_name.lower()]

vals = p2.iloc[:len(labs)]['value'].to_numpy()
cov_matrix = np.array(p2['value'][len(labs) + 4])
cov_filtered, names_filtered, mask = filter_covariance(cov_matrix=cov_matrix, param_names=labs)

plot_covariance_corner(means=vals[mask], cov_matrix=cov_filtered, param_names=names_filtered)

[plt.savefig(f'./{m_name}.{i}', dpi=600) for i in ['eps', 'pdf']]

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
