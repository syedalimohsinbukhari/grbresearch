"""Created on Sep 30 13:16:33 2025"""

from matplotlib import pyplot as plt

from src.grb_research import model_n_pars, PARAMETERS
from src.grb_research.core import flattened_json, query_data, two_scatter

data = flattened_json()

grb_name = 'GRB080916009'
m_name = 'BAND'
m_name_pl = m_name + '_PL'
N_CONST = 4

df_band = query_data(data=data, grb_name=grb_name, m_name=m_name)
df_band_pl = query_data(data=data, grb_name=grb_name, m_name=m_name_pl)

N_UNIQUE_BAND = df_band['epoch'].unique()
N_UNIQUE_BAND_PL = df_band_pl['epoch'].unique()

n_par_band = model_n_pars[m_name.lower()]
n_par_band_pl = model_n_pars[m_name_pl.lower()]

labels_band = PARAMETERS[m_name.lower()]
labels_band_pl = PARAMETERS[m_name_pl.lower()]

df_band_E_PEAK = df_band.query(f"param == 'e_peak_{m_name.lower()}'")
df_band_pl__E_PEAK = df_band_pl.query(f"param == 'e_peak_{m_name.lower()}'")

merged = df_band_pl__E_PEAK.merge(right=df_band_E_PEAK, on='epoch', suffixes=('_pl', ''))

start_, end_ = [], []
for time_ in df_band_E_PEAK["epoch"]:
    ts, te = map(float, time_.split("_"))
    start_.append(ts)
    end_.append(te)

fig, ax = plt.subplots(figsize=(8, 6))

two_scatter(start_list=start_, end_list=end_,
            val1=merged['value'], val2=merged['value_pl'],
            err1=merged['error'], err2=merged['error_pl'], plot_axis=ax)

# Main axis scaling
# x_min, x_max = ax.get_xlim()
# y_min, y_max = ax.get_ylim()
# lim_min, lim_max = min(x_min, y_min), max(x_max, y_max)
#
# plt.plot([lim_min, lim_max], [lim_min, lim_max], 'k--', zorder=0, )
#
# ax.set_xlim((lim_min, lim_max))
# ax.set_ylim((lim_min, lim_max))

ax.set_xlabel(f"{m_name.upper()}\n" + r"E$_\text{peak}$ [keV]")
ax.set_ylabel(f"{m_name_pl.upper().replace('_', '+')}\n" + r"E$_\text{peak}$ [keV]")
ax.grid(visible=True, which="both", alpha=0.3, ls="--", zorder=0)
ax.legend(loc='best', frameon=True, title=f'{grb_name}')

# axins = inset_axes(ax,
#                    width="40%", height="40%", loc="lower right",
#                    bbox_to_anchor=(0, 0.1, 1, 1), bbox_transform=ax.transAxes, borderpad=0.5)
# axins.set_xlim(-1.05, -0.65)
# axins.set_ylim(-1.05, -0.65)
#
# [i.plot([lim_min, -0.4], [lim_min, -0.4], 'k--') for i in [ax, axins]]
#
# two_scatter(start_, end_,
#             df_band_E_PEAK["value"], df_band_pl__E_PEAK["value"],
#             df_band_E_PEAK["error"], df_band_pl__E_PEAK["error"], plot_axis=axins)
#
# axins.grid(True, which="both", alpha=0.3, ls="--", zorder=0)

fig.tight_layout()
plt.show()
