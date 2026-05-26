"""Created on May 26 20:25:58 2026"""
from grb_research import TimeInterval
from grb_research.grb_constants import long_to_short
from grb_research.grb_time import EpisodeTypes
from grb_research.grb_utils import EpisodeMarkerResolver

"""
GRB Spectral Properties Visualization Script
Publication-ready figures for research paper
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ============================================================
# 1. LOAD DATA
# ============================================================
df = pd.read_csv('./flux_energy_flux.csv')

# ============================================================
# 2. STYLE CONFIGURATION
# ============================================================
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 12,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': ':',
    'axes.axisbelow': True,
})

grbs = df['grb_name'].unique()
model_colors = {
    'SBPL_BB': '#1f77b4', 'BAND_BB': '#ff7f0e', 'BAND': '#2ca02c',
    'SBPL': '#d62728', 'PL': '#9467bd', 'CPL': '#8c564b'
}
grb_palette = {
    'GRB080916009': '#1f77b4', 'GRB140206275': '#ff7f0e',
    'GRB131014215': '#2ca02c', 'GRB231129779': '#d62728'
}
markers = {
    'GRB080916009': 'o', 'GRB140206275': 's',
    'GRB131014215': '^', 'GRB231129779': 'D'
}

# ============================================================
# 5. FIGURE 3: Flux vs Fluence Correlation
# ============================================================
fig, ax = plt.subplots(2, 2, figsize=(9, 7), squeeze=False, sharex=True, sharey=True)
ax_flat = ax.flatten()

[i.set_xscale('log') for i in ax_flat]
[i.set_yscale('log') for i in ax_flat]

emr = EpisodeMarkerResolver(t90_marker='o')
kev_to_erg = 1.602e-9
flux_ref = np.logspace(0, 3, 200)  # spans your x-axis range
for idx2, grb in enumerate(grbs):
    tr_count = 0
    sub = df[df['grb_name'] == grb]
    for _, row in sub.iterrows():
        if 'TR' not in row['ep_type']:
            ep_type = EpisodeTypes[row['ep_type']]
            mm = emr.resolve(TimeInterval(ep_type))
            col_ = emr.get_color(TimeInterval(ep_type))
        else:
            ep_type = EpisodeTypes.TR
            ep_type = TimeInterval(ep_type, index=tr_count)
            mm = emr.resolve(ep_type)
            col_ = emr.get_color(ep_type)
            tr_count += 1

        ax_flat[idx2].scatter(row['flux'], row['fluence'],
                               marker=mm, color=col_, label=row['ep_type'], zorder=1)

        for e_kev in [10, 100]:
            e_erg = e_kev * kev_to_erg
            ax_flat[idx2].plot(flux_ref, e_erg * flux_ref,
                               'k--', alpha=0.25, lw=1, zorder=0)
            # label at the right edge
            ax_flat[idx2].text(flux_ref[-1], e_erg * flux_ref[-1],
                               f'⟨E⟩ = {e_kev} keV',
                               fontsize=8, color='gray',
                               va='bottom', ha='right')

        ax_flat[idx2].legend(loc='best', title=f"GRB{long_to_short[grb]}", ncol=3, fontsize=8)
# [i.legend(loc='best') for i in ax_flat]
plt.xlim(left=0.75)
plt.ylim(top=4.5e-4)

[i.set_xlabel(r'Flux (ph cm$^{-2}$ s$^{-1}$)') for i in ax_flat[2:]]
[i.set_ylabel(r'Energy flux (erg cm$^{-2}$ s$^{-1}$)') for i in ax_flat[::2]]
[i.grid(True, which='both') for i in ax_flat]
plt.tight_layout()
# plt.show()
[plt.savefig(f'flux_vs_energy_flux.{i}') for i in ['png', 'pdf']]
