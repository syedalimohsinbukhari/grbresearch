"""Created on Jan 04 18:46:18 2026"""

import json
import time
from multiprocessing import cpu_count, Pool
from typing import Tuple

import numpy as np
from matplotlib import pyplot as plt
from numpy.random import multivariate_normal
from tqdm import tqdm

from src.grb_research import find_project_root, Model, SpectralModels
from src.grb_research.grb_constants import short_to_long
from src.grb_research.grb_core import GRBCatalog

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"

with open(result_file, "r") as f:
    example_data = json.load(f)

grb_list = ["080916C", "110721A", "110731A", "150210A"]
grb_list_long = [short_to_long[i] for i in grb_list]

gc = GRBCatalog.from_iterable(grb_list=grb_list, data=example_data, name_mapping=short_to_long)

grb110721a = gc.get_grb(grb_list_long[0])

grb110721a_best = grb110721a.get_all_best_models()
model_to_evaluate = grb110721a_best[0]

print(model_to_evaluate)

start_110721, end_110721, diff_110721, midpoint_110721 = grb110721a.intervals.extract_interval_arrays(
    return_include=("diff", "midpoint")
)


def legacy_build_mp_runner(pars: tuple[str, object, list[str], list[float], np.ndarray, str]) -> np.ndarray:
    """
    Multiprocessing worker wrapper for `SpectralModels.legacy_build`.

    Parameters
    ----------
    pars : tuple[str, object, list[str], list[float], np.ndarray, str]
        Tuple containing:
        - m_name: model name
        - interval: model interval object (opaque to this function)
        - m_keys: list of parameter names
        - sample: parameter values for this sample (list of floats)
        - covar: covariance matrix (np.ndarray)
        - model_type: string passed through to `legacy_build`

    Returns
    -------
    np.ndarray
        The evaluated model values.
    """
    m_name, interval, m_keys, sample, covar, model_type = pars
    built = SpectralModels.legacy_build(
        m_name, interval, m_keys, sample, covar, model_type=model_type
    ).get_values()

    # the original behavior returned element 1 when the name contains an underscore
    if "_" in m_name:
        return built[1]
    return built


def mcmc_sampler_parallel(model: Model, n_iters: int = 10_000, n_workers: int = None):
    """
    Parallel MCMC sampler for spectral model parameter estimation.

    Parameters:
    -----------
    model : Model
        The model to sample from
    n_iters : int
        Number of MCMC iterations
    n_workers : int, optional
        Number of parallel workers (default: CPU count)

    Returns:
    --------
    pars : np.ndarray
        Array of parameter values (shape: n_iters)
    samples : np.ndarray
        Array of all samples (shape: n_iters x n_parameters)
    """
    m_keys = [i.name for i in model.parameters]
    m_vals = [i.value for i in model.parameters]

    covar_ = model.covariance_matrix_value
    covar_ = 0.5 * (covar_ + covar_.T)

    samples = multivariate_normal(m_vals, covar_, n_iters)

    if n_workers is None:
        n_workers = cpu_count()

    print(f"Starting parallel MCMC with {n_workers} workers...")
    st = time.perf_counter()

    args_list = [(model.name, model.interval, m_keys, v.tolist(), covar_, "counts")
                 for v in samples]

    with Pool(n_workers) as pool:
        results = list(tqdm(pool.imap(legacy_build_mp_runner, args_list), total=n_iters))

    elapsed = time.perf_counter() - st
    print(f"Total time: {elapsed:.2f} seconds")
    print(f"Average time per iteration: {elapsed / n_iters * 1000:.2f} ms")

    return results


def credible_interval_partition(samples: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute 16th, 50th (median), and 84th percentiles per parameter from MCMC samples.

    Parameters
    ----------
    samples : np.ndarray
        2D input array with shape (n_samples, n_parameters). Each row is an independent
        sample of the parameter vector.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        A tuple (median, lower, upper), each a 1D array of shape (n_parameters,)
        containing the 50th, 16th, and 84th percentiles respectively.
    """
    s = samples.T
    part = np.percentile(s, [16, 50, 80], axis=1)

    return np.asarray(part[1], float), np.asarray(part[0], float), np.asarray(part[2], float)


sp = SpectralModels(model_to_evaluate, "nfn").get_values()

n_energy = 10_000
n_iterations = 1_000

x = np.logspace(1, 7, n_energy)

q = mcmc_sampler_parallel(model_to_evaluate, n_iters=n_iterations)
q = np.array(q)

print(q.shape)
q_arr = q[~np.any(q < 0, axis=1)]
print(q_arr.shape)

st = time.perf_counter()
y_med, y_lo, y_hi = credible_interval_partition(q_arr)
print(f"Time taken in partitioning = {time.perf_counter() - st:.2f} seconds")

plt.loglog(x, sp[-1] if isinstance(sp, tuple) else sp, 'k--', label=model_to_evaluate.name)
plt.plot(x, y_med * x**2, 'r--', label='Median')
plt.fill_between(x, y_hi * x**2, y_lo * x**2, alpha=0.15, color='r')
plt.xlabel('Energy [keV]')
plt.ylabel('Flux [keV/cm$^2$/s]')
plt.legend()
plt.tight_layout()
plt.show()
