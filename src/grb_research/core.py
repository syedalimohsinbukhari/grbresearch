"""Created on Sep 20 12:48:54 2025"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn
from matplotlib.patches import Ellipse
from uncertainties import correlated_values

from . import OK_THRESHOLD, NOK_THRESHOLD, model_n_pars, PARAMETERS

m_style = seaborn.color_palette("deep6")


def get_directories_in_current_folder(cur_dir=None):
    current_directory = os.getcwd() if cur_dir is None else cur_dir
    all_entries = os.listdir(current_directory)
    directories = []
    for entry in all_entries:
        full_path = os.path.join(current_directory, entry)
        if np.logical_and(os.path.isdir(full_path),
                          np.logical_or(entry.startswith('GRB'),
                                        entry.startswith('Ep'))
                          ):
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
    for k_, v_ in u.items():
        if isinstance(v_, dict):
            # ensure destination has a dict to merge into
            node = d.setdefault(k_, {})
            if isinstance(node, dict):
                deep_merge(d=node, u=v_)
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

    fig, axes = plt.subplots(n_params, n_params, figsize=(3 * n_params, 2.5 * n_params), constrained_layout=False)

    for i in range(n_params):
        for j in range(n_params):
            ax = axes[i, j]

            if i == j:
                # 1D Gaussian histogram centered on mean
                vals = np.random.normal(loc=means[i], scale=stds[i], size=10_000)
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

                samples = np.random.multivariate_normal(mean=[means[j], means[i]], cov=cov_2d, size=5_000)

                ax.scatter(samples[:, 0], samples[:, 1], s=1, color='k', alpha=0.3, zorder=1)
                for k, n_std in enumerate(n_stds[::-1]):
                    if n_std < max(n_stds):
                        width, height = 2 * n_std * np.sqrt(vals_)
                        ellipse = Ellipse(xy=(float(means[j]), float(means[i])),
                                          width=width, height=height, angle=theta,
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

    top, right = 0.96 if n_params > 4 else 0.94, 0.97

    fig.subplots_adjust(left=right * 0.1,
                        bottom=top * 0.1,
                        right=right,
                        top=top,
                        wspace=0.03,
                        hspace=0.03)
    return fig, axes


def flattened_json(file_path="results.json"):
    with open(f"{file_path}", "r") as f:
        data = json.load(f)
    return flatten_results(res_total=data, include_covariance=True)


def query_data(data, grb_name: str, m_name: str, status: str = "both", epoch: str = None):
    """
    Query the dataset for GRB, model, and optional filters.

    Parameters
    ----------
    data : pd.DataFrame
        The dataset to query.
    grb_name : str
        Required GRB identifier.
    m_name : str
        Required model name.
    status : str, optional
        Status filter: 'SAFE', 'UNSAFE', or 'both' (default).
    epoch : str, optional
        Epoch filter (default is None).

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.
    """
    query_str = f"GRB == '{grb_name}' and model == '{m_name}'"

    if status.upper() in ("SAFE", "UNSAFE"):
        query_str += f" and status == '{status.upper()}'"
    elif status.lower() != "both":
        raise ValueError("status must be 'SAFE', 'UNSAFE', or 'both'")

    if epoch is not None:
        query_str += f" and epoch == '{epoch}'"

    result = data.query(query_str).reset_index(drop=True)
    return result


def two_scatter(start_list, end_list, val1, val2, err1, err2, ti_fmt='s', ti_color='r', tr_fmt='o',
                x_time=False, plot_axis=None, remove_extra=False):
    for index, (v1, v2, e1, e2) in enumerate(zip(val1, val2, err1, err2)):
        err_crit2 = e2 / abs(v2)
        fmt_, color_ = tr_fmt, m_style[index % len(m_style)]

        if index == 0:
            fmt_, color_ = ti_fmt, ti_color

        if not x_time:
            err_crit1 = e1 / abs(v1)
            err_bad = np.logical_or(err_crit1 > NOK_THRESHOLD, err_crit2 > NOK_THRESHOLD)
            err_warn = np.logical_or(err_crit1 > OK_THRESHOLD, err_crit2 > OK_THRESHOLD)
        else:
            err_bad = err_crit2 > NOK_THRESHOLD
            err_warn = err_crit2 > OK_THRESHOLD

        alpha_mask = np.logical_or(start_list[index] < start_list[0], end_list[index] > end_list[0])

        if index == 0:
            alpha_ = 1.0
        else:
            alpha_ = 0.5 if alpha_mask else 1.0

        if err_bad:
            l_lim, u_lim = 1, 1
        elif err_warn:
            l_lim, u_lim = 0, 1
        else:
            l_lim, u_lim = 0, 0

        if remove_extra:
            if alpha_mask:
                continue

        plot_axis.errorbar(x=v1, y=v2,
                           xerr=e1, yerr=e2,
                           color=color_, fmt=fmt_, capsize=3, lolims=l_lim, uplims=u_lim, alpha=alpha_,
                           label=f"{start_list[index]}_{end_list[index]}")


def epoch_to_time(epochs, differences=False):
    start, end = [], []
    for time_ in epochs:
        ts_, te_ = map(float, time_.split('_'))
        start.append(ts_)
        end.append(te_)
    start, end = np.array(start), np.array(end)
    if differences:
        return {'start': start,
                'end': end,
                'difference': 0.5 * np.diff(a=[start, end], axis=0)[0],
                'midpoint': 0.5 * (start + end)}
    else:
        return start, end


def grb_characteristics(grb_df, model_name, epoch_difference=False):
    unique_epochs = grb_df['epoch'].unique()
    model_n_par = model_n_pars[model_name.lower()]
    model_labels = PARAMETERS[model_name.lower()]
    epoch = epoch_to_time(epochs=unique_epochs, differences=epoch_difference)

    return unique_epochs, model_n_par, model_labels, epoch


def sbpl_e_break_to_e_peak(break_energy, lambda1, lambda2, delta=0.3):
    num = lambda1 + lambda2 + 4
    den = lambda1 - lambda2

    ratio = num / den

    if abs(ratio) > 1:
        raise ValueError(f"Invalid parameters: |(λ₁ + λ₂ + 4)/(λ₁ - λ₂)| = {abs(ratio):.4f} ≥ 1")

    return break_energy * np.power(10, delta * np.arctanh(ratio))
