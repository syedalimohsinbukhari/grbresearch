"""Created on Sep 20 15:07:35 2025"""

import os
from typing import Dict, List, Union

import numpy as np

from .grb_constants import ALLOWED_MODELS, MODEL_PARAMETERS, SINGLE_MODEL_FREE_PARAMS, SINGLE_MODEL_ORDER
from .grb_enums import GRBModelsCombinations
from .grb_enums import GRBModelsCombinations as gmC
from .grb_enums import normalize_model
from .grb_fits_io import (
    build_composite_schema,
    collect_model_cstat,
    get_extra_values,
    get_model_name_from_path,
    read_cstat_from_fit,
    read_param_values_errors,
)

# Re-export for backward compatibility
__all__ = [
    "ALLOWED_MODELS",
    "build_composite_schema",
    "collect_model_cstat",
    "compare_models",
    "compare_single_models",
    "complexity_key",
    "filter_models_by_error",
    "get_extra_values",
    "get_model_name_from_path",
    "list_par_err",
    "model_passes_error_criteria",
    "pick_best_in_group",
    "pick_best_model",
    "pick_best_single_model",
    "read_cstat_from_fit",
    "read_param_values_errors",
]


# ----------------- Utilities -----------------


def complexity_key(model_name: Union[str, GRBModelsCombinations]):
    """Get complexity sorting key for a model.

    Returns tuple of (base_model_order, total_free_params).

    Parameters
    ----------
    model_name : Union[str, GRBModelsCombinations]
        Model name as string or enum.

    Returns
    -------
    tuple
        (complexity_order, free_params) for sorting.
    """
    model = normalize_model(model_name)
    return model.complexity_order, model.free_params


# ----------------- Comparison Helpers -----------------


def _handle_nan_comparison(a: GRBModelsCombinations, b: GRBModelsCombinations, a_nan: bool, b_nan: bool) -> str:
    """Handle model comparison when one or both have NaN c-stat values.

    Parameters
    ----------
    a, b : GRBModelsCombinations
        Models to compare.
    a_nan, b_nan : bool
        Whether each model has NaN c-stat.

    Returns
    -------
    str
        Name of the better model (uppercase).
    """
    if a_nan and not b_nan:
        return b.name_upper
    if b_nan and not a_nan:
        return a.name_upper
    # Both NaN - choose simpler
    return min([a, b], key=lambda m: m.complexity_order).name_upper


def _compare_equal_complexity(
    a: GRBModelsCombinations, b: GRBModelsCombinations, a_cstat: float, b_cstat: float
) -> str:
    """Compare models with equal number of free parameters.

    Parameters
    ----------
    a, b : GRBModelsCombinations
        Models to compare.
    a_cstat, b_cstat : float
        C-statistic values.

    Returns
    -------
    str
        Name of the better model (uppercase).
    """
    if a_cstat == b_cstat:
        return min([a, b], key=lambda m: (m.complexity_order, m.free_params)).name_upper
    return a.name_upper if a_cstat < b_cstat else b.name_upper


def _compare_different_complexity(
    a: GRBModelsCombinations,
    b: GRBModelsCombinations,
    a_free: int,
    b_free: int,
    a_cstat: float,
    b_cstat: float,
    is_separate_group: int = 0,
) -> str:
    """Compare models with different complexity using improvement threshold.

    Parameters
    ----------
    a, b : GRBModelsCombinations
        Models to compare.
    a_free, b_free : int
        Number of free parameters.
    a_cstat, b_cstat : float
        C-statistic values.

    Returns
    -------
    str
        Name of the better model (uppercase).
    """
    if a_free < b_free:
        simple, simple_c, simple_f = a, a_cstat, a_free
        complex_, complex_c, complex_f = b, b_cstat, b_free
    else:
        simple, simple_c, simple_f = b, b_cstat, b_free
        complex_, complex_c, complex_f = a, a_cstat, a_free

    required = 9 * (complex_f - simple_f) if is_separate_group == 0 else 28.74 if is_separate_group == 1 else 36.86
    improvement = simple_c - complex_c
    return complex_.name_upper if improvement >= required else simple.name_upper


# ----------------- Comparison -----------------


