"""Created on Mar 18 09:16:55 2026"""

import json
from dataclasses import dataclass

import numpy as np
from matplotlib import pyplot as plt

from src.grb_research import GRB, find_project_root, Model, ModelSet
from src.grb_research.grb_constants import short_to_long
from src.grb_research.grb_enums import GoodnessOfFit

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

grb_name = "110731A"

with open(result_file, "r") as f:
    grb080916c_data = json.load(f)[short_to_long[grb_name]]

grb080916c = GRB.from_dictionary(grb_name, grb080916c_data)

base_ = 'SBPL'

band_all = grb080916c.get_model(f'{base_}')  # [:-3]
band_bb_all = grb080916c.get_model(f'{base_}_BB')  # [:-3]


def filter_for_safe(simple_model: ModelSet, complex_model: ModelSet) -> tuple[ModelSet, ModelSet]:
    """Determines if a pair of models is safe to compare based on their midpoint and half-difference."""
    safe_idx = [i.status not in [GoodnessOfFit.UNSAFE, GoodnessOfFit.UNKNOWN] for i in complex_model]
    simple_r = ModelSet([j for i, j in zip(safe_idx, simple_model) if i])
    comp_r = ModelSet([j for i, j in zip(safe_idx, complex_model) if i])

    return simple_r, comp_r


band_all, band_bb_all = filter_for_safe(band_all, band_bb_all)


@dataclass
class PeakEnergyRatioResult:
    """Result of calculating the ratio of peak energy to kT."""
    delta_e_peak_over_kt: float
    kt_over_e_peak: float
    band_bb_amp_ratio: float
    bb_band_diff_ratio: float
    ep_type: str
    midpoint: float
    half_difference: float


def calculate_peak_energy_to_kt_ratio(
    model_name: str,
    simple_model: Model,
    complex_model: Model,
) -> PeakEnergyRatioResult:
    """Calculates the peak energy to thermal energy ratio and other related ratios using parameters from simple and complex models.


    :param model_name: The name of the model whose parameters are being analyzed.
    :param simple_model: A model object providing simple model parameter values and intervals.
    :param complex_model: A model object providing complex model parameter values.

    :return: A `PeakEnergyRatioResult` object containing computed ratios for energy distribution and other related metrics.
    """
    m_name = model_name.lower()

    if m_name != 'sbpl':
        ep1 = simple_model.get_parameter_value(f'e_peak_{m_name}')
        ep2 = complex_model.get_parameter_value(f'e_peak_{m_name}')
    else:
        ep1 = simple_model.get_parameter_value(f'e_break_{m_name}')
        ep2 = complex_model.get_parameter_value(f'e_break_{m_name}')

    kt = complex_model.get_parameter_value('kt_bb')
    ep = simple_model.interval.to_string()

    amp1 = simple_model.get_parameter_value(f'amp_{m_name}')
    amp2 = complex_model.get_parameter_value(f'amp_bb')
    amp3 = complex_model.get_parameter_value(f'amp_{m_name}')

    return PeakEnergyRatioResult(
        delta_e_peak_over_kt=(ep2 - ep1) / kt,
        kt_over_e_peak=kt / ep1,
        band_bb_amp_ratio=amp2 / amp1,
        bb_band_diff_ratio=amp1 / (amp1 - amp3),
        midpoint=simple_model.interval.midpoint,
        half_difference=simple_model.interval.half_difference,
        ep_type=ep.split(' ')[0],
    )


del_ep, kt_pe, mid_point, half_diff, ep_type, amp_ratio, amp_ratio2 = [], [], [], [], [], [], []
for i, j in zip(band_all, band_bb_all):
    pp = calculate_peak_energy_to_kt_ratio(f'{base_}', i, j)
    del_ep.append(pp.delta_e_peak_over_kt)
    kt_pe.append(pp.kt_over_e_peak)
    mid_point.append(pp.midpoint)
    half_diff.append(pp.half_difference)
    ep_type.append(pp.ep_type)
    amp_ratio.append(pp.band_bb_amp_ratio)
    amp_ratio2.append(pp.bb_band_diff_ratio)

del_ep, kt_pe, mid_point, half_diff = np.array(del_ep), np.array(kt_pe), np.array(mid_point), np.array(half_diff)
ep_type = np.array(ep_type)
amp_ratio = np.array(amp_ratio)
amp_ratio2 = np.array(amp_ratio2)

f, ax = plt.subplots(2, 2, figsize=(9, 8), sharey=True)
ax = ax.flatten()

for i, j, k, l, m, n1, n2 in zip(mid_point, del_ep, kt_pe, ep_type, half_diff, amp_ratio, amp_ratio2):
    ax[0].errorbar(i, j, xerr=m, fmt='o', capsize=5, label=f'{l}')
    ax[1].scatter(k * 1e3, j, label=f'{l}', marker='o')
    ax[2].scatter(n1 * 1e6, j, label=f'{l}', marker='o')
    ax[3].scatter(n2, j, label=f'{l}', marker='o')

ax[0].set_ylabel(r'$\Delta E_\text{peak} / kT$')
ax[0].set_xlabel('Midpoint\n[s]')
ax[1].set_xlabel(r'$kT / E_\text{peak}$' + '\n' + r'$[10^{-3}]$')
ax[2].set_xlabel(r'$A_\text{BB}/ A_\text{Band}$' + '\n' + r'$[10^{-6}]$')
ax[3].set_xlabel(r'$A_\text{BB}/ (A_\text{Band} - A_\text{Band+BB})$' + '\n' + r'$[10^{-6}]$')
[i.legend(title='Episode') for i in ax]
[i.grid('k--', alpha=0.5) for i in ax]
plt.tight_layout()
plt.show()
