"""Created on Dec 19 12:41:29 2025"""

import json

import matplotlib.pyplot as plt
import numpy as np

from src.grb_research import short_to_long
from src.grb_research.grb_class import GRBCatalog


# data = flattened_json('./../../results.json')
# grb_name = short_to_long['080916C']
# model_name = 'cpl'.upper()
#
# df_cpl = query_data(data, grb_name, model_name, 'both')
# df_cpl.reset_index(drop=True, inplace=True)
# df_cpl_index = df_cpl.query(f'param == "index_{model_name.lower()}"')
#
# epoch = df_cpl_index['epoch'].unique()
# epoch_dict = epoch_to_time(epochs=epoch, differences=True)
#
# epoch_labels = epoch_dict['episode_label']
# start = epoch_dict['start']
# end = epoch_dict['end']
# difference = epoch_dict['difference']
# midpoint = epoch_dict['midpoint']
#
# f, ax = plt.subplots(1, 4, figsize=(15, 4), sharey=True)
#
# for m, d, v, e, c in zip(midpoint, difference, df_cpl_index['value'], df_cpl_index['error'],
#                          ['r', 'blue', 'g', 'g', 'g', 'g', 'g']):
#     if c == 'r':
#         s, en = map(float, epoch[0].split(' ')[1].split('_'))
#         ax[0].plot([s, en], [v, v], c='k', ls='--', lw=2)
#         ax[0].fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
#     else:
#         ax[0].errorbar(m, v, xerr=d, yerr=e, color=c, marker='.', ms=10, capsize=5)
#
# ax[0].set_title(f'{model_name}')
#
# model_name = 'sbpl'.upper()
# df_pl = query_data(data, grb_name, model_name, 'both')
# df_pl.reset_index(drop=True, inplace=True)
# df_pl_index = df_pl.query(f'param == "index1_{model_name.lower()}"')
# epoch = df_pl_index['epoch'].unique()
# epoch_dict = epoch_to_time(epochs=epoch, differences=True)
#
# epoch_labels = epoch_dict['episode_label']
# start = epoch_dict['start']
# end = epoch_dict['end']
# difference = epoch_dict['difference']
# midpoint = epoch_dict['midpoint']
#
# for m, d, v, e, c in zip(midpoint, difference, df_pl_index['value'], df_pl_index['error'],
#                          ['r', 'blue', 'g', 'g', 'g', 'g', 'g']):
#     if c == 'r':
#         s, en = map(float, epoch[0].split(' ')[1].split('_'))
#         ax[1].plot([s, en], [v, v], c='k', ls='--', lw=2)
#         ax[1].fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
#     else:
#         ax[1].errorbar(m, v, xerr=d, yerr=e, color=c, marker='.', ms=10, capsize=5)
#
# ax[1].set_title(f'{model_name}')
#
# model_name = 'band'.upper()
# df_pl = query_data(data, grb_name, model_name, 'both')
# df_pl.reset_index(drop=True, inplace=True)
# df_pl_index = df_pl.query(f'param == "index1_{model_name.lower()}"')
# epoch = df_pl_index['epoch'].unique()
# epoch_dict = epoch_to_time(epochs=epoch, differences=True)
#
# epoch_labels = epoch_dict['episode_label']
# start = epoch_dict['start']
# end = epoch_dict['end']
# difference = epoch_dict['difference']
# midpoint = epoch_dict['midpoint']
#
# for m, d, v, e, c in zip(midpoint, difference, df_pl_index['value'], df_pl_index['error'],
#                          ['r', 'blue', 'g', 'g', 'g', 'g', 'g']):
#     if c == 'r':
#         s, en = map(float, epoch[0].split(' ')[1].split('_'))
#         ax[2].plot([s, en], [v, v], c='k', ls='--', lw=2)
#         ax[2].fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
#     else:
#         ax[2].errorbar(m, v, xerr=d, yerr=e, color=c, marker='.', ms=10, capsize=5)
#
# ax[2].set_title(model_name.upper())
#
# model_name = 'pl'.upper()
# df_pl = query_data(data, grb_name, model_name, 'both')
# df_pl.reset_index(drop=True, inplace=True)
# df_pl_index = df_pl.query(f'param == "index_{model_name.lower()}"')
# epoch = df_pl_index['epoch'].unique()
# epoch_dict = epoch_to_time(epochs=epoch, differences=True)
#
# epoch_labels = epoch_dict['episode_label']
# start = epoch_dict['start']
# end = epoch_dict['end']
# difference = epoch_dict['difference']
# midpoint = epoch_dict['midpoint']
#
# axp = ax[3].twinx()
# # ax[3].set_yticks([])
#
# for m, d, v, e, c in zip(midpoint, difference, df_pl_index['value'], df_pl_index['error'],
#                          ['r', 'blue', 'g', 'g', 'g', 'g', 'g']):
#     if c == 'r':
#         s, en = map(float, epoch[0].split(' ')[1].split('_'))
#         axp.plot([s, en], [v, v], c='k', ls='--', lw=2)
#         axp.fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
#     else:
#         axp.errorbar(m, v, xerr=d, yerr=e, color=c, marker='.', ms=10, capsize=5)
#
# axp.set_title(model_name.upper())
#
# [i.grid(True, ls='--', alpha=0.5) for i in ax]
# [i.set_xlabel('Time [s] since trigger') for i in ax]
# # [i.set_ylabel('PL Index') for i in ax]
# # ax.set_title(f'{grb_name} - {model_name} Index Evolution')
# # ax.legend()
# plt.tight_layout()
# plt.show()
# # [plt.savefig(f'./{grb_name}_parameter_index_evolution.{i}', dpi=600) for i in ['png', 'pdf']]
# # plt.close()
def plot_per_episode(values, errors, start, end, difference, midpoints, axes):
    axes.plot([start[0], end[0]], [values[0], values[0]], c="k", ls="--", lw=2)
    axes.fill_between(x=[start[0], end[0]], y1=values[0] - errors[0], y2=values[0] + errors[0], color="k", alpha=0.15)
    for i, value in enumerate(midpoints[1:]):
        axes.errorbar(
            value,
            values[i + 1],
            xerr=difference[i + 1],
            yerr=errors[i + 1],
            color="b" if np.logical_or(start[i + 1] < start[0], end[i + 1] > end[0] + 0.064) else "g",
            marker=".",
            ms=10,
            capsize=5,
        )


