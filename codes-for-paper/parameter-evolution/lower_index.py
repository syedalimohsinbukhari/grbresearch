"""Created on Dec 19 12:41:29 2025"""

import matplotlib.pyplot as plt

from src.grb_research import short_to_long
from src.grb_research.core import epoch_to_time, flattened_json, query_data

data = flattened_json('./../../results.json')
grb_name = short_to_long['150210A']
model_name = 'cpl'.upper()

df_cpl = query_data(data, grb_name, model_name, 'safe')
df_cpl.reset_index(drop=True, inplace=True)
df_cpl_index = df_cpl.query(f'param == "index_{model_name.lower()}"')

epoch = df_cpl_index['epoch'].unique()
epoch_dict = epoch_to_time(epochs=epoch, differences=True)

epoch_labels = epoch_dict['episode_label']
start = epoch_dict['start']
end = epoch_dict['end']
difference = epoch_dict['difference']
midpoint = epoch_dict['midpoint']

f, ax = plt.subplots(1, 4, figsize=(15, 4), sharey=True)

for m, d, v, e, c in zip(midpoint, difference, df_cpl_index['value'], df_cpl_index['error'],
                         ['r', 'blue', 'g', 'g', 'g', 'g', 'g']):
    if c == 'r':
        s, en = map(float, epoch[0].split(' ')[1].split('_'))
        ax[0].plot([s, en], [v, v], c='k', ls='--', lw=2)
        ax[0].fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
    else:
        ax[0].errorbar(m, v, xerr=d, yerr=e, color=c, marker='.', ms=10, capsize=5)

ax[0].set_title(f'{model_name}')

model_name = 'sbpl'.upper()
df_pl = query_data(data, grb_name, model_name, 'both')
df_pl.reset_index(drop=True, inplace=True)
df_pl_index = df_pl.query(f'param == "index1_{model_name.lower()}"')
epoch = df_pl_index['epoch'].unique()
epoch_dict = epoch_to_time(epochs=epoch, differences=True)

epoch_labels = epoch_dict['episode_label']
start = epoch_dict['start']
end = epoch_dict['end']
difference = epoch_dict['difference']
midpoint = epoch_dict['midpoint']

for m, d, v, e, c in zip(midpoint, difference, df_pl_index['value'], df_pl_index['error'],
                         ['r', 'blue', 'g', 'g', 'g', 'g', 'g']):
    if c == 'r':
        s, en = map(float, epoch[0].split(' ')[1].split('_'))
        ax[1].plot([s, en], [v, v], c='k', ls='--', lw=2)
        ax[1].fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
    else:
        ax[1].errorbar(m, v, xerr=d, yerr=e, color=c, marker='.', ms=10, capsize=5)

ax[1].set_title(f'{model_name}')

model_name = 'band'.upper()
df_pl = query_data(data, grb_name, model_name, 'both')
df_pl.reset_index(drop=True, inplace=True)
df_pl_index = df_pl.query(f'param == "index1_{model_name.lower()}"')
epoch = df_pl_index['epoch'].unique()
epoch_dict = epoch_to_time(epochs=epoch, differences=True)

epoch_labels = epoch_dict['episode_label']
start = epoch_dict['start']
end = epoch_dict['end']
difference = epoch_dict['difference']
midpoint = epoch_dict['midpoint']

for m, d, v, e, c in zip(midpoint, difference, df_pl_index['value'], df_pl_index['error'],
                         ['r', 'blue', 'g', 'g', 'g', 'g', 'g']):
    if c == 'r':
        s, en = map(float, epoch[0].split(' ')[1].split('_'))
        ax[2].plot([s, en], [v, v], c='k', ls='--', lw=2)
        ax[2].fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
    else:
        ax[2].errorbar(m, v, xerr=d, yerr=e, color=c, marker='.', ms=10, capsize=5)

ax[2].set_title(model_name.upper())

model_name = 'pl'.upper()
df_pl = query_data(data, grb_name, model_name, 'both')
df_pl.reset_index(drop=True, inplace=True)
df_pl_index = df_pl.query(f'param == "index_{model_name.lower()}"')
epoch = df_pl_index['epoch'].unique()
epoch_dict = epoch_to_time(epochs=epoch, differences=True)

epoch_labels = epoch_dict['episode_label']
start = epoch_dict['start']
end = epoch_dict['end']
difference = epoch_dict['difference']
midpoint = epoch_dict['midpoint']

axp = ax[3].twinx()
# ax[3].set_yticks([])

for m, d, v, e, c in zip(midpoint, difference, df_pl_index['value'], df_pl_index['error'],
                         ['r', 'blue', 'g', 'g', 'g', 'g', 'g']):
    if c == 'r':
        s, en = map(float, epoch[0].split(' ')[1].split('_'))
        axp.plot([s, en], [v, v], c='k', ls='--', lw=2)
        axp.fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
    else:
        axp.errorbar(m, v, xerr=d, yerr=e, color=c, marker='.', ms=10, capsize=5)

axp.set_title(model_name.upper())

[i.grid(True, ls='--', alpha=0.5) for i in ax]
[i.set_xlabel('Time [s] since trigger') for i in ax]
# [i.set_ylabel('PL Index') for i in ax]
# ax.set_title(f'{grb_name} - {model_name} Index Evolution')
# ax.legend()
plt.tight_layout()
plt.show()
# [plt.savefig(f'./{grb_name}_parameter_index_evolution.{i}', dpi=600) for i in ['png', 'pdf']]
# plt.close()
