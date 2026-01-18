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


def amati_mod(
        e_iso_norm=1e52,
        e_i_peak_norm=950.0,
        log_k=1.67,
        sigma_log_k=0.16,
        m=1.16,
        sigma_m=0.37,
        sigma_ext=0.47,
        sigmas=(1, 2, 3),
        x_lim=(10, 1e5),
        y_lim=(1e50, 1e55),
        num_points=1000,
):
    """Plot the Amati relation with confidence bands."""

    # Generate e_i_peak and calculate log-space values
    e_i_peak = np.logspace(np.log10(x_lim[0]), np.log10(x_lim[1]), num=num_points)
    x = np.log10(e_i_peak / e_i_peak_norm)

    # Central relation and point-wise uncertainty
    y = log_k + m * x
    sigma_y = np.sqrt(sigma_log_k**2 + x**2 * sigma_m**2 + sigma_ext**2)
    e_isotropic = (10**y) * e_iso_norm

    # Plot central line
    plt.plot(e_i_peak, e_isotropic, lw=1, alpha=0.45, color="k")

    # Plot confidence bands
    colors = ["#FFD166", "#FF9F43", "#FF6B6B"]
    for i, n_sigma in enumerate(sigmas):
        c = colors[i % len(colors)]
        y_upper, y_lower = y + n_sigma * sigma_y, y - n_sigma * sigma_y
        e_iso_upper, e_iso_lower = (10**y_upper) * e_iso_norm, (10**y_lower) * e_iso_norm

        plt.fill_between(e_i_peak, e_iso_lower, e_iso_upper, color=c, alpha=0.1)
        plt.plot(e_i_peak, e_iso_lower, color=c, ls='--')
        plt.plot(e_i_peak, e_iso_upper, color=c, ls='--')

    # Formatting
    plt.xlabel(r"E$_\text{i,peak}$ [keV]", fontsize=12)
    plt.ylabel(r"E$_\text{iso}$ [erg]", fontsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlim(x_lim)
    plt.ylim(y_lim)


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

marker = ["o", "v", "s"]


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
            if "sbpl" in m_name.lower():
                new_sample_size = int(1.5 * n_sample)
                vals = pc.get_populated_values(cov_, size=new_sample_size)
                mvd = {}
                for i, v in enumerate(pc_names):
                    mvd[v] = vals[:, i]
                mask = np.logical_and(
                    np.abs((mvd["index1_sbpl"] + mvd["index2_sbpl"] + 4) / (mvd["index1_sbpl"] - mvd["index2_sbpl"]))
                    < 1,
                    mvd["e_break_sbpl"] > 0,
                )
                mvd_filtered = {k: v[mask] for k, v in mvd.items()}

                if mvd_filtered["index1_sbpl"].shape[0] < n_sample:
                    raise ValueError("Not enough samples")

                rng = np.random.default_rng()  # or pass a seeded RNG if you want reproducibility
                idx = rng.choice(mvd_filtered["index1_sbpl"].shape[0], size=n_sample, replace=False)

                mvd_n_samples = {k: v[idx] for k, v in mvd_filtered.items()}

                vals = break_e_to_e_peak(
                    mvd_n_samples["index1_sbpl"], mvd_n_samples["index2_sbpl"], mvd_n_samples["e_break_sbpl"]
                )
                e_iso = mcmc_e_iso_sampler(
                    m,
                    redshift_list[index],
                    n_samples=n_sample,
                    n_grid=5000,
                    method=2,
                    samples=np.array(list(mvd_n_samples.values())).T,
                )
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
                vals = mvd[f"e_peak_{name_split.lower()}"]

                e_iso = mcmc_e_iso_sampler(
                    m,
                    redshift_list[index],
                    n_samples=n_sample,
                    n_grid=5000,
                    method=2,
                    samples=np.array(list(mvd.values())).T,
                )

            e_peak_i = vals * (1 + redshift_list[index])

            p16_e_peak, p50_e_peak, p84_e_peak = np.percentile(e_peak_i, [16, 50, 84])
            p16_e_iso, p50_e_iso, p84_e_iso = np.percentile(e_iso, [16, 50, 84])

            x_err = np.array([[p50_e_peak - p16_e_peak], [p84_e_peak - p50_e_peak]])
            y_err = np.array([[p50_e_iso - p16_e_iso], [p84_e_iso - p50_e_iso]])

            col = (
                "r"
                if m.interval.kind == EpisodeTypes.T90
                else "g" if m.interval.kind in [EpisodeTypes.EX0, EpisodeTypes.EX1] else "b"
            )

            plt.errorbar(
                p50_e_peak,
                p50_e_iso,
                xerr=x_err,
                yerr=y_err,
                capsize=5,
                fmt=marker_list[index],
                ms=8,
                label=(
                    f"{grb_list_long[index] if not is_1502 else grb_list_long[-1]}"
                    if m.interval.kind == EpisodeTypes.T90
                    else ""
                ),
                color=(
                    "r"
                    if m.interval.kind == EpisodeTypes.T90
                    else "g" if m.interval.kind in [EpisodeTypes.EX0, EpisodeTypes.EX1] else "b"
                ),
                alpha=0.5 if is_1502 else 1,
            )

            ep_sc.append(p50_e_peak)
            ei_sc.append(p50_e_iso)

    if is_1502:
        plt.plot(np.array(ep_sc), np.array(ei_sc), f"{col}--", marker="D", alpha=0.5, ms=1)


def plot_unknown_redshift_grb(best_model):
    """Plot the unknown redshift GRB."""
    z_list = [1, 2, 3, 4, 5, 6, 7]
    grb150210a_mod = [[best_model]] * len(z_list)
    plot_grbs_in_amati(grb150210a_mod, z_list, ["D"] * len(z_list), is_1502=True)


n_sample = 48

plt.figure(figsize=(10, 8))
amati_mod()

plot_grbs_in_amati(grb_best_all, z, marker)
[plot_unknown_redshift_grb(i) for i in grb150210a_best]
plt.grid(which='both', ls='--', lw=0.5, color='k', alpha=0.15)
plt.legend()
handles, labels = plt.gca().get_legend_handles_labels()
plt.gca().legend(handles[:4], labels[:4], ncols=2, loc="best", fontsize=12)
plt.tight_layout()
[plt.savefig(f"isotropic_energy.{i}") for i in ["png", "pdf"]]
plt.close()
# plt.show()