with open("./../../results.json", "r") as f:
    example_data = json.load(f)

f, ax = plt.subplots(1, 4, figsize=(15, 4), sharey=True)

grb_list = ["080916C", "110721A", "110731A", "150210A"]
gc = GRBCatalog.from_iterable(grb_list, data=example_data)

grb080916c = gc[short_to_long[grb_list[0]]]
grb110721a = gc[short_to_long[grb_list[1]]]
grb110731a = gc[short_to_long[grb_list[2]]]
grb150210a = gc[short_to_long[grb_list[3]]]

st, ed, diff, mp = grb080916c.extract_interval_arrays(return_all=True, exclude_ex=True)

print(grb080916c.intervals.get_model("band"))

v, e = grb080916c.get_model("cpl").get_parameter("index_cpl", exclude_ex=True)

plot_per_episode(v, e, st, ed, diff, mp, ax[0])
ax[0].set_title("CPL")

v, e = grb110731a.get_model("band").get_parameter("index1_band", exclude_ex=True)
plot_per_episode(v, e, st, ed, diff, mp, ax[1])
ax[1].set_title("BAND")
v, e = grb150210a.get_model("sbpl").get_parameter("index1_sbpl", exclude_ex=True)

plot_per_episode(v, e, st, ed, diff, mp, ax[2])
ax[2].set_title("SBPL")

v, e = grb080916c.get_model("pl").get_parameter("index_pl")
ax2 = ax[3].twinx()
plot_per_episode(v, e, st, ed, diff, mp, ax2)
ax2.set_title("PL")


plt.tight_layout()
plt.show()
