"""Created on Sep 20 15:07:35 2025"""

import os
from typing import Iterable, Dict, List

import numpy as np
from astropy.io import fits

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

BASE_PARAM_SCHEMAS = {
    "PL": [("amplitude", False, False), ("e_pivot", True, False), ("index", False, False)],
    "CPL": [("amplitude", False, False), ("peak_energy", False, False), ("index", False, False),
            ("e_pivot", True, False)],
    "BAND": [("amplitude", False, False), ("peak_energy", False, False), ("index1", False, False),
             ("index2", False, False)],
    "SBPL": [("amplitude", False, False), ("e_pivot", True, False), ("index1", False, False),
             ("break_energy", False, False), ("delta", True, False), ("index2", False, False)],
}

COMPONENT_PARAM_SCHEMAS = {
    "PL": [("amplitude_pl", False, False), ("e_pivot_pl", True, False), ("index_pl", False, False)],
    "BB": [("amplitude_bb", False, False), ("kt_temperature", False, False)],
}

ALLOWED_MODELS = {
    "PL", "CPL", "BAND", "SBPL",
    "PL_BB", "CPL_BB", "CPL_PL", "CPL_PL_BB",
    "BAND_BB", "BAND_PL", "BAND_PL_BB",
    "SBPL_BB", "SBPL_PL", "SBPL_PL_BB",
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


def read_cstat_from_fit(path: str):
    ff = fits.open(path)
    try:
        return float(ff[2].data["REDCHSQ"][0][1] * ff[2].data["CHSQDOF"][0]), ff[2].data['CHSQDOF'][0]
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
        if a_nan and not b_nan: return b
        if b_nan and not a_nan: return a
        return min([a, b], key=lambda m: SINGLE_MODEL_ORDER.get(m.split("_")[0], 99))
    if a_free == b_free:
        if a_cstat == b_cstat:
            return min([a, b], key=complexity_key)
        return a if a_cstat < b_cstat else b
    simple, simple_c, simple_f, complex_, complex_c, complex_f = (
        (a, a_cstat, a_free, b, b_cstat, b_free) if a_free < b_free else
        (b, b_cstat, b_free, a, a_cstat, a_free)
    )
    required = 9 * (complex_f - simple_f)
    improvement = simple_c - complex_c
    return complex_ if improvement >= required else simple


def compare_single_models(a_model, a_cstat, b_model, b_cstat):
    return compare_models(a_model=a_model, a_cstat=a_cstat, b_model=b_model, b_cstat=b_cstat, single_only=True)


# ----------------- Error Criteria -----------------

def _param_error_limit(model, pname, v, par_constraint, loose):
    pname = pname.lower()
    base = model.split("_")[0]
    if pname == "index2" and base in ("BAND", "SBPL"):
        factor = 1.0 if loose else 0.7
        return factor * abs(v), f"loose_index2({factor})"
    if pname == "index_pl" and "PL" in model.split("_")[1:]:
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
    for (pname, _, _), v, e in zip(schema, vals, errs):
        limit, _ = _param_error_limit(model=model,
                                      pname=pname,
                                      v=v,
                                      par_constraint=par_constraint,
                                      loose=loose_criteria)
        if abs(v) == 0 and abs(e) != 0: return False
        if abs(v) != 0 and abs(e) >= limit: return False
    return True


# ----------------- Filtering & Picking -----------------

def filter_models_by_error(cstats, folder_path, candidates, **kwargs):
    return {m: cstats[m] for m in candidates if
            m in cstats and os.path.exists(os.path.join(folder_path, f"{m}.fit")) and model_passes_error_criteria(
                path=os.path.join(folder_path, f"{m}.fit"), **kwargs)}


def pick_best_in_group(cstats, candidates, group_name):
    present = [m for m in candidates if m in cstats]
    if not present:
        raise ValueError(f"No {group_name} models found")
    present.sort(key=complexity_key)
    best, best_c = present[0], cstats[present[0]]
    for m in present[1:]:
        best = compare_models(a_model=best, a_cstat=best_c, b_model=m, b_cstat=cstats[m])
        best_c = cstats[best]
    return best, best_c


def pick_best_model(cstats, candidates, group_name, folder_path=None, **kwargs):
    if folder_path:
        cstats = filter_models_by_error(cstats=cstats, folder_path=folder_path, candidates=candidates, **kwargs)
        if not cstats:
            raise ValueError(f"No {group_name} models passed error criteria")
    return pick_best_in_group(cstats=cstats, candidates=candidates, group_name=group_name)


def pick_best_single_model(cstats: Dict[str, float]):
    singles = {k.upper(): v for k, v in cstats.items() if k.upper() in SINGLE_MODEL_FREE_PARAMS}
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
    return {m for m in ALLOWED_MODELS if
            os.path.exists(os.path.join(folder_path, f"{m}.fit")) and model_passes_error_criteria(
                os.path.join(folder_path, f"{m}.fit"), **kwargs)}


def compute_good_models(cstats, folder_path, **kwargs):
    good = {}
    base = filter_models_by_error(cstats=cstats,
                                  folder_path=folder_path,
                                  candidates=["PL", "CPL", "BAND", "SBPL"],
                                  **kwargs)
    if base:
        good["BASE"] = pick_best_single_model(base)
    for group, candidates in {
        "+BB": ["PL_BB", "CPL_BB", "BAND_BB", "SBPL_BB"],
        "+PL": ["CPL_PL", "BAND_PL", "SBPL_PL"],
        "+PL+BB": ["CPL_PL_BB", "BAND_PL_BB", "SBPL_PL_BB"]
    }.items():
        try:
            good[group.strip("+")] = pick_best_model(cstats=cstats,
                                                     candidates=candidates,
                                                     group_name=group,
                                                     folder_path=folder_path, **kwargs)
        except Exception:
            pass
    return good


def list_par_err(cwd_, fit_type, string="SAFE", result_dict=None):
    if result_dict is None:
        result_dict = {}

    grb = cwd_.split("/")[-2]
    ep = cwd_.split("/")[-1].split("__")[1].replace("m", "-")

    for m in fit_type:
        fit_path = os.path.join(cwd_, f"{m}.fit")
        if not os.path.exists(fit_path):
            continue
        try:
            schema = build_composite_schema(m)
            vals, errs = read_param_values_errors(path=fit_path, n_parameters=len(schema))

            # store SAFE/UNSAFE status
            model_dict = result_dict.setdefault(grb, {}).setdefault(ep, {}).setdefault(m, {})
            model_dict["_status"] = string

            # store parameters
            for m2, v, e in zip(PARAMETERS[m.lower()], vals, errs):
                model_dict[m2] = np.array([v, e])

            # print log
            print(f"[{string}] {m} parameter details:")
            for (pname, _, _), v, e in zip(schema, vals, errs):
                pct = (abs(e) / abs(v) * 100) if v != 0 else float("inf")
                print(f"   {pname:15s} = {v:.6g}, {e:.6g}, {pct:.3g} %")

        except Exception as e:
            print(f"[{string}] {m}: failed to read params ({e})")

    return result_dict
