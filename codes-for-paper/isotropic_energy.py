"""Created on Jan 04 18:46:18 2026"""

import json

import matplotlib.pyplot as plt
import numpy as np

from src.grb_research import find_project_root
from src.grb_research.core import break_e_to_e_peak
from src.grb_research.grb_calculations import mcmc_e_iso_sampler
from src.grb_research.grb_constants import short_to_long
from src.grb_research.grb_core import GRBCatalog
from src.grb_research.grb_time import EpisodeTypes


def amati():
    # Array limits
    # powxmin, powxmax = 46, 59
    powymin, powymax = 1.0, 5.0

    # Plot limits
    eisomin, eisomax = 5e51, 3e54
    eipeakmin, eipeakmax = 100.0, 24000.0

    # Constants from Dirirsa et al. 2019
    eiso0, eipeak0 = 1e52, 950.0
    logK, sigma_logK = 1.67, 0.16
    k, sigma_k = logK, sigma_logK
    m, sigma_m = 1.16, 0.37
    sigma_ext = 0.47

    # Generate logarithmically spaced values for Eipeak
    eipeak = np.logspace(powymin, powymax, num=100, base=10.0)
    x = np.log10(eipeak / eipeak0)

    # Calculate sigma_y
    sigmay = np.sqrt(sigma_k**2 + m**2 * 0.0**2 + x**2 * sigma_m**2 + sigma_ext**2)
    sigmay_mean = np.mean(sigmay)  # Use mean for smooth lines

    # Calculate y and Eiso
    y = k + m * x
    eiso = (10.0**y) * eiso0

    # 1 and 2-sigma uncertainty limits
    ytop, ybot = y + sigmay_mean, y - sigmay_mean
    eisotop, eisobot = (10.0**ytop) * eiso0, (10.0**ybot) * eiso0

    ytop2, ybot2 = y + 2.0 * sigmay_mean, y - 2.0 * sigmay_mean
    eisotop2, eisobot2 = (10.0**ytop2) * eiso0, (10.0**ybot2) * eiso0

    plt.figure(figsize=(10, 8))
    # Plotting
    plt.plot(eipeak, eiso, lw=1, alpha=0.45, color='k')
    plt.fill_between(eipeak, eisobot, eisotop, color='#FF6B6B', alpha=0.15)
    plt.fill_between(eipeak, eisobot2, eisotop2, color='#FF9F43', alpha=0.15)

    plt.plot(eipeak, eisobot, color='k', alpha=0.45, linestyle=':')
    plt.plot(eipeak, eisotop, color='k', alpha=0.45, linestyle=':')
    plt.plot(eipeak, eisobot2, color='k', alpha=0.45, linestyle=':')
    plt.plot(eipeak, eisotop2, color='k', alpha=0.45, linestyle=':')

    plt.xlabel(r'E$_\mathrm{i,peak}$ (keV)')
    plt.ylabel(r'E$_\mathrm{iso}$ (erg)')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlim(eipeakmin, eipeakmax)
    plt.ylim(eisomin, eisomax)
    # plt.legend(loc="best")
    # plt.grid(True, which="both", linestyle="--", alpha=0.3)

    # plt.tight_layout()

    # Uncomment to save the plot
    # plt.savefig('amati.png', bbox_inches='tight')
    # plt.savefig('amati.pdf', bbox_inches='tight')


def plot_amati_relation(multiple=None):
    """
    Plot the Amati-like relation for GRBs with 1, 2, and 3 sigma boundaries.

    The relation is:
    E_iso / 10^52 erg = 10^(1.67 ± 0.16) * (E_i,p / 950 keV)^(1.16 ± 0.37)
    """

    # Define parameters
    a_central = 1.67  # log10 normalization
    a_error = 0.16  # 1-sigma error in normalization
    b_central = 1.16  # power-law index
    b_error = 0.37  # 1-sigma error in index

    E_peak_i = np.logspace(0, 4, 1_000)  # from 1 to 10^4 keV in log space
    x = E_peak_i / 950.0  # normalized energy

    log10_y_central = a_central + b_central * np.log10(x)
    y_central = 10**log10_y_central  # E_iso in units of 10^52 erg

    sigma_levels = [1, 2, 3]

    colors = ['#FF6B6B', '#FF9F43', '#FFD166'][::-1]  # red, orange, yellow

    plt.figure(figsize=(10, 10))

    mult = 1 if multiple is None else multiple

    for i, sigma in enumerate(reversed(sigma_levels)):
        delta_log10_y = sigma * np.sqrt(a_error**2 + (b_error * np.log10(x))**2)

        log10_y_upper = log10_y_central + delta_log10_y
        log10_y_lower = log10_y_central - delta_log10_y

        y_upper = 10**log10_y_upper
        y_lower = 10**log10_y_lower

        plt.fill_between(E_peak_i, y_lower * mult, y_upper * mult,
                         alpha=0.25, color=colors[i])

    plt.plot(E_peak_i, y_central * mult, 'k-', linewidth=2, label=r'$E_{\mathrm{iso}} \propto E_{\mathrm{i,p}}^{1.16}$')

    # Plot formatting
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel(r'$E_{\mathrm{i,p}}$ [keV]', fontsize=14)
    plt.ylabel(r'$E_{\mathrm{iso}}$ / 1E52 [erg]', fontsize=14)
    plt.grid(True, which="both", ls="--", alpha=0.15)
    # plt.legend(loc='best', fontsize=12)
    plt.xlim(10, 1e4)
    plt.ylim(bottom=1e50 if multiple is not None else 1, top=1e55)

    plt.tight_layout()

    return E_peak_i, y_central


SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

with open(result_file, "r") as f:
    example_data = json.load(f)

