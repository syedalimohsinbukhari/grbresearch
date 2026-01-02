"""Created on Sep 20 12:48:54 2025"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn
from matplotlib.patches import Ellipse
from uncertainties import unumpy

from . import model_n_pars, MODEL_PARAMETERS, NOK_THRESHOLD, OK_THRESHOLD

m_style = seaborn.color_palette("deep6")


def get_directories_in_current_folder(cur_dir=None):
    """Get sorted list of relevant directories in the current folder."""
    current_directory = os.getcwd() if cur_dir is None else cur_dir
    all_entries = os.listdir(current_directory)
    directories = []
    for entry in all_entries:
        full_path = os.path.join(current_directory, entry)
        if np.logical_and(os.path.isdir(full_path), np.logical_or(entry.startswith("GRB"), entry.startswith("Ep"))):
            if "Research" not in entry:
                directories.append(entry)
    directories.sort()
    return directories


def make_json_safe(obj):
    """Recursively convert an object to a JSON-serializable format."""
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
    """Deep merge dictionary u into dictionary d."""
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
    """Convert a covariance matrix to a correlation matrix."""
    cov = np.asarray(a=cov, dtype=float)
    d = np.sqrt(np.diag(cov))
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = cov / np.outer(a=d, b=d)
        corr[~np.isfinite(corr)] = 0.0  # handle 0/0 or inf cases
    return corr


def flatten_results(res_total, include_covariance=True):
    """Flatten nested results dictionary into a pandas DataFrame."""
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
                    rows.append(
                        {
                            "GRB": grb,
                            "epoch": ep,
                            "model": model,
                            "status": status,
                            "param": p_name,
                            "value": v,
                            "error": e,
                        }
                    )
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
                ax.hist(vals, bins=24, fc="w", ec="k", histtype="step")
                ax.set_xlim(means[i] - max_std * stds[i], means[i] + max_std * stds[i])
                m, s = np.mean(vals), np.std(vals)
                spec = "g" if abs(s) < 1 else "f"
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

                ax.scatter(samples[:, 0], samples[:, 1], s=1, color="k", alpha=0.3, zorder=1)
                for k, n_std in enumerate(n_stds[::-1]):
                    if n_std < max(n_stds):
                        width, height = 2 * n_std * np.sqrt(vals_)
                        ellipse = Ellipse(
                            xy=(float(means[j]), float(means[i])),
                            width=width,
                            height=height,
                            angle=theta,
                            ec="r" if k == 1 else "g",
                            fc="w",
                            lw=1.5,
                            zorder=2 + k,
                            ls="--" if k == 1 else "-.",
                        )
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

            ax.tick_params(axis="both", labelrotation=45)

    top, right = 0.96 if n_params > 4 else 0.94, 0.97

    fig.subplots_adjust(left=right * 0.1, bottom=top * 0.1, right=right, top=top, wspace=0.03, hspace=0.03)
    return fig, axes


def flattened_json(file_path="results.json"):
    """Load and flatten results from a JSON file."""
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


def two_scatter(
        start_list,
        end_list,
        val1,
        val2,
        err1,
        err2,
        ti_fmt="s",
        ti_color="r",
        tr_fmt="o",
        x_time=False,
        plot_axis=None,
        remove_extra=False,
):
    """Create a scatter plot comparing two sets of values with error bars."""
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
            alpha_ = 0.75 if alpha_mask else 1.0

        if err_bad:
            l_lim, u_lim = 1, 1
        elif err_warn:
            l_lim, u_lim = 0, 1
        else:
            l_lim, u_lim = 0, 0

        if remove_extra:
            if alpha_mask:
                continue

        plot_axis.errorbar(
            x=v1,
            y=v2,
            xerr=e1,
            yerr=e2,
            color=color_,
            fmt=fmt_,
            capsize=3,
            lolims=l_lim,
            uplims=u_lim,
            alpha=alpha_,
            label=f"{start_list[index]}_{end_list[index]}",
        )


def epoch_to_time(epochs, differences=False):
    """Convert epoch strings to numerical start and end times."""
    label, start, end = [], [], []
    for time_ in epochs:
        label.append(time_.split(" ")[0])
        ts_, te_ = map(float, time_.split(" ")[1].split("_"))
        start.append(ts_)
        end.append(te_)
    start, end = np.array(start), np.array(end)
    if differences:
        return {
            "episode_label": label,
            "start": start,
            "end": end,
            "difference": 0.5 * np.diff(a=[start, end], axis=0)[0],
            "midpoint": 0.5 * (start + end),
        }
    else:
        return label, start, end


def grb_characteristics(grb_df, model_name, epoch_difference=False):
    """Get characteristics of a GRB for a specific model."""
    unique_epochs = grb_df["epoch"].unique()
    model_n_par = model_n_pars[model_name.lower()]
    model_labels = MODEL_PARAMETERS[model_name.lower()]
    epoch = epoch_to_time(epochs=unique_epochs, differences=epoch_difference)

    return unique_epochs, model_n_par, model_labels, epoch


def break_e_to_e_peak(lambda1, lambda2, break_energy):
    f1 = (lambda1 + lambda2 + 4) / (lambda1 - lambda2)
    return break_energy * 10**(0.3 * unumpy.arctanh(f1))


def plot_per_episode(values, errors, m_name, start, end, difference, midpoints, axes):
    axes.plot([], [], ls='none', marker=None, label=f'GRB{m_name}')
    axes.plot([start[0], end[0]], [values[0], values[0]], c='k', ls='--', lw=2)
    axes.fill_between(x=[start[0], end[0]], y1=values[0] - errors[0], y2=values[0] + errors[0], color='k', alpha=0.15)
    for i, value in enumerate(midpoints[1:]):
        axes.errorbar(value, values[i + 1], xerr=difference[i + 1], yerr=errors[i + 1],
                      color='b' if np.logical_or(start[i + 1] < start[0],
                                                 end[i + 1] > end[0] + 0.064) else 'g', marker='.', ms=10, capsize=5)