def compare_models(
    a_model: Union[str, GRBModelsCombinations],
    a_cstat: float,
    b_model: Union[str, GRBModelsCombinations],
    b_cstat: float,
    single_only: bool = False,
    is_separate_group: int = 0,
) -> str:
    """Compare two models and return the better one based on c-stat and complexity.

    Parameters
    ----------
    a_model : Union[str, GRBModelsCombinations]
        Name of the first model (string or enum).
    a_cstat : float
        C-statistic of first model.
    b_model : Union[str, GRBModelsCombinations]
        Name of second model (string or enum).
    b_cstat : float
        C-statistic of second model.
    single_only : bool, optional
        If True, only allow comparison of single models (PL/CPL/BAND/SBPL).

    Returns
    -------
    str
        Name of the better model (uppercase string).
    """
    # Convert to enums for internal processing
    a = normalize_model(a_model)
    b = normalize_model(b_model)

    # Validate single_only constraint
    single_models = {
        GRBModelsCombinations.PL,
        GRBModelsCombinations.CPL,
        GRBModelsCombinations.BAND,
        GRBModelsCombinations.SBPL,
    }
    if single_only and (a not in single_models or b not in single_models):
        raise ValueError("Single-model comparison requires PL/CPL/BAND/SBPL")

    a_free, b_free = a.free_params, b.free_params
    a_nan, b_nan = np.isnan(a_cstat), np.isnan(b_cstat)

    # Handle NaN cases
    if a_nan or b_nan:
        return _handle_nan_comparison(a, b, a_nan, b_nan)

    # Handle equal complexity
    if a_free == b_free:
        return _compare_equal_complexity(a, b, a_cstat, b_cstat)

    # Handle different complexity with the improvement threshold
    return _compare_different_complexity(a, b, a_free, b_free, a_cstat, b_cstat, is_separate_group)


def compare_single_models(
    a_model: Union[str, GRBModelsCombinations],
    a_cstat: float,
    b_model: Union[str, GRBModelsCombinations],
    b_cstat: float,
) -> str:
    """Compare only single models (PL, CPL, BAND, SBPL).

    Parameters
    ----------
    a_model, b_model : Union[str, GRBModelsCombinations]
        Model names or enums (must be single models).
    a_cstat, b_cstat : float
        C-statistic values.

    Returns
    -------
    str
        Name of the better model (uppercase string).
    """
    return compare_models(a_model=a_model, a_cstat=a_cstat, b_model=b_model, b_cstat=b_cstat, single_only=True)


# ----------------- Error Criteria -----------------


def model_passes_error_criteria(path, par_constraint=0.4):
    model = get_model_name_from_path(path)
    try:
        schema = build_composite_schema(model)
        vals, errs = read_param_values_errors(path=path, n_parameters=len(schema))
    except Exception:
        return False
    elevated_constraint = 0
    for (p_name, _, _), v, e in zip(schema, vals, errs):
        limit = par_constraint * abs(v)
        if abs(v) == 0 and abs(e) != 0:
            return False
        if abs(v) != 0 and abs(e) >= limit:
            return False
        if abs(v) != 0 and np.logical_and(0.4 * abs(v) < abs(e), abs(e) < par_constraint * abs(v)):
            elevated_constraint += 1
    return True if elevated_constraint <= 1 else False


# ----------------- Filtering & Picking -----------------


def filter_models_by_error(c_stats, folder_path, candidates, **kwargs):
    return {
        m: c_stats[m]
        for m in candidates
        if m in c_stats
           and os.path.exists(os.path.join(folder_path, f"{m}.fit"))
           and model_passes_error_criteria(path=os.path.join(folder_path, f"{m}.fit"), **kwargs)
    }


def pick_best_in_group(c_stats, candidates, group_name, is_separate_group=0):
    present = [m for m in candidates if m in c_stats]
    if not present:
        raise ValueError(f"No {group_name} models found")
    present.sort(key=complexity_key)
    best, best_c = present[0], c_stats[present[0]]
    for m in present[1:]:
        best = compare_models(
            a_model=best, a_cstat=best_c, b_model=m, b_cstat=c_stats[m], is_separate_group=is_separate_group
        )
        best_c = c_stats[best]
    return best, best_c


def pick_best_model(c_stats, candidates, group_name, folder_path=None, is_separate_group=0, **kwargs):
    if folder_path:
        c_stats = filter_models_by_error(c_stats=c_stats, folder_path=folder_path, candidates=candidates, **kwargs)
        if not c_stats:
            raise ValueError(f"No {group_name} models passed error criteria")
    return pick_best_in_group(
        c_stats=c_stats, candidates=candidates, group_name=group_name, is_separate_group=is_separate_group
    )


def pick_best_single_model(c_stats: Dict[str, float]):
    singles = {k.upper(): v for k, v in c_stats.items() if k.upper() in SINGLE_MODEL_FREE_PARAMS}
    if not singles:
        raise ValueError("No single models in cstats")
    available = sorted(singles.keys(), key=lambda kp: (SINGLE_MODEL_ORDER[kp], SINGLE_MODEL_FREE_PARAMS[kp]))
    best, best_c = available[0], singles[available[0]]
    for m in available[1:]:
        best = compare_single_models(a_model=best, a_cstat=best_c, b_model=m, b_cstat=singles[m])
        best_c = singles[best]
    return best, best_c


# ----------------- Parameter Error Listing Helpers -----------------


