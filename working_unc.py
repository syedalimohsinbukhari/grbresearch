"""Created on Sep 27 17:17:41 2025"""

import matplotlib.pyplot as plt
import numpy as np
from uncertainties import correlated_values

from src.grb_research import short_to_long, model_n_pars
from src.grb_research.core import flattened_json, query_data
from src.grb_research.seds import model_bb, plot_double_model

grb_name = short_to_long['150210A']
keVToErgs = 1.6021766e-9
data = flattened_json()
x = np.logspace(1, 7, 10_000)

pp = query_data(data=data, grb_name=grb_name, m_name='SBPL_BB', epoch='0.832_2.176')
vals = pp['value'].iloc[:model_n_pars['SBPL_BB'.lower()]].to_numpy()
cov = np.array(pp['value'].iloc[-2])

vals_U = correlated_values(vals, cov)
m_v = model_bb(x=x, model_values=vals_U, model_string='SBPL_BB')
plot_double_model(x=x, model_values=m_v, model_string='SBPL_BB', use_ergs=True)
plt.ylim([1e-9, 4e-5])
plt.show()

# import matplotlib.pyplot as plt
# import numpy as np
# from uncertainties import correlated_values
#
# import src.grb_research.core as grb_core
# import src.grb_research.seds as grb_seds
# from src.grb_research import short_to_long
#
# grb_name = short_to_long['080916C']
#
# SINGLE_MODEL_FUNCTION_DICT = {'PL': grb_seds.powerlaw,
#                               'CPL': grb_seds.cutoff_powerlaw,
#                               'BAND': grb_seds.band_function,
#                               'SBPL': grb_seds.smoothly_broken_power_law}
#
# keVToErgs = 1.60217662e-9
# data = grb_core.flattened_json()
# x = np.logspace(start=1, stop=7, num=200)
#
# f, ax = plt.subplots(figsize=(8, 6))
#
# for model in SINGLE_MODEL_FUNCTION_DICT.keys():
#     pp = grb_core.query_data(data=data, grb_name=grb_name, m_name=model)
#
#     episode, n_pars, labels, epoch = grb_core.grb_characteristics(grb_df=pp,
#                                                                   model_name=model,
#                                                                   epoch_difference=True)
#
#     pq = pp.query(f"epoch == '{episode[3]}'")
#     vals = pq['value'].iloc[:n_pars].to_numpy()
#     cov = np.array(pq['value'].iloc[-2])
#     vals_U = correlated_values(nom_values=vals, covariance_mat=cov)
#     m_v = SINGLE_MODEL_FUNCTION_DICT[model](x, *list(vals_U))
#     grb_seds.plot_single_model(x=x, model_values=m_v, model_string=model, x_label='Energy (keV)',
#                                y_label='Flux (erg cm$^{-2}$ s$^{-1}$)', use_ergs=True, axis=ax)
#
# plt.xscale('log')
# plt.yscale('log')
# plt.tight_layout()
# plt.show()
