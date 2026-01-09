"""Created on Sep 20 15:07:35 2025"""

import os
from typing import Dict, Iterable, List

import numpy as np
from astropy.io import fits

from .grb_constants import MODEL_PARAMETERS
from .flags import analyze_model_hierarchy

BASE_PARAM_SCHEMAS = {
    "PL": [("amplitude", False, False), ("e_pivot", True, False), ("index1", False, False)],
    "CPL": [
        ("amplitude", False, False),
        ("peak_energy", False, False),
        ("index1", False, False),
        ("e_pivot", True, False),
    ],
    "BAND": [
        ("amplitude", False, False),
        ("peak_energy", False, False),
        ("index1", False, False),
        ("index2", False, False),
    ],
    "SBPL": [
        ("amplitude", False, False),
        ("e_pivot", True, False),
        ("index1", False, False),
        ("break_energy", False, False),
        ("delta", True, False),
        ("index2", False, False),
    ],
}

COMPONENT_PARAM_SCHEMAS = {
    "PL": [("amplitude_pl", False, False), ("e_pivot_pl", True, False), ("index2_pl", False, False)],
    "BB": [("amplitude_bb", False, False), ("kt_temperature", False, False)],
}

ALLOWED_MODELS = {
    "PL",
    "CPL",
    "BAND",
    "SBPL",
    "PL_BB",
    "CPL_BB",
    "CPL_PL",
    "CPL_PL_BB",
    "BAND_BB",
    "BAND_PL",
    "BAND_PL_BB",
    "SBPL_BB",
    "SBPL_PL",
    "SBPL_PL_BB",
}

SINGLE_MODEL_FREE_PARAMS = {"PL": 2, "CPL": 3, "BAND": 4, "SBPL": 4}
SINGLE_MODEL_ORDER = {"PL": 0, "CPL": 1, "BAND": 2, "SBPL": 2}
COMPONENT_FREE_PARAMS = {"PL": 2, "BB": 2}


# ----------------- Utilities -----------------


def build_composite_schema(model_name: str):
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


def compute_free_params(model_name: str) -> int:
    parts = model_name.upper().split("_")
    base, comps = parts[0], parts[1:]
    total = SINGLE_MODEL_FREE_PARAMS.get(base, 0)
    for comp in comps:
        total += COMPONENT_FREE_PARAMS.get(comp, 0)
    return total


def complexity_key(model_name: str):
    base = model_name.upper().split("_")[0]
    return SINGLE_MODEL_ORDER.get(base, 99), compute_free_params(model_name)


# ----------------- FITS Access -----------------


def get_model_name_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0].upper()


def read_cstat_from_fit(path: str, give_covariance=False):
    ff = fits.open(path)
    try:
        dof = ff[2].data["CHSQDOF"][0]
        cstat = float(ff[2].data["REDCHSQ"][0][1] * dof)
        if not give_covariance:
            return cstat, dof
        else:
            return cstat, dof, ff[2].data["COVARMAT"][0]
    finally:
        ff.close()


def collect_model_cstat(paths: Iterable[str]) -> Dict[str, List[float]]:
    result = {}
    for p in paths:
        model = get_model_name_from_path(p)
        try:
            cstat, dof = read_cstat_from_fit(p)
            result[model] = [cstat, dof]
        except Exception:
            result[model] = [float("nan"), float("nan")]
    return result


def read_param_values_errors(path: str, n_parameters=None):
    model = get_model_name_from_path(path)
    if n_parameters is None:
        schema = build_composite_schema(model)
        n_parameters = len(schema)
    ff = fits.open(path)
    try:
        vals = [ff[2].data[f"PARAM{i}"][0][0] for i in range(n_parameters)]
        errs = [ff[2].data[f"PARAM{i}"][0][1] for i in range(n_parameters)]
        return np.array(object=vals, dtype=float), np.array(object=errs, dtype=float)
    finally:
        ff.close()


# ----------------- Comparison -----------------


