"""Created on Sep 20 12:48:54 2025"""

import os

import numpy as np
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

