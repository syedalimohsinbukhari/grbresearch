"""Created on Jan 07 15:37:00 2026"""

import os
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count
from typing import Optional, Tuple

import numpy as np
from astropy.cosmology import FlatLambdaCDM
from matplotlib import pyplot as plt
from scipy.integrate import simpson
from tqdm import tqdm

from .grb_constants import kev_to_erg, LABEL_FONT_SIZE
from .grb_model import Model
from .grb_sed import SpectralModels
from .grb_time import EpisodeTypes, TimeInterval


def get_rng(seed: int | None = None, rng: np.random.Generator | None = None) -> np.random.Generator:
    """
    Get or create a NumPy random number generator.

    Parameters
    ----------
    seed : int, optional
        Seed for creating a new RNG. Ignored if rng is provided.
    rng : np.random.Generator, optional
        Existing RNG instance to use.

    Returns
    -------
    np.random.Generator
        RNG instance to use for random sampling.
    """
    if seed is None and rng is None:
        raise ValueError("Either seed or rng must be provided.")

    if rng is not None:
        return rng
    return np.random.default_rng(seed)


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
    n_samples : int
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
    n_samples: int = 10_000

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

        rng = np.random.default_rng()
        mn_distribution = rng.multivariate_normal(param_values, param_covar_, self.n_samples)

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

        return qty.cgs.value if not in_units else qty.cgs

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
    model: Model,
    model_type="counts",
    e_range=(1, 7),
    n_samples: int = 10_000,
    n_grid: int = 10_000,
    n_workers: int = None,
    samples=None,
    seed: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
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
    samples : np.ndarray, optional
        Pre-generated samples. If None, samples will be generated.
    seed : int, optional
        Random seed for reproducibility. Ignored if rng is provided.
    rng : np.random.Generator, optional
        Random number generator instance for reproducibility.

    Returns
    -------
    list
        List of evaluated model values for each sample.
    """
    m_keys = [i.name for i in model.parameters]
    m_vals = [i.value for i in model.parameters]

    covar_ = model.covariance_matrix_value
    covar_ = 0.5 * (covar_ + covar_.T)

    if samples is None:
        rng_instance = get_rng(seed=seed, rng=rng)
        samples = rng_instance.multivariate_normal(mean=m_vals, cov=covar_, size=n_samples)

    if n_workers is None:
        n_workers = cpu_count()

    args_list = [
        (model.name, model.interval, m_keys, v, covar_, model_type, e_range, n_samples, n_grid) for v in samples
    ]

    with Pool(n_workers) as pool:
        results = list(tqdm(iterable=pool.imap(func=legacy_build_mp, iterable=args_list), total=n_samples))

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
    part = np.nanpercentile(s, [16, 50, 84], axis=1)

    return np.asarray(part[1], dtype=float).T, np.asarray(part[0], dtype=float).T, np.asarray(part[2], dtype=float).T


def mcmc_e_iso_sampler(
    model: Model,
    z: float = 1.0,
    n_samples: int = 100,
    n_grid: int = 100,
    det_min: float = 1.0,
    det_max: float = 7.0,
    bol_min: float = 0,
    bol_max: float = 4.0,
    h0: float = 70.0,
    omega_m: float = 0.315,
    method=1,
    samples=None,
    seed_number=1234,
    rng: Optional[np.random.Generator] = None,
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
    method : int, optional
        Method to use for calculation (default: 1).
    samples : np.ndarray, optional
        Pre-generated samples. If None, samples will be generated.
    seed_number : int, optional
        Random seed for reproducibility (default: 1234). Ignored if rng is provided.
    rng : np.random.Generator, optional
        Random number generator instance for reproducibility.

    Returns
    -------
    np.ndarray
        Array of E_iso samples in erg with shape (1, n_samples).
    """
    rng_instance = get_rng(seed=seed_number, rng=rng)
    bolometric_fluence = 0

    energy_bolometric = np.logspace(start=bol_min, stop=bol_max, num=n_grid)
    e_observed = energy_bolometric / (1 + z)
    # ph / cm^2 / s / keV (n_samples, n_grid)
    bolometric_samples = np.asarray(
        mcmc_spectra_sampler(
            model=model,
            model_type="energy",
            e_range=(bol_min, bol_max),
            n_samples=n_samples,
            n_grid=n_grid,
            samples=samples,
            rng=rng_instance,
        )
    )
    if method == 1:
        energy_detector = np.logspace(start=det_min, stop=det_max, num=n_grid)
        detector_samples = np.asarray(
            mcmc_spectra_sampler(
                model=model,
                model_type="energy",
                e_range=(det_min, det_max),
                n_samples=n_samples,
                n_grid=n_grid,
                rng=rng_instance,
            )
        )
        # keV / cm^2: vectorized integration over axis=1
        detector_fluence = (
            simpson(y=detector_samples * energy_detector, x=energy_detector, axis=1) * model.interval.duration
        )

        numerator = simpson(y=bolometric_samples * e_observed, x=e_observed, axis=1)
        denominator = simpson(y=detector_samples * energy_detector, x=energy_detector, axis=1)

        # k correction
        bolometric_fluence = detector_fluence * (numerator / denominator)
        # erg / cm^2
        bolometric_fluence = np.asarray(bolometric_fluence, dtype=float) * kev_to_erg
    elif method == 2:
        bolometric_fluence = simpson(y=bolometric_samples, x=e_observed, axis=1) * model.interval.duration * kev_to_erg

    lum_distance = FlatLambdaCDM(H0=h0, Om0=omega_m).luminosity_distance(z).cgs.value
    return (4 * np.pi * lum_distance**2 * bolometric_fluence.reshape(1, -1)) / (1 + z)