def compare_models(a_model, a_cstat, b_model, b_cstat, single_only=False):
    a, b = a_model.upper(), b_model.upper()
    if single_only and (a not in SINGLE_MODEL_FREE_PARAMS or b not in SINGLE_MODEL_FREE_PARAMS):
        raise ValueError("Single-model comparison requires PL/CPL/BAND/SBPL")
    a_free, b_free = compute_free_params(a), compute_free_params(b)
    a_nan, b_nan = np.isnan(a_cstat), np.isnan(b_cstat)
    if a_nan or b_nan:
        if a_nan and not b_nan:
            return b
        if b_nan and not a_nan:
            return a
        return min([a, b], key=lambda m: SINGLE_MODEL_ORDER.get(m.split("_")[0], 99))
    if a_free == b_free:
        if a_cstat == b_cstat:
            return min([a, b], key=complexity_key)
        return a if a_cstat < b_cstat else b
    simple, simple_c, simple_f, complex_, complex_c, complex_f = (
        (a, a_cstat, a_free, b, b_cstat, b_free) if a_free < b_free else (b, b_cstat, b_free, a, a_cstat, a_free)
    )
    required = 9 * (complex_f - simple_f)
    improvement = simple_c - complex_c
    return complex_ if improvement >= required else simple


def compare_single_models(a_model, a_cstat, b_model, b_cstat):
    """Compare only single models (PL, CPL, BAND, SBPL)."""
    return compare_models(a_model=a_model, a_cstat=a_cstat, b_model=b_model, b_cstat=b_cstat, single_only=True)


# ----------------- Error Criteria -----------------


def _param_error_limit(model, pname, v, par_constraint, loose):
    parameter_name = pname.lower()
    base = model.split("_")[0]
    if parameter_name == "index2" and base in ("BAND", "SBPL"):
        factor = 1.0 if loose else 0.7
        return factor * abs(v), f"loose_index2({factor})"
    if parameter_name == "index2_pl" and "PL" in model.split("_")[1:]:
        factor = 1.0 if loose else 0.7
        return factor * abs(v), f"loose_pl_index({factor})"
    return par_constraint * abs(v), f"default({par_constraint})"


def model_passes_error_criteria(path, par_constraint=0.4, loose_criteria=True):
    model = get_model_name_from_path(path)
    try:
        schema = build_composite_schema(model)
        vals, errs = read_param_values_errors(path=path, n_parameters=len(schema))
    except Exception:
        return False
    for (p_name, _, _), v, e in zip(schema, vals, errs):
        limit, _ = _param_error_limit(
            model=model, pname=p_name, v=v, par_constraint=par_constraint, loose=loose_criteria
        )
        if abs(v) == 0 and abs(e) != 0:
            return False
        if abs(v) != 0 and abs(e) >= limit:
            return False
    return True


# ----------------- Filtering & Picking -----------------


def filter_models_by_error(c_stats, folder_path, candidates, **kwargs):
    return {
        m: c_stats[m]
        for m in candidates
        if m in c_stats
        and os.path.exists(os.path.join(folder_path, f"{m}.fit"))
        and model_passes_error_criteria(path=os.path.join(folder_path, f"{m}.fit"), **kwargs)
    }


def pick_best_in_group(c_stats, candidates, group_name):
    present = [m for m in candidates if m in c_stats]
    if not present:
        raise ValueError(f"No {group_name} models found")
    present.sort(key=complexity_key)
    best, best_c = present[0], c_stats[present[0]]
    for m in present[1:]:
        best = compare_models(a_model=best, a_cstat=best_c, b_model=m, b_cstat=c_stats[m])
        best_c = c_stats[best]
    return best, best_c


def pick_best_model(c_stats, candidates, group_name, folder_path=None, **kwargs):
    if folder_path:
        c_stats = filter_models_by_error(c_stats=c_stats, folder_path=folder_path, candidates=candidates, **kwargs)
        if not c_stats:
            raise ValueError(f"No {group_name} models passed error criteria")
    return pick_best_in_group(c_stats=c_stats, candidates=candidates, group_name=group_name)


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


# ----------------- SAFE / GOOD / BEST -----------------


def list_safe_models(folder_path, **kwargs):
    return {
        m
        for m in ALLOWED_MODELS
        if os.path.exists(os.path.join(folder_path, f"{m}.fit"))
        and model_passes_error_criteria(os.path.join(folder_path, f"{m}.fit"), **kwargs)
    }


