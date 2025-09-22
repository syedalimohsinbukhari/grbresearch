"""Created on Sep 22 11:33:50 2025"""

import os

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits

from src.grb_research import get_value, model_params, get_directories_in_current_folder

path_ = "/home/sarl-ws-5/PycharmProjects/GRBResearch/GRB110721200/"


def band_params(band_file, model_name, band_value='e_peak'):
    """Extract a specific parameter value and its error from a BAND-type fit model."""
    cov_ = band_file[2].data['COVARMAT'][0]
    val, err = get_value(fit_file=band_file, n_parameters=model_params[model_name], full_cov=cov_, return_errors=True)

    model_name = model_name.lower()

    # Lookup table: (band_value, model_type) -> index
    param_map = {'amplitude': {'band': 0, 'band_bb': 0, 'band_pl': 3, 'band_pl_bb': 3},
                 'e_peak': {'band': 1, 'band_bb': 1, 'band_pl': 4, 'band_pl_bb': 4},
                 'index1': {'band': 2, 'band_bb': 2, 'band_pl': 5, 'band_pl_bb': 5},
                 'index2': {'band': 3, 'band_bb': 3, 'band_pl': 6, 'band_pl_bb': 6},
                 }

    idx = param_map.get(band_value, {}).get(model_name)
    return (val[idx], err[idx]) if idx is not None else None


def cpl_params(band_file, model_name, band_value='e_peak'):
    """Extract a specific parameter value and its error from a CPL-type fit model."""
    cov_ = band_file[2].data['COVARMAT'][0]
    val, err = get_value(fit_file=band_file, n_parameters=model_params[model_name], full_cov=cov_, return_errors=True)

    model_name = model_name.lower()

    # Lookup table: (band_value, model_type) -> index
    param_map = {'amplitude': {'cpl': 0, 'cpl_bb': 0, 'cpl_pl': 3, 'cpl_pl_bb': 3},
                 'e_peak': {'cpl': 1, 'cpl_bb': 1, 'cpl_pl': 4, 'cpl_pl_bb': 4},
                 'index1': {'cpl': 2, 'cpl_bb': 2, 'cpl_pl': 5, 'cpl_pl_bb': 5},
                 }

    idx = param_map.get(band_value, {}).get(model_name)
    return (val[idx], err[idx]) if idx is not None else None


out_dir = get_directories_in_current_folder(path_)

band_e_peak = []

markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'h', '+', 'x']  # extend if needed

for i, out_ in enumerate(out_dir):
    intervals = []
    band_e_peak = []

    s, e = out_.split('__')[1].replace('m', '-').split('_')
    s, e = float(s), float(e)
    intervals.append((s, e))
    ff = [f for f in os.listdir(f'{path_}/{out_}') if f.endswith(".fit")]
    ff.sort()

    for file_ in ff:
        f_name = file_.split(".")[0].lower()
        f2 = fits.open(f'{path_}/{out_}/{file_}')
        cov = f2[2].data['COVARMAT'][0]
        if f_name == 'band':
            band_e_peak.append(band_params(band_file=f2, model_name=f_name, band_value='index2'))

        f2.close()

    band_e_peak = np.array(band_e_peak)
    intervals = np.array(intervals)

    x = intervals.mean(axis=1)
    x_err = (intervals[:, 1] - intervals[:, 0]) / 2
    plt.errorbar(
        x=x,
        xerr=x_err,
        y=band_e_peak[:, 0],
        yerr=band_e_peak[:, 1],
        ls='',
        marker='o',  # pick marker by directory index
        ms=5,
        capsize=5,
        label=out_.split('__')[1].replace('m', '-')
    )

plt.grid(True, ls='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()