def plot_best_models(best_models, n_rows=2, n_cols=None, grb_name=None, fig_size=(15, 4), save=True):
    """
    Plots the energy flux of the best-fitting models for gamma-ray burst (GRB) intervals.

    This function creates subplots to display the results of spectral fits for a set of best models
    applied to a GRB dataset. It computes the median and credible interval from MCMC samples for
    each model and visualizes them with log-log plots. Each subplot corresponds to a specific
    model or time interval.

    Parameters
    ----------
    best_models :
        A list of best-fitting spectral models, where each model contains
        attributes such as interval type and name.
    n_rows :
        Number of rows in the subplot grid. Default is 2.
    n_cols :
        Number of columns in the subplot grid. If None, it will be determined dynamically.
    grb_name :
        Name of the GRB for labeling and saving output files. Default is None.
    fig_size :
        Figure size for the plot, specified as (width, height). Default is (15, 4).

    Returns
    -------
    None
    """
    n_grid = 500
    n_samples = 10_000 if os.cpu_count() > 10 else 1_000
    x = np.logspace(1, 7, n_grid)

    f, ax = plt.subplots(n_rows, n_cols, figsize=fig_size, sharex=True, sharey=True)
    ax = ax.flatten()

    has_cpl_bb = False

    for i, v in enumerate(best_models):
        if "BB" in v.name or "CPL" in v.name:
            has_cpl_bb = True
        color = (
            "k"
            if v.interval.kind == EpisodeTypes.T90
            else (
                "b"
                if v.interval.kind in [EpisodeTypes.EX0, EpisodeTypes.EX1]
                else "g" if v.interval.kind == EpisodeTypes.SP else "r"
            )
        )
        print(f"processing {v.name}")
        samples = mcmc_spectra_sampler(v, n_samples=n_samples, n_grid=n_grid)
        samples = np.array(samples)

        med, low, high = credible_interval_partition(samples)
        med, low, high = med * kev_to_erg, low * kev_to_erg, high * kev_to_erg
        ax[i].loglog(
            x, med * x**2, f"{color}--", label=f"{v.name.replace('_', '+')}\n({v.interval.start} - {v.interval.end})"
        )
        ax[i].fill_between(x, low * x**2, high * x**2, color=color, alpha=0.2)
        ax[i].legend()

    [v.set_xlabel("Energy [keV]") for i, v in enumerate(ax) if i > (n_cols - 1)]
    [v.set_ylabel("Energy Flux\n" + r"[erg/cm$^2$/s]") for i, v in enumerate(ax) if i % n_cols == 0]

    if has_cpl_bb:
        ax[-1].set_ylim(bottom=3.2e-10, top=2.8e-4)

    f.tight_layout()
    if save:
        [plt.savefig(f"butterfly_{grb_name}.{i}", dpi=300) for i in ["png", "pdf"]]
        plt.close()
    else:
        plt.show()


