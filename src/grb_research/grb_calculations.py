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
    """
    Class to calculate isotropic energy for a given model and time interval.

    Attributes
    ----------
    model : Model
        The spectral model used for calculations.
    model_interval : TimeInterval
        The time interval for the model.
    n_iter : int
        Number of iterations for Monte Carlo simulations.
    e_low : int, optional
        Lower energy bound for calculations (default: 1).
    e_high : int, optional
        Upper energy bound for calculations (default: 7).
    redshift : float, optional
        Redshift value for the GRB (default: 0.0).
    h0 : float, optional
        Hubble constant (default: 70).
    omega_m : float, optional
        Matter density parameter (default: 0.315).
    """

    model: Model
    model_interval: TimeInterval
    n_iter: int

    e_low: int = 1
    e_high: int = 7

    redshift: float = 0.0

    h0: float = 70
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

        for index, value in enumerate(param_names):
            multivariate_dict[value] = mn_distribution[:, index]

        return multivariate_dict

    def luminosity_distance(self, in_units: bool = False):
        """
        Calculate the luminosity distance in cm.

        Parameters
        ----------
        in_units : bool, optional
            If True, returns the distance as an astropy Quantity object (default: False).

        Returns
        -------
        float or Quantity
            Luminosity distance in cm (or as a Quantity if in_units is True).
        """
        qty = FlatLambdaCDM(H0=self.h0, Om0=self.omega_m).luminosity_distance(self.redshift)

        return (
            qty.cgs.value if not in_units else qty.cgs
        )

    def calculate(self):
        """
        Calculate the isotropic energy in ergs.

        Returns
        -------
        float
            The isotropic energy in ergs.
        """
        fluence = self.spectral_model(m_type="bolometric")

        # E_iso = (4 * pi * dl^2 * fluence) / (1 + z)
        dl = self.luminosity_distance()
        e_iso = (4 * np.pi * dl**2 * fluence) / (1 + self.redshift)

        return e_iso

    def spectral_model(self, m_type="integrate"):
        """
        Generate the spectral model values.

        Parameters
        ----------
        m_type : str, optional
            Type of model to generate (default: "integrate").

        Returns
        -------
        np.ndarray
            Spectral model values.
        """
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


