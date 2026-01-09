"""Created on Jan 07 15:37:00 2026"""

from dataclasses import dataclass
from multiprocessing import cpu_count, Pool
from typing import Tuple

import numpy as np
from astropy.cosmology import FlatLambdaCDM
from matplotlib import pyplot as plt
from numpy.random import multivariate_normal
from scipy.integrate import simpson
from tqdm import tqdm

from .grb_constants import kev_to_erg
from .grb_model import Model
from .grb_sed import SpectralModels
from .grb_time import EpisodeTypes, TimeInterval


@dataclass
class IsotropicEnergy:
    model: Model
    model_interval: TimeInterval
    n_iter: int

    e_low: int = 1
    e_high: int = 7

    redshift: float = 0.0

    h0: float = 67.4
    omega_m: float = 0.315

    def __post_init__(self):
        self.mvd = self.__create_mvd()

    def __create_mvd(self):
        multivariate_dict = {}
        param_names = [param.name for param in self.model.parameters]
        param_values = [param.value for param in self.model.parameters]
        param_covar_ = self.model.covariance_matrix_value
        param_covar_ = 0.5 * (param_covar_ + param_covar_.T)
        mn_distribution = multivariate_normal(param_values, param_covar_, self.n_iter)

        for i, v in enumerate(param_names):
            multivariate_dict[v] = mn_distribution[:, i]

        return multivariate_dict

    def luminosity_distance(self):
        """Calculate luminosity distance in cm."""
        return FlatLambdaCDM(H0=self.h0, Om0=self.omega_m).luminosity_distance(self.redshift).cgs.value

    def calculate(self):
        """Calculate the isotropic energy in ergs."""
        fluence = self.spectral_model(m_type="bolometric")

        # E_iso = (4 * pi * dl^2 * fluence) / (1 + z)
        dl = self.luminosity_distance()
        e_iso = (4 * np.pi * dl**2 * fluence) / (1 + self.redshift)

        return e_iso

    def spectral_model(self, m_type="integrate"):
        p_name = [i.name for i in self.model.parameters]
        p_values = [i.value for i in self.model.parameters]

        sp_model = SpectralModels.legacy_build(
            m_name=self.model.name,
            interval_instance=self.model_interval,
            p_name=p_name,
            p_vals=p_values,
            cov_=self.model.covariance_matrix_value,
            model_type=m_type,
            e_range=(self.e_low, self.e_high),
            redshift=self.redshift,
            h0=self.h0,
            omega_m=self.omega_m,
        )

        return sp_model.get_values()


def legacy_build_mp_runner(pars):
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
    m_name, interval, m_keys, sample, covar, model_type, e_range, n_sample, n_grid = pars
    built = SpectralModels.legacy_build(
        m_name,
        interval,
        m_keys,
        sample,
        covar,
        n_samples=n_sample,
        n_grid=n_grid,
        model_type=model_type,
        e_range=e_range,
    ).get_values()

    # the original behavior returned element 1 when the name contains an underscore
    if "_" in m_name:
        return built[1]
    return built


def mcmc_sampler_parallel(
        model: Model, e_range=(1, 7), n_samples: int = 10_000, n_grid: int = 10_000, n_workers: int = None
):
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

    samples = multivariate_normal(m_vals, covar_, n_samples)

    if n_workers is None:
        n_workers = cpu_count()

    args_list = [
        (model.name, model.interval, m_keys, v.tolist(), covar_, "counts", e_range, n_samples, n_grid) for v in samples
    ]

    with Pool(n_workers) as pool:
        results = list(tqdm(pool.imap(legacy_build_mp_runner, args_list), total=n_samples))

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
    part = np.nanpercentile(s, [16, 50, 80], axis=1)

    return np.asarray(part[1], float).T, np.asarray(part[0], float).T, np.asarray(part[2], float).T


