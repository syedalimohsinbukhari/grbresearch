"""Created on Sep 20 12:48:54 2025"""

import os

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse
from uncertainties import correlated_values

model_n_pars = {"pl": 3,
                "bb": 2,
                "cpl": 4,
                "band": 4,
                "sbpl": 6,
                "pl_bb": 5,
                "cpl_pl": 7,
                "cpl_bb": 6,
                "cpl_pl_bb": 9,
                "band_pl": 7,
                "band_bb": 6,
                "band_pl_bb": 9,
                "sbpl_pl": 9,
                "sbpl_bb": 8,
                "sbpl_pl_bb": 11}

pl_par = ['amp_pl', 'e_piv_pl', 'index_pl']
cpl_par = ['amp_cpl', 'e_peak_cpl', 'index_cpl', 'e_piv_cpl']
band_par = ['amp_band', 'e_peak_band', 'index1_band', 'index2_band']
sbpl_par = ['amp_sbpl', 'e_piv_sbpl', 'index1_sbpl', 'e_break_sbpl', 'delta_sbpl', 'index2_sbpl']
bb_par = ['amp_bb', 'kt_bb']

PARAMETERS = {'pl': pl_par,
              'pl_bb': pl_par + bb_par,
              'band': band_par,
              'band_pl': pl_par + band_par,
              'band_bb': band_par + bb_par,
              'band_pl_bb': pl_par + band_par + bb_par,
              'cpl': cpl_par,
              'cpl_pl': pl_par + cpl_par,
              'cpl_bb': cpl_par + bb_par,
              'cpl_pl_bb': pl_par + cpl_par + bb_par,
              'sbpl': sbpl_par,
              'sbpl_bb': sbpl_par + bb_par,
              'sbpl_pl': pl_par + sbpl_par,
              'sbpl_pl_bb': pl_par + sbpl_par + bb_par}


def get_directories_in_current_folder(cur_dir=None):
    """
    Returns a list of directory names in the current working directory.
    """
    current_directory = os.getcwd() if cur_dir is None else cur_dir
    all_entries = os.listdir(current_directory)
    directories = []
    for entry in all_entries:
        full_path = os.path.join(current_directory, entry)
        if os.path.isdir(full_path) and np.logical_or(entry.startswith('GRB'), entry.startswith('Ep')):
            directories.append(entry)
    directories.sort()
    return directories


def get_fit_files_in_current_directory(cur_dir):
    files_ = [f for f in os.listdir(cur_dir) if f.endswith('.fit')]
    files_.sort()
    return files_


def get_value(fit_file, n_parameters, full_cov, return_errors: bool = False, un_correlated=False):
    values = [fit_file[2].data[f"PARAM{i}"][0][0] for i in range(n_parameters)]
    errors = [fit_file[2].data[f"PARAM{i}"][0][1] for i in range(n_parameters)]

    if return_errors:
        return np.array(object=values, dtype=float), np.array(object=errors, dtype=float)
    elif un_correlated:
        return np.array(object=values, dtype=float)
    else:
        return correlated_values(nom_values=values, covariance_mat=full_cov)


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(make_json_safe(v) for v in obj)
    elif hasattr(obj, "tolist"):  # catches numpy arrays/scalars
        return obj.tolist()
    else:
        return obj


def deep_merge(d, u):
    """Recursively merge dict u into dict d (no overwrite of nested dicts)."""
    for k_, v_ in u.items():
        if isinstance(v_, dict):
            # ensure destination has a dict to merge into
            node = d.setdefault(k_, {})
            if isinstance(node, dict):
                deep_merge(node, v_)
            else:
                d[k_] = v_
        else:
            d[k_] = v_
    return d


def covariance_to_correlation(cov):
    cov = np.asarray(a=cov, dtype=float)
    d = np.sqrt(np.diag(cov))
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = cov / np.outer(a=d, b=d)
        corr[~np.isfinite(corr)] = 0.0  # handle 0/0 or inf cases
    return corr


def flatten_results(res_total, include_covariance=True):
    rows = []
    for grb, epochs in res_total.items():
        for ep, models in epochs.items():
            for model, params in models.items():
                status = params.get("_status", "NA")
                for p_name, val in params.items():
                    if p_name == "_status":
                        continue
                    if p_name in ["covariance_matrix", "correlation_matrix"] and not include_covariance:
                        continue  # skip it
                    if isinstance(val, (list, tuple)) and len(val) == 2 and all(np.isscalar(x) for x in val):
                        v, e = val
                    else:
                        v, e = val, None
                    rows.append({
                        "GRB": grb,
                        "epoch": ep,
                        "model": model,
                        "status": status,
                        "param": p_name,
                        "value": v,
                        "error": e,
                    })
    return pd.DataFrame(rows)