def legacy_build_mp(pars):
    """
    Multiprocessing worker wrapper for `SpectralModels.legacy_build`.

    Parameters
    ----------
    pars : tuple
        Tuple containing:
        - m_name: str
            Model name.
        - interval: object
            Model interval object (opaque to this function).
        - m_keys: list of str
            List of parameter names.
        - sample: list of float
            Parameter values for this sample.
        - covar: np.ndarray
            Covariance matrix.
        - model_type: str
            String passed through to `legacy_build`.
        - e_range: tuple
            Energy range for the model.
        - n_sample: int
            Number of samples.
        - n_grid: int
            Number of grid points.

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


def mcmc_spectra_sampler(
        model: Model, model_type='counts', e_range=(1, 7), n_samples: int = 10_000, n_grid: int = 10_000, n_workers: int = None
):
    """
    Parallel MCMC sampler for spectral model parameter estimation.

    Parameters
    ----------
    model : Model
        The model to sample from.
    model_type : str, optional
        Type of model to generate (default: 'counts').
    e_range : tuple, optional
        Energy range for the model (default: (1, 7)).
    n_samples : int, optional
        Number of MCMC samples to draw (default: 10,000).
    n_grid : int, optional
        Number of grid points for numerical integration (default: 10,000).
    n_workers : int, optional
        Number of parallel workers (default: CPU count).

    Returns
    -------
    list
        List of evaluated model values for each sample.
    """
    m_keys = [i.name for i in model.parameters]
    m_vals = [i.value for i in model.parameters]

    covar_ = model.covariance_matrix_value
    covar_ = 0.5 * (covar_ + covar_.T)

    samples = multivariate_normal(m_vals, covar_, n_samples)

    if n_workers is None:
        n_workers = cpu_count()

    args_list = [
        (model.name, model.interval, m_keys, v, covar_, model_type, e_range, n_samples, n_grid) for v in samples
    ]

    with Pool(n_workers) as pool:
        results = list(tqdm(pool.imap(legacy_build_mp, args_list), total=n_samples))

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
    tuple
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
        h0: float = 70.0,
        omega_m: float = 0.315,
) -> np.ndarray:
    """
    Draw MCMC samples and compute isotropic-equivalent energy (E_iso).

    Parameters
    ----------
    model : Model
        Spectral model container providing sampling and interval duration.
    z : float, optional
        Redshift used for K-correction and luminosity distance (default: 1.0).
    n_samples : int, optional
        Number of MCMC samples to draw (default: 100).
    n_grid : int, optional
        Number of energy grid points for numerical integration (default: 100).
    det_min : float, optional
        Log10 lower bound for detector energy grid (keV) (default: 1.0).
    det_max : float, optional
        Log10 upper bound for detector energy grid (keV) (default: 7.0).
    bol_min : float, optional
        Log10 lower bound for bolometric energy grid (keV) (default: -1.0).
    bol_max : float, optional
        Log10 upper bound for bolometric energy grid (keV) (default: 4.0).
    h0 : float, optional
        Hubble constant (default: 70.0).
    omega_m : float, optional
        Matter density parameter (default: 0.315).

    Returns
    -------
    np.ndarray
        Array of E_iso samples in erg with shape (1, n_samples).
    """
    energy_detector = np.logspace(start=det_min, stop=det_max, num=n_grid)
    energy_bolometric = np.logspace(start=bol_min, stop=bol_max, num=n_grid)

    # ph / cm^2 / s / keV (n_samples, n_grid)
    detector_samples = mcmc_spectra_sampler(model, 'counts',
                                            e_range=(det_min, det_max), n_samples=n_samples, n_grid=n_grid)
    bolometric_samples = mcmc_spectra_sampler(model, 'counts',
                                              e_range=(bol_min, bol_max), n_samples=n_samples, n_grid=n_grid)

    detector_samples, bolometric_samples = np.asarray(detector_samples), np.asarray(bolometric_samples)

    # keV / cm^2: vectorized integration over axis=1
    detector_fluence = simpson(y=detector_samples * energy_detector, x=energy_detector, axis=1) * model.interval.duration

    e_observed = energy_bolometric / (1 + z)
    numerator = simpson(y=bolometric_samples * e_observed, x=e_observed, axis=1)
    denominator = simpson(y=detector_samples * energy_detector, x=energy_detector, axis=1)

    # k correction
    bolometric_fluence = detector_fluence * (numerator / denominator)
    # erg / cm^2
    bolometric_fluence = np.asarray(bolometric_fluence, dtype=float) * kev_to_erg

    lum_distance = FlatLambdaCDM(H0=h0, Om0=omega_m).luminosity_distance(z).cgs.value
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
        samples = mcmc_spectra_sampler(v, n_samples=n_samples, n_grid=n_grid)
        samples = np.array(samples)

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


def plot_all_models(best_models, grb_name, n_rows=2, n_cols=None, fig_size=(12, 8)):
    n_grid = 500
    n_samples = 1000
    x = np.logspace(1, 7, n_grid)

    f, ax = plt.subplots(n_rows, n_cols, figsize=fig_size)
    ax = ax.flatten()

    has_cpl_bb = False

    for i, v in enumerate(best_models):
        print(f'processing {grb_name[i]}')
        is_ex = sum([i.interval.is_ex for i in v])
        if is_ex == 2:
            v[-1], v[-2] = v[-2], v[-1]

        for j, w in enumerate(v):
            if 'CPL' in w.name:
                has_cpl_bb = True

            print(f'processing {w.name}')
            samples = mcmc_spectra_sampler(w, n_samples=n_samples, n_grid=n_grid)
            samples = np.array(samples)

            med, low, high = credible_interval_partition(samples)
            med, low, high = med * kev_to_erg, low * kev_to_erg, high * kev_to_erg

            if j == 0:
                ax[i].loglog(x, med * x**2, 'k--', label=f"{w.interval.kind}")
                ax[i].fill_between(x, low * x**2, high * x**2, color='k', alpha=0.2)
            else:
                sub = f'{w.interval.kind}{w.interval.index}' if w.interval.kind == EpisodeTypes.TR else w.interval.kind
                ax[i].loglog(x, med * x**2, '--', label=f"{sub}")
                ax[i].fill_between(x, low * x**2, high * x**2, alpha=0.2)

            if has_cpl_bb:
                ax[i].set_ylim(bottom=3.2e-10, top=2.8e-4)

            has_cpl_bb = False

        ax[i].legend(ncols=4 if i == 0 else 2, title=f'{grb_name[i]}')

        if i % 2 != 0:
            ax[i].set_yticks([])

        if i % 2 == 0:
            ax[i].set_ylabel("Energy Flux\n" + r"[erg/cm$^2$/s]")

    [i.set_xticks([]) for i in [ax[0], ax[1]]]
    [i.set_xlabel('Energy [keV]') for i in [ax[2], ax[3]]]
    plt.tight_layout()
    # plt.show()
    [plt.savefig(f'butterfly_all.{i}', dpi=300) for i in ["png", "pdf"]]
    plt.close()