def plot_all_models(
    best_models,
    grb_name,
    n_rows: int = 2,
    n_cols: int | None = None,
    fig_size: tuple[float, float] = (12.0, 8.0),
    save: bool = False,
    seed: int | None = None,
    rng: np.random.Generator | None = None,
):
    """
    Generates a grid of plots displaying spectral energy distributions for a collection of models.

    Parameters
    ----------
    :param best_models: A nested list where each sublist contains spectral models for a specific GRB.
        Each model within a sublist should contain spectral information and interval data.
    :param grb_name: A list of strings corresponding to the names of the GRBs.
        This is used to label the plots and to save the output files.
    :param n_rows: The number of rows in the grid of plots. Default is 2.
    :param n_cols: The number of columns in the grid of plots.
        If None (default), it is automatically determined based on the number of GRBs and `n_rows`.
    :param fig_size: A tuple of floats representing the size of the figure in inches.
        Default is (12, 8).
    :param save: A boolean flag indicating whether to save the generated plots.
        If True, the plots will be saved as PNG and PDF files in the current working directory.
        If False, the plots will be displayed on the screen.
    :param seed: An optional integer seed for reproducibility.
        If provided, it will be used to initialize the random number generator.
    :param rng: An optional instance of `np.random.Generator` for reproducible results.
        If provided, it will be used instead of the default random number generator.

    """
    rng = get_rng(seed=seed, rng=rng)

    n_grid = 500
    n_samples = 10_000 if os.cpu_count() > 10 else 1_000
    x = np.logspace(1, 7, n_grid)

    # legend position per panel — keeps legend away from the spectral peaks
    legend_loc = {0: 'lower left', 1: 'lower left', 2: 'lower left', 3: 'upper right'}

    f, ax = plt.subplots(n_rows, n_cols, figsize=fig_size, sharey=True, sharex=True)
    ax = ax.flatten()

    for i, v in enumerate(best_models):
        print(f"processing {grb_name[i]}")
        is_ex = sum([ep.interval.is_ex for ep in v])  # fixed: was shadowing outer loop variable i
        if is_ex == 2:
            v[-1], v[-2] = v[-2], v[-1]

        for j, w in enumerate(v):
            print(f"processing {w.name}")
            samples = mcmc_spectra_sampler(w, n_samples=n_samples, n_grid=n_grid, rng=rng)
            samples = np.array(samples)

            med, low, high = credible_interval_partition(samples)
            med, low, high = med * kev_to_erg, low * kev_to_erg, high * kev_to_erg

            if j == 0:
                ax[i].loglog(x, med * x**2, "k-", label=f"{w.interval.kind}" + r"$_\text{" + f'{w.name.replace("_", "+")}' + r"}$")
                ax[i].fill_between(x, low * x**2, high * x**2, color="k", alpha=0.2)
            else:
                sub = (
                    f"{w.interval.kind}{w.interval.index}"
                    if w.interval.kind in [EpisodeTypes.TR, EpisodeTypes.SP]
                    else w.interval.kind
                )
                ax[i].loglog(x, med * x**2, "--", label=f"{sub}" + r"$_\text{" + f'{w.name.replace("_", "+")}' + r"}$")
                ax[i].fill_between(x, low * x**2, high * x**2, alpha=0.2)

            ax[i].set_ylim(bottom=3.2e-10, top=8.7e-5)

        # ── legend fix ────────────────────────────────────────────────────────
        ax[i].legend(
            ncols=3,
            title=f"{grb_name[i]}",
            shadow=True,
            loc=legend_loc.get(i, 'best'),
            fontsize=7,
            title_fontsize=8,
        )
        # ─────────────────────────────────────────────────────────────────────

        if i % n_cols == 0:  # fixed: was hardcoded % 2, now uses n_cols
            ax[i].set_ylabel("Energy Flux\n" + r"[erg/cm$^2$/s]", fontsize=LABEL_FONT_SIZE)

    [i.grid(True, axis="both", ls="--", alpha=0.5, zorder=-10) for i in ax]
    [ax[i].set_xlabel("Energy [keV]", fontsize=LABEL_FONT_SIZE) for i in range(len(best_models) - n_cols, len(best_models))]  # fixed: was hardcoded [ax[2], ax[3]]
    plt.tight_layout()
    if save:
        [plt.savefig(f"butterfly_all.{i}", dpi=300) for i in ["png", "pdf"]]
        plt.close()
    else:
        plt.show()