def filter_covariance(cov_matrix, param_names):
    """Remove parameters with ~0 variance values from covariance matrix and names."""
    diagonals = np.diag(cov_matrix)
    keep_idx = [i for i, v in enumerate(diagonals.tolist()) if abs(float(v)) != 0.0]
    filtered_cov = cov_matrix[np.ix_(keep_idx, keep_idx)]
    filtered_names = [param_names[i] for i in keep_idx]
    return filtered_cov, filtered_names, keep_idx


def plot_covariance_corner(means, cov_matrix, param_names):
    """
    Corner-style plot with histograms on the diagonal and covariance ellipses off-diagonal.

    Parameters
    ----------
    means : array-like, shape (N,)
        Mean values of the parameters.
    cov_matrix : array-like, shape (N, N)
        Covariance matrix.
    param_names : list of str
        Names of parameters (length N).
    """
    means = np.asarray(means)
    cov_matrix = np.asarray(cov_matrix)
    n_params = len(param_names)

    stds = np.sqrt(np.diag(cov_matrix))
    n_stds = range(1, 4)
    max_std = max(n_stds) + 1

    fig, axes = plt.subplots(nrows=n_params, ncols=n_params, figsize=(3 * n_params, 2.5 * n_params),
                             constrained_layout=False)

    for i in range(n_params):
        for j in range(n_params):
            ax = axes[i, j]

            if i == j:
                # 1D Gaussian histogram centered on mean
                vals = np.random.normal(means[i], stds[i], 10_000)
                ax.hist(vals, bins=24, fc="w", ec='k', histtype='step')
                ax.set_xlim(means[i] - max_std * stds[i], means[i] + max_std * stds[i])
                m, s = np.mean(vals), np.std(vals)
                spec = 'g' if abs(s) < 1 else 'f'
                ax.set_title(rf"{param_names[i]}" + "\n" + rf"${m:.3{spec}}\pm{s:.3{spec}}$", fontsize=14)
            elif j < i:
                # covariance ellipse centered at (mean[j], mean[i])
                cov_2d = cov_matrix[np.ix_([j, i], [j, i])]
                cov_2d = (cov_2d + cov_2d.T) / 2

                vals_, vectors = np.linalg.eigh(cov_2d)
                order = vals_.argsort()[::-1]
                vals_, vectors = vals_[order], vectors[:, order]

                theta = np.degrees(np.arctan2(*vectors[:, 0][::-1]))

                samples = np.random.multivariate_normal([means[j], means[i]], cov_2d, size=5_000)

                ax.scatter(samples[:, 0], samples[:, 1], s=1, color='k', alpha=0.3, zorder=1)
                for k, n_std in enumerate(n_stds[::-1]):
                    if n_std < max(n_stds):
                        width, height = 2 * n_std * np.sqrt(vals_)
                        ellipse = Ellipse((float(means[j]), float(means[i])),
                                          width, height, angle=theta,
                                          ec='r' if k == 1 else 'g',
                                          fc='w', lw=1.5,
                                          zorder=2 + k,
                                          ls='--' if k == 1 else '-.')
                        ax.add_patch(ellipse)

                ax.set_xlim(means[j] - max_std * stds[j], means[j] + max_std * stds[j])
                ax.set_ylim(means[i] - max_std * stds[i], means[i] + max_std * stds[i])
            else:
                ax.axis("off")

            if i == 0 and j == 0:
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_xticklabels([])
                ax.set_yticklabels([])
                ax.set_xlabel("")
                ax.set_ylabel("")
            else:
                if i != n_params - 1:
                    ax.set_xticks([])
                    ax.set_xticklabels([])
                else:
                    ax.set_xlabel(param_names[j])

                if j != 0:
                    ax.set_yticks([])
                    ax.set_yticklabels([])
                else:
                    ax.set_ylabel(param_names[i] if i != 0 else "")

            ax.tick_params(axis='both', labelrotation=45)

    top, right = 0.963 if n_params > 4 else 0.943, 0.95

    fig.subplots_adjust(top=top,
                        bottom=top * 0.1,
                        right=right,
                        left=right * 0.1,
                        hspace=0.03,
                        wspace=0.03)
    return fig, axes
