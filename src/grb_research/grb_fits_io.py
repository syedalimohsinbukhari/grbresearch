"""FITS file I/O operations for GRB spectral model analysis.

This module provides functions for reading GRB spectral model fit results from FITS files.
It is designed to work with FITS files containing spectral fit outputs with specific HDU structure:

HDU[2] contains:
    - PARAM{i}: Parameter values and errors for i-th parameter
    - CHSQDOF: Chi-squared degrees of freedom
    - REDCHSQ: Reduced chi-squared values
    - COVARMAT: Covariance matrix
    - PHTFLUX, PHTFLNC: Photon flux and fluence
    - NRGFLUX, NRGFLNC: Energy flux and fluence

This module is part of the model selection pipeline and is primarily used by safe_good_best.py.

Created on Feb 12 2026
"""

import os
from typing import Dict, Iterable, List

import numpy as np
from astropy.io import fits

from .grb_constants import BASE_PARAM_SCHEMAS, COMPONENT_PARAM_SCHEMAS

__all__ = [
    "get_model_name_from_path",
    "read_cstat_from_fit",
    "collect_model_cstat",
    "read_param_values_errors",
    "get_extra_values",
    "build_composite_schema",
]


def build_composite_schema(model_name: str):
    """Build parameter schema for a composite model.

    Parameters
    ----------
    model_name : str
        Name of the model (e.g., 'CPL_PL_BB').

    Returns
    -------
    list
        List of tuples (param_name, is_fixed, has_bounds) defining the parameter schema.

    Raises
    ------
    ValueError
        If the base model is not recognized.
    """
    parts = model_name.upper().split("_")
    base = parts[0]
    if base not in BASE_PARAM_SCHEMAS:
        raise ValueError(f"Unknown base model: {model_name}")
    schema = []
    if base == "PL":
        schema.extend(BASE_PARAM_SCHEMAS["PL"])
    elif "PL" in parts[1:]:
        schema.extend(COMPONENT_PARAM_SCHEMAS["PL"])
    if base != "PL":
        schema.extend(BASE_PARAM_SCHEMAS[base])
    if "BB" in parts[1:]:
        schema.extend(COMPONENT_PARAM_SCHEMAS["BB"])
    return schema


def get_model_name_from_path(path: str) -> str:
    """Extract model name from FITS file path.

    Parameters
    ----------
    path : str
        Path to the FITS file.

    Returns
    -------
    str
        Model name in uppercase (e.g., 'CPL_BB').
    """
    return os.path.splitext(os.path.basename(path))[0].upper()


def read_cstat_from_fit(path: str, give_covariance=False):
    """Read C-statistic and degrees of freedom from a FITS file.

    Parameters
    ----------
    path : str
        Path to the FITS file.
    give_covariance : bool, optional
        If True, also return the covariance matrix. Default is False.

    Returns
    -------
    float
        C-statistic value.
    float
        Degrees of freedom.
    numpy.ndarray, optional
        Covariance matrix (only if give_covariance=True).
    """
    with fits.open(path) as ff:
        dof = ff[2].data["CHSQDOF"][0]
        cstat = float(ff[2].data["REDCHSQ"][0][1] * dof)
        if not give_covariance:
            return cstat, dof
        cov = ff[2].data["COVARMAT"][0]
        return cstat, dof, cov


def collect_model_cstat(paths: Iterable[str]) -> Dict[str, List[float]]:
    """Collect C-statistics and DOF from multiple FITS files.

    Parameters
    ----------
    paths : Iterable[str]
        Paths to FITS files.

    Returns
    -------
    dict
        Dictionary mapping model names to [cstat, dof] lists.
    """
    result = {}
    for p in paths:
        model = get_model_name_from_path(p)
        cstat, dof = read_cstat_from_fit(p)
        result[model] = [cstat, dof]
    return result


def read_param_values_errors(path: str, n_parameters=None):
    """Read parameter values and their corresponding errors from a FITS file.

    Parameters
    ----------
    path : str
        Path to the FITS file to be read.
    n_parameters : int, optional
        Number of parameters to extract. If ``None`` (default), the number is
        inferred from the composite schema derived from the model name in the
        FITS file name.

    Returns
    -------
    tuple of (numpy.ndarray, numpy.ndarray)
        A tuple ``(values, errors)`` where both are 1-D ``numpy.ndarray`` objects
        of length ``n_parameters``.

    Raises
    ------
    ValueError
        If the model name cannot be mapped to a known schema when ``n_parameters`` is not provided.
    OSError
        If the FITS file cannot be opened.
    """
    model = get_model_name_from_path(path)
    if n_parameters is None:
        schema = build_composite_schema(model)
        n_parameters = len(schema)
    with fits.open(path) as ff:
        vals = [ff[2].data[f"PARAM{i}"][0][0] for i in range(n_parameters)]
        errs = [ff[2].data[f"PARAM{i}"][0][1] for i in range(n_parameters)]
        return np.array(object=vals, dtype=float), np.array(object=errs, dtype=float)


def get_extra_values(path):
    """Extract flux, fluence, and covariance matrix from FITS file.

    Parameters
    ----------
    path : str
        Path to the FITS file.

    Returns
    -------
    tuple
        (photon_flux, photon_fluence, energy_flux, energy_fluence, covariance_matrix)
        Each flux/fluence is a tuple of (value, error).
    """
    ff = fits.open(path)
    try:
        ff2 = ff[2].data
        ph_flx, ph_fln = ff2["PHTFLUX"][0], ff2["PHTFLNC"][0]
        en_flx, en_fln = ff2["NRGFLUX"][0], ff2["NRGFLNC"][0]
        cov_ = ff2["COVARMAT"][0]
    finally:
        ff.close()

    return ph_flx, ph_fln, en_flx, en_fln, cov_