def compute_good_models(c_stats, folder_path, **kwargs):
    good = {}
    base = filter_models_by_error(
        c_stats=c_stats, folder_path=folder_path, candidates=["PL", "CPL", "BAND", "SBPL"], **kwargs
    )
    if base:
        good["BASE"] = pick_best_single_model(base)
    for group, candidates in {
        "+BB": ["PL_BB", "CPL_BB", "BAND_BB", "SBPL_BB"],
        "+PL": ["CPL_PL", "BAND_PL", "SBPL_PL"],
        "+PL+BB": ["CPL_PL_BB", "BAND_PL_BB", "SBPL_PL_BB"],
    }.items():
        try:
            good[group.strip("+")] = pick_best_model(
                c_stats=c_stats, candidates=candidates, group_name=group, folder_path=folder_path, **kwargs
            )
        except Exception:
            pass
    return good


def get_extra_values(path):
    ff = fits.open(path)
    try:
        ff2 = ff[2].data
        ph_flx, ph_fln = ff2["PHTFLUX"][0], ff2["PHTFLNC"][0]
        en_flx, en_fln = ff2["NRGFLUX"][0], ff2["NRGFLNC"][0]
        cov_ = ff2["COVARMAT"][0]
    finally:
        ff.close()

    return ph_flx, ph_fln, en_flx, en_fln, cov_


def list_par_err(cwd_, fit_type, string=1, is_good=None, result_dict=None, ep_ext="T90") -> Dict:
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

    result = {}

    if is_good:
        result = analyze_model_hierarchy(is_good)

    grb = cwd_.split("/")[-2]
    ep = cwd_.split("/")[-1].split("__")[1].replace("m", "-")

    s_ = "SAFE" if string == 1 else "UNSAFE"

    for m in fit_type:
        fit_path = os.path.join(cwd_, f"{m}.fit")
        if not os.path.exists(fit_path):
            continue
        try:
            schema = build_composite_schema(m)
            vals, errs = read_param_values_errors(path=fit_path, n_parameters=len(schema))
            (
                (ph_flx_v, ph_flx_e),
                (ph_fluence_v, ph_fluence_e),
                (en_flx_v, en_flx_e),
                (en_fluence_v, en_fluence_e),
                cov_matrix,
            ) = get_extra_values(path=fit_path)

            c_stat, dof = read_cstat_from_fit(path=fit_path)

            p_name2 = ["c-stat/dof", "photon_flux", "photon_fluence", "energy_flux", "energy_fluence"]
            vals2 = [c_stat, ph_flx_v, ph_fluence_v, en_flx_v, en_fluence_v]
            errs2 = [dof, ph_flx_e, ph_fluence_e, en_flx_e, en_fluence_e]

            model_dict = result_dict.setdefault(grb, {}).setdefault(f"{ep_ext} {ep}", {}).setdefault(m, {})
            model_dict["_status"] = s_
            if m in list(result.keys()):
                if result[m] == 1:
                    model_dict["_status"] = "BEST"

            # store parameters
            for m2, v, e in zip(MODEL_PARAMETERS[m.lower()], vals, errs):
                model_dict[m2] = [v, e]

            model_dict["c-stat/dof"] = [c_stat, dof]
            model_dict["covariance_matrix"] = cov_matrix

            # print log
            print(f"[{s_}] {m} parameter details:")
            for (par_name, _, _), v, e in zip(schema, vals, errs):
                pct = (abs(e) / abs(v) * 100) if v != 0 else float("inf")
                print(f"   {par_name:15s} = {v:.20f}({e:.20f}) , {pct:.3g} %")
            for par_name, v, e in zip(p_name2, vals2, errs2):
                acc = "4" if par_name == "c-stat/dof" else "20"
                sep1 = "/" if par_name == "c-stat/dof" else "("
                sep2 = "" if par_name == "c-stat/dof" else ")"
                print(f"   {par_name:15s} = {v:.{acc}f}{sep1}{e:.{acc}f}{sep2}")

        except Exception as e:
            print(f"[{string}] {m}: failed to read params ({e})")

    return result_dict
