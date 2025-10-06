"""Created on Sep 11 16:25:54 2025"""

import os
from typing import Optional

import numpy as np
import pandas as pd
from astropy.io import fits
from numpy.typing import NDArray
from uncertainties import correlated_values
from uncertainties.unumpy import nominal_values, std_devs

from .core import model_n_pars

## TODO:
# for each episode, collect the parameters +/- errors
# prepare a nice csv or something and than latex table,

pl_params = ["amp_pl", "e_piv_pl", "index1_pl"]
band_params = ["amp_band", "e_peak_band", "index1_band", "index2_band"]
sbpl_params = [
    "amp_sbpl",
    "e_piv_sbpl",
    "index1_sbpl",
    "e_break_sbpl",
    "delta_sbpl",
    "index2_sbpl",
]
cpl_params = ["amp_cpl", "e_peak_cpl", "index1_cpl", "e_piv_cpl"]
bb_params = ["amp_bb", "kt_bb"]

pl_bb_params = pl_params + bb_params

cpl_pl_params = cpl_params + pl_params
cpl_bb_params = cpl_params + bb_params
cpL_pl_bb_params = cpl_params + pl_params + bb_params

band_pl_params = band_params + pl_params
band_bb_params = band_params + bb_params
band_pl_bb_params = band_params + pl_params + bb_params

sbpl_pl_params = sbpl_params + pl_params
sbpl_bb_params = sbpl_params + bb_params
sbpl_pl_bb_params = sbpl_params + pl_params + bb_params

parma_names = {
    "pl": pl_params,
    "pl_bb": pl_bb_params,
    "cpl": cpl_params,
    "cpl_pl": cpl_pl_params,
    "cpl_bb": cpl_bb_params,
    "cpl_pl_bb": cpL_pl_bb_params,
    "band": band_params,
    "band_pl": band_pl_params,
    "band_bb": band_bb_params,
    "band_pl_bb": band_pl_bb_params,
    "sbpl": sbpl_params,
    "sbpl_pl": sbpl_pl_params,
    "sbpl_bb": sbpl_bb_params,
    "sbpl_pl_bb": sbpl_pl_bb_params,
}

cwd_ = os.getcwd()
dir_ = [
    "Ep0_Model_Data",
    "Ep1_Model_Data",
    "Ep2_Model_Data",
    "Ep3_Model_Data",
    "Ep4_Model_Data",
    "Ep5_Model_Data",
]
files_ = [f for f in os.listdir(f"./{dir_[0]}") if f.endswith(".fit")]
files_.sort()


def get_value(fit_file, n_parameters, full_cov, return_errors: bool = False):
    """
    Extract parameter values (and optionally errors) from the FITS file.

    - Value is stored at [0][0]
    - Error is stored at [0][1]

    If return_errors is False (default), returns a list of uncertainties.ufloat via
    correlated_values using full covariance. This preserves error correlations in
    downstream computations.

    If return_errors is True, returns a tuple (values, errors) where both are numpy arrays
    taken directly from the FITS (per-parameter 1-sigma errors), with 0.0 for frozen parameters.
    """
    values = [fit_file[2].data[f"PARAM{i}"][0][0] for i in range(n_parameters)]
    errors = [fit_file[2].data[f"PARAM{i}"][0][1] for i in range(n_parameters)]

    if return_errors:
        return (
            np.array(object=values, dtype=float),
            np.array(object=errors, dtype=float),
        )

    return correlated_values(nom_values=values, covariance_mat=full_cov)


def save_model(
    values: NDArray, model_name: str, ret: bool = False
) -> Optional[pd.DataFrame]:
    df_ = pd.DataFrame(values).T
    df_.columns = parma_names[model_name]

    # expand uncertainties columns into value + error
    expanded = {}
    for col in df_.columns:
        series = df_[col]
        expanded[col + "_val"] = nominal_values(series)
        expanded[col + "_err"] = std_devs(series)
        # expanded[col + "_rel_err"] = str((expanded[col + "_err"] / np.abs(expanded[col + "_val"]))[0] * 100) + ' %'

    df_clean = pd.DataFrame(expanded).T.reset_index()
    df_clean.columns = ["par_name", "par_value"]

    if not ret:
        df_clean.to_csv(
            path_or_buf=f"./{dir_[0]}/{model_name}.csv",
            index=False,
            float_format="%.17g",
        )
        return None
    else:
        return df_clean


for fit_ in files_:
    model_ = fit_.split(".fit")[0].lower()
    with fits.open(f"{cwd_}/{dir_[0]}/{fit_}") as f:
        print(fit_.split(".fit")[0].lower())
        v = get_value(
            fit_file=f,
            n_parameters=model_n_pars[model_],
            full_cov=f[2].data["COVARMAT"][0],
        )
        if model_ == "pl_bb":
            save_model(values=v, model_name=model_)