def _extract_model_data(fit_path, schema_len):
    """Extract all model data from a FITS file.

    Returns
    -------
    tuple
        (schema, vals, errs, flux_data, cstat, dof, cov_matrix)
    """
    schema = build_composite_schema(os.path.splitext(os.path.basename(fit_path))[0])
    vals, errs = read_param_values_errors(path=fit_path, n_parameters=schema_len)

    (
        (ph_flx_v, ph_flx_e),
        (ph_fluence_v, ph_fluence_e),
        (en_flx_v, en_flx_e),
        (en_fluence_v, en_fluence_e),
        cov_matrix,
    ) = get_extra_values(path=fit_path)

    c_stat, dof = read_cstat_from_fit(path=fit_path)

    flux_data = {
        "names": ["c-stat/dof", "photon_flux", "photon_fluence", "energy_flux", "energy_fluence"],
        "values": [c_stat, ph_flx_v, ph_fluence_v, en_flx_v, en_fluence_v],
        "errors": [dof, ph_flx_e, ph_fluence_e, en_flx_e, en_fluence_e],
    }

    return schema, vals, errs, flux_data, c_stat, dof, cov_matrix


def _store_model_results(result_dict, grb, ep_ext, ep, model, status, vals, errs, cstat, dof, cov, model_params):
    """Store model results in the result dictionary.

    Parameters
    ----------
    result_dict : dict
        Dictionary to store results.
    grb : str
        GRB name.
    ep_ext : str
        Episode extension label.
    ep : str
        Episode identifier.
    model : str
        Model name.
    status : str
        Model status.
    vals : numpy.ndarray
        Parameter values.
    errs : numpy.ndarray
        Parameter errors.
    cstat : float
        C-statistic value.
    dof : float
        Degrees of freedom.
    cov : numpy.ndarray
        Covariance matrix.
    model_params : list
        List of parameter names.
    """
    model_dict = result_dict.setdefault(grb, {}).setdefault(f"{ep_ext} {ep}", {}).setdefault(model, {})
    model_dict["_status"] = status

    # Store parameters
    for param_name, v, e in zip(model_params, vals, errs):
        model_dict[param_name] = [v, e]

    model_dict["c-stat/dof"] = [cstat, dof]
    model_dict["covariance_matrix"] = cov


def _print_parameter_details(status_str, model, schema, vals, errs, flux_data):
    """Print parameter details to console.

    Parameters
    ----------
    status_str : str
        Status string (SAFE/UNSAFE/BEST).
    model : str
        Model name.
    schema : list
        Parameter schema.
    vals : numpy.ndarray
        Parameter values.
    errs : numpy.ndarray
        Parameter errors.
    flux_data : dict
        Dictionary with flux/fluence data.
    """
    print(f"[{status_str}] {model} parameter details:")

    # Print model parameters
    for (par_name, _, _), v, e in zip(schema, vals, errs):
        pct = (abs(e) / abs(v) * 100) if v != 0 else float("inf")
        print(f"   {par_name:15s} = {v:.20f}({e:.20f}) , {pct:.3g} %")

    # Print flux/fluence data
    for par_name, v, e in zip(flux_data["names"], flux_data["values"], flux_data["errors"]):
        acc = "4" if par_name == "c-stat/dof" else "20"
        sep1 = "/" if par_name == "c-stat/dof" else "("
        sep2 = "" if par_name == "c-stat/dof" else ")"
        print(f"   {par_name:15s} = {v:.{acc}f}{sep1}{e:.{acc}f}{sep2}")


def list_par_err(cwd_, fit_type, string: str = "SAFE", result_dict=None, ep_ext="T90") -> Dict:
    """List parameter errors for given models in the specified directory.

    Parameters
    ----------
    cwd_ : str
        Current working directory containing the fit files.
    fit_type : List[str]
        List of model names to process.
    string : int, optional
        Indicator for SAFE (1) or UNSAFE (0) models. Default is 1.
    is_good : dict, optional
        Dictionary of GOOD models for hierarchy analysis. Default is None.
    result_dict : dict, optional
        Dictionary to store results. Default is None.
    ep_ext : str, optional
        Extension label for the episode. Default is 'T90'.

    Returns
    -------
    dict
        Updated result dictionary with parameter details.
    """
    if result_dict is None:
        result_dict = {}

    # Extract GRB and episode info from the path
    grb = cwd_.split("/")[-2]
    ep = cwd_.split("/")[-1].split("__")[1].replace("m", "-")

    # Process each model
    for model in fit_type:
        fit_path = os.path.join(cwd_, f"{model}.fit")
        if not os.path.exists(fit_path):
            continue

        try:
            # Extract all model data
            schema, vals, errs, flux_data, c_stat, dof, cov_matrix = _extract_model_data(
                fit_path, len(build_composite_schema(model))
            )

            # Store results
            _store_model_results(
                result_dict,
                grb,
                ep_ext,
                ep,
                model,
                string,
                vals,
                errs,
                c_stat,
                dof,
                cov_matrix,
                MODEL_PARAMETERS[gmC(model.lower())],
            )

            # Print details
            _print_parameter_details(string, model, schema, vals, errs, flux_data)

        except Exception as e:
            print(f"[{string}] {model}: failed to read params ({e})")

    return result_dict
