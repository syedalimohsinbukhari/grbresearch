"""Created on Dec 17 13:22:15 2025"""

from matplotlib import pyplot as plt

from src.grb_research import short_to_long
from src.grb_research.core import epoch_to_time, flattened_json, query_data


class TimeIntervals:

    def __init__(self, epoch_list, order_list):
        self.epoch_list = epoch_list
        self.order_list = order_list

    def __repr__(self):
        parts = []
        for ep in self.order_list:
            times = self.get_time_from_episode(ep)
            if times is None:
                parts.append(f"{ep}=None")
            else:
                # format with concise float representation
                parts.append(f"{ep}={times[0]:g}_{times[1]:g}")
        return f"TimeIntervals\n{', '.join(parts)}"

    def get_time_from_episode(self, episode_name):
        if episode_name == 'all':
            return {
                ep: tuple(map(float, epoch.split('_')))
                for ep, epoch in zip(self.order_list, self.epoch_list)
            }

        for ep, epoch in zip(self.order_list, self.epoch_list):
            if ep == episode_name:
                return list(map(float, epoch.split('_')))

        return None


data = flattened_json("./../results.json")

# 080916C
# c_list = ['r', 'blue', 'g', 'g', 'g', 'g', 'blue', 'g']
# 110713A
# c_list = ['r', 'blue', 'g', 'g', 'blue', 'g']
# 110721A
# c_list = ['r', 'b', 'g', 'g']
# 150210A
# c_list = ['r', 'blue', 'g', 'g', 'g', 'g', 'g']

grb_name = short_to_long['110721A']
model_name = 'cpl'.upper()
c_list = ['r', 'b', 'g', 'g']

df_band = query_data(data, grb_name, model_name, 'safe')
df_band_e_peak = df_band.query(f'param == "e_peak_{model_name.lower()}"')
df_band_e_peak.reset_index(drop=True, inplace=True)

epoch = df_band['epoch'].unique()

epoch_dict = epoch_to_time(epoch, differences=True)
start = epoch_dict['start']
end = epoch_dict['end']
difference = epoch_dict['difference']
midpoint = epoch_dict['midpoint']

print(df_band_e_peak)

plt.figure(figsize=(6, 3))
for m, d, v, e, c in zip(midpoint, difference, df_band_e_peak['value'], df_band_e_peak['error'], c_list):
    if c == 'r':
        s, en = map(float, epoch[0].split(' ')[1].split('_'))
        plt.plot([s, en], [v, v], color='k', ls='--', lw=2)
        plt.fill_between(x=[s, en], y1=v - e, y2=v + e, color='k', alpha=0.15)
    else:
        plt.errorbar(m, xerr=d, y=v, yerr=e, ls='', marker='.', ms=10, capsize=5, color=c)
plt.grid(True, ls='--', alpha=0.3)
plt.xlabel('Time since trigger [s]')
plt.ylabel(r'E$_{\rm peak}$ [keV]')
plt.tight_layout()
plt.show()
# [plt.savefig(f'./{grb_name}_{model_name}_E_peak_over_time.{i}', dpi=600) for i in ['png', 'pdf']]
# plt.close()
