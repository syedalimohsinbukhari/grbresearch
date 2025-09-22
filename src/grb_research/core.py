"""Created on Sep 20 12:48:54 2025"""

import os

import numpy as np
import pandas as pd
from uncertainties import correlated_values

model_params = {"pl": 3,
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


def flatten_results(res_total):
    rows = []
    for grb, epochs in res_total.items():
        for ep, models in epochs.items():
            for model, params in models.items():
                status = params.get("_status", "NA")
                for pname, val in params.items():
                    if pname == "_status":
                        continue
                    v, e = val  # because JSON list [value, error]
                    rows.append({
                        "GRB": grb,
                        "epoch": ep,
                        "model": model,
                        "status": status,
                        "param": pname,
                        "value": v,
                        "error": e,
                    })
    return pd.DataFrame(rows)