def mcmc_e_iso_sampler(
        model: Model,
        z: float = 1.0,
        n_samples: int = 100,
        n_grid: int = 100,
        det_min: float = 1.0,
        det_max: float = 7.0,
        bol_min: float = -1.0,
        bol_max: float = 4.0,
) -> np.ndarray:
    """
    Draw MCMC samples and compute isotropic-equivalent energy (E_iso).

    Parameters
    \- `model` : Model
        Spectral model container providing sampling and interval duration.
    \- `n_samples` : int
        Number of MCMC samples to draw.
    \- `n_grid` : int
        Number of energy grid points for numerical integration.
    \- `det_min`, `det_max` : float
        Log10 bounds for detector energy grid (keV).
    \- `bol_min`, `bol_max` : float
        Log10 bounds for bolometric energy grid (keV).
    \- `z` : float
        Redshift used for K-correction and luminosity distance.

    Returns
    \- `np.ndarray`
        Array of E\_iso samples in erg with shape `(1, n_samples)`.
    """
    energy_detector = np.logspace(det_min, det_max, n_grid)
    energy_bolometric = np.logspace(bol_min, bol_max, n_grid)

    # ph / cm^2 / s / keV (n_samples, n_grid)
    detector_samples = mcmc_sampler_parallel(model, (det_min, det_max), n_samples, n_grid)
    bolometric_samples = mcmc_sampler_parallel(model, (bol_min, bol_max), n_samples, n_grid)

    detector_samples, bolometric_samples = np.asarray(detector_samples), np.asarray(bolometric_samples)

    # keV / cm^2: vectorized integration over axis=1
    detector_fluence = simpson(detector_samples * energy_detector, x=energy_detector, axis=1) * model.interval.duration

    e_observed = energy_bolometric / (1 + z)
    num = simpson(bolometric_samples * e_observed, x=e_observed, axis=1)
    den = simpson(detector_samples * energy_detector, x=energy_detector, axis=1)

    # k correction
    bolometric_fluence = detector_fluence * (num / den)
    # erg / cm^2
    bolometric_fluence = np.asarray(bolometric_fluence, dtype=float) * kev_to_erg

    lum_distance = FlatLambdaCDM(H0=67.4, Om0=0.315).luminosity_distance(z).cgs.value
    return (4 * np.pi * lum_distance**2 * bolometric_fluence.reshape(1, -1)) / (1 + z)


def plot_best_models(best_models, n_rows=2, n_cols=None, grb_name=None, fig_size=(15, 4)):
    n_grid = 500
    n_samples = 1000
    x = np.logspace(1, 7, n_grid)

    f, ax = plt.subplots(n_rows, n_cols, figsize=fig_size, sharex=True, sharey=True)
    ax = ax.flatten()

    has_cpl_bb = False

    for i, v in enumerate(best_models):
        if 'BB' in v.name or 'CPL' in v.name:
            has_cpl_bb = True
        color = 'k' if v.interval.kind == EpisodeTypes.T90 else 'b' if v.interval.kind in [EpisodeTypes.EX0, EpisodeTypes.EX1] else 'r'
        print(f'processing {v.name}')
        samples = mcmc_sampler_parallel(v, n_samples=n_samples, n_grid=n_grid)
        samples = np.array(samples)

        p = np.percentile(samples, [16, 50, 84], axis=0)
        med, low, high = credible_interval_partition(samples)
        med, low, high = med * kev_to_erg, low * kev_to_erg, high * kev_to_erg
        ax[i].loglog(x, med * x**2, f'{color}--', label=f"{v.name.replace('_', '+')}\n({v.interval.start} - {v.interval.end})")
        ax[i].fill_between(x, low * x**2, high * x**2, color=color, alpha=0.2)
        ax[i].legend()

    [v.set_xlabel("Energy [keV]") for i, v in enumerate(ax) if i > (n_cols - 1)]
    [v.set_ylabel("Energy Flux\n" + r"[erg/cm$^2$/s]") for i, v in enumerate(ax) if i % n_cols == 0]

    if has_cpl_bb:
        ax[-1].set_ylim(bottom=3.2e-10, top=2.8e-4)

    f.tight_layout()
    [plt.savefig(f'butterfly_{grb_name}.{i}', dpi=300) for i in ["png", "pdf"]]
    plt.close()