grb_list = ["080916C", "110721A", "110731A", "150210A"]
grb_list_long = [short_to_long[i] for i in grb_list]

gc = GRBCatalog.from_iterable(grb_list=grb_list, data=example_data, name_mapping=short_to_long)

grb080916c = gc.get_grb(grb_list_long[0])
grb110721a = gc.get_grb(grb_list_long[1])
grb110731a = gc.get_grb(grb_list_long[2])
grb150210a = gc.get_grb(grb_list_long[3])

z = [4.35, 0.3826, 2.83]
grb080916c_best = grb080916c.get_all_best_models()
grb110721a_best = grb110721a.get_all_best_models()
grb110731a_best = grb110731a.get_all_best_models()
grb150210a_best = grb150210a.get_all_best_models()

grb_best_all = [grb080916c_best, grb110721a_best, grb110731a_best]

marker = ['o', 'v', 's']

# model_to_evaluate = grb080916c_best[0]

amati()
# plot_amati_relation(1e52)
n_sample = 100


def plot_grbs_in_amati(best_model_list, redshift_list, marker_list, is_1502=False):
    ep_sc, ei_sc, col = [], [], []
    for index, k in enumerate(best_model_list):
        for m in k:
            m_name = m.name
            print(m_name)
            pc = m.get_parameters
            pc_names = [i.name for i in pc]
            # print(pc_names)
            cov_ = 0.5 * (m.covariance_matrix_value + m.covariance_matrix_value.T)
            if 'sbpl' in m_name.lower():
                new_sample_size = int(1.5 * n_sample)
                vals = pc.get_populated_values(cov_, size=new_sample_size)
                mvd = {}
                for i, v in enumerate(pc_names):
                    mvd[v] = vals[:, i]
                mask = np.logical_and(np.abs((mvd['index1_sbpl'] + mvd['index2_sbpl'] + 4) / (mvd['index1_sbpl'] - mvd['index2_sbpl'])) < 1,
                                      mvd['e_break_sbpl'] > 0)
                mvd_filtered = {k: v[mask] for k, v in mvd.items()}

                if mvd_filtered['index1_sbpl'].shape[0] < n_sample:
                    raise ValueError("Not enough samples")

                rng = np.random.default_rng()  # or pass a seeded RNG if you want reproducibility
                idx = rng.choice(mvd_filtered['index1_sbpl'].shape[0], size=n_sample, replace=False)

                mvd_n_samples = {k: v[idx] for k, v in mvd_filtered.items()}

                vals = break_e_to_e_peak(mvd_n_samples['index1_sbpl'], mvd_n_samples['index2_sbpl'],
                                         mvd_n_samples['e_break_sbpl'])
                e_iso = mcmc_e_iso_sampler(m, redshift_list[index], n_samples=n_sample, n_grid=5000, method=2,
                                           samples=np.array(list(mvd_n_samples.values())).T)
            else:
                name_split = m_name.lower().split("_")
                if len(name_split) > 1:
                    name_split = name_split[0] if "BB" in m_name else name_split[1]
                else:
                    name_split = m_name
                vals = pc.get_populated_values(cov_, size=n_sample)
                mvd = {}
                for i, v in enumerate(pc_names):
                    mvd[v] = vals[:, i]
                vals = mvd[f'e_peak_{name_split.lower()}']

                e_iso = mcmc_e_iso_sampler(m, redshift_list[index], n_samples=n_sample, n_grid=5000, method=2,
                                           samples=np.array(list(mvd.values())).T)

            e_peak_i = vals * (1 + redshift_list[index])

            p16_e_peak, p50_e_peak, p84_e_peak = np.percentile(e_peak_i, [16, 50, 84])
            p16_e_iso, p50_e_iso, p84_e_iso = np.percentile(e_iso, [16, 50, 84])

            x_err = np.array([[p50_e_peak - p16_e_peak], [p84_e_peak - p50_e_peak]])
            # y_err = np.array([[p50_e_iso - p16_e_iso], [p84_e_iso - p50_e_iso]])
            # y_err = np.array([[p50]])
            # print(p50_e_peak, p50_e_iso * 1e52)

            col = 'r' if m.interval.kind == EpisodeTypes.T90 else 'g' if m.interval.kind in [EpisodeTypes.EX0, EpisodeTypes.EX1] else 'b'

            plt.errorbar(p50_e_peak, p50_e_iso, xerr=x_err, capsize=5, fmt=marker_list[index], ms=8,
                         label=f'{grb_list_long[index] if not is_1502 else grb_list_long[-1]}' if m.interval.kind == EpisodeTypes.T90 else '',
                         color='r' if m.interval.kind == EpisodeTypes.T90 else 'g' if m.interval.kind in [EpisodeTypes.EX0,
                                                                                                          EpisodeTypes.EX1] else 'b',
                         alpha=0.5 if is_1502 else 1)

            ep_sc.append(p50_e_peak)
            ei_sc.append(p50_e_iso)

    if is_1502:
        plt.plot(np.array(ep_sc), np.array(ei_sc), f'{col}--', marker='D', alpha=0.5, ms=1)


# plot_amati_relation(1e52)
plot_grbs_in_amati(grb_best_all, z, marker)


def plot_1502(best_model):
    z_list = [1, 2, 3, 4, 5, 6, 7]
    grb150210a_mod = [[best_model]] * len(z_list)
    plot_grbs_in_amati(grb150210a_mod, z_list, ['D'] * len(z_list), is_1502=True)


[plot_1502(i) for i in grb150210a_best]

plt.legend()
handles, labels = plt.gca().get_legend_handles_labels()

plt.gca().legend(handles[:4], labels[:4], ncols=4, title='Amati Relationship', loc='upper left')
plt.tight_layout()
plt.show()
