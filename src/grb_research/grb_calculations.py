"""Created on Jan 07 15:37:00 2026"""

from dataclasses import dataclass
from multiprocessing import cpu_count, Pool
from typing import List, Optional, Tuple

import numpy as np
from astropy.cosmology import FlatLambdaCDM
from matplotlib import pyplot as plt
from scipy.integrate import simpson
from tqdm import tqdm

from .grb_constants import kev_to_erg
from .grb_model import Model
from .grb_sed import SpectralModels
from .grb_time import EpisodeTypes, TimeInterval
from .grb_utils import break_e_to_e_peak


def get_rng(seed: Optional[int] = None, rng: Optional[np.random.Generator] = None) -> np.random.Generator:
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
    part = np.nanpercentile(s, [16, 50, 80], axis=1)

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
            model=model, model_type="energy", e_range=(bol_min, bol_max), n_samples=n_samples, n_grid=n_grid,
            samples=samples, rng=rng_instance
        )
    )
    if method == 1:
        energy_detector = np.logspace(start=det_min, stop=det_max, num=n_grid)
        detector_samples = np.asarray(
            mcmc_spectra_sampler(
                model=model, model_type="energy", e_range=(det_min, det_max), n_samples=n_samples, n_grid=n_grid,
                rng=rng_instance
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


def plot_best_models(best_models, n_rows=2, n_cols=None, grb_name=None, fig_size=(15, 4)):
    """
    Plots the energy flux of the best-fitting models for gamma-ray burst (GRB) intervals.

    This function creates subplots to display the results of spectral fits for a set of best models
    applied to a GRB dataset. It computes the median and credible interval from MCMC samples for
    each model and visualizes them with log-log plots. Each subplot corresponds to a specific
    model or time interval.

    Parameters
    ----------
    best_models : list
        A list of best-fitting spectral models, where each model contains
        attributes such as interval type and name.
    n_rows : int, optional
        Number of rows in the subplot grid. Default is 2.
    n_cols : int, optional
        Number of columns in the subplot grid. If None, it will be determined dynamically.
    grb_name : str, optional
        Name of the GRB for labeling and saving output files. Default is None.
    fig_size : tuple of float, optional
        Figure size for the plot, specified as (width, height). Default is (15, 4).

    Returns
    -------
    None
    """
    n_grid = 500
    n_samples = 1000
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
            else "b" if v.interval.kind in [EpisodeTypes.EX0, EpisodeTypes.EX1]
            else "g" if v.interval.kind == EpisodeTypes.SP else "r"
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
    [plt.savefig(f"butterfly_{grb_name}.{i}", dpi=300) for i in ["png", "pdf"]]
    plt.close()


def plot_all_models(best_models, grb_name, n_rows=2, n_cols=None, fig_size=(12, 8)):
    """
    Generates a grid of plots displaying spectral energy distributions for a collection of models.

    This function takes a set of best-fit models for gamma-ray bursts (GRBs), creates energy flux
    distributions for each model using Monte Carlo sampling, and visualizes the results on a grid of
    log-log plots. Each plot corresponds to one GRB, displaying its associated models and intervals.
    Special consideration is given to cases with a "CPL" component in the models, where specific limits
    are applied to the y-axis.

    Parameters
    ----------
    best_models : list of lists
        A nested list where each sublist contains spectral models for a specific GRB.
        Each model within a sublist should contain spectral information and interval data.

    grb_name : list of str
        List of gamma-ray burst names corresponding to the entries in `best_models`.

    n_rows : int, optional
        Number of rows in the plot grid. Default is 2.

    n_cols : int, optional
        Number of columns in the plot grid.
        If None (default), it is automatically determined based on the number of GRBs and `n_rows`.

    fig_size : tuple of float, optional
        The size of the entire figure in inches. Default is (12, 8).
    """
    n_grid = 500
    n_samples = 1000
    x = np.logspace(1, 7, n_grid)

    f, ax = plt.subplots(n_rows, n_cols, figsize=fig_size)
    ax = ax.flatten()

    has_cpl_bb = False

    for i, v in enumerate(best_models):
        print(f"processing {grb_name[i]}")
        is_ex = sum([i.interval.is_ex for i in v])
        if is_ex == 2:
            v[-1], v[-2] = v[-2], v[-1]

        for j, w in enumerate(v):
            if "CPL" in w.name:
                has_cpl_bb = True

            print(f"processing {w.name}")
            samples = mcmc_spectra_sampler(w, n_samples=n_samples, n_grid=n_grid)
            samples = np.array(samples)

            med, low, high = credible_interval_partition(samples)
            med, low, high = med * kev_to_erg, low * kev_to_erg, high * kev_to_erg

            if j == 0:
                ax[i].loglog(x, med * x**2, "k--", label=f"{w.interval.kind}")
                ax[i].fill_between(x, low * x**2, high * x**2, color="k", alpha=0.2)
            else:
                sub = f"{w.interval.kind}{w.interval.index}" if w.interval.kind in [EpisodeTypes.TR, EpisodeTypes.SP] else w.interval.kind
                ax[i].loglog(x, med * x**2, "--", label=f"{sub}")
                ax[i].fill_between(x, low * x**2, high * x**2, alpha=0.2)

            if has_cpl_bb:
                ax[i].set_ylim(bottom=3.2e-10, top=2.8e-4)

            has_cpl_bb = False

        ax[i].legend(ncols=4 if i == 0 else 2, title=f"{grb_name[i]}")

        if i % 2 != 0:
            ax[i].set_yticks([])

        if i % 2 == 0:
            ax[i].set_ylabel("Energy Flux\n" + r"[erg/cm$^2$/s]")

    [i.set_xticks([]) for i in [ax[0], ax[1]]]
    [i.set_xlabel("Energy [keV]") for i in [ax[2], ax[3]]]
    plt.tight_layout()
    # plt.show()
    [plt.savefig(f"butterfly_all.{i}", dpi=300) for i in ["png", "pdf"]]
    plt.close()


def amati_relationship_dirirsia2019(
        e_iso_norm=1e52,
        e_i_peak_norm=950.0,
        log_k=1.67,
        sigma_log_k=0.16,
        m=1.16,
        sigma_m=0.37,
        sigma_ext=0.47,
        sigmas=(1, 2, 3),
        x_lim=(10, 1e5),
        y_lim=(1e50, 1e55),
        num_points=1_000,
        use_average=False
):
    """Plot the Amati relation with confidence bands."""

    # Generate e_i_peak and calculate log-space values
    e_i_peak = np.logspace(np.log10(x_lim[0]), np.log10(x_lim[1]), num=num_points)
    x = np.log10(e_i_peak / e_i_peak_norm)

    # Central relation and point-wise uncertainty
    y = log_k + m * x
    sigma_y = np.sqrt(sigma_log_k**2 + x**2 * sigma_m**2 + sigma_ext**2)
    if use_average:
        sigma_y = np.mean(sigma_y)
    e_isotropic = (10**y) * e_iso_norm

    # Plot central line
    plt.plot(e_i_peak, e_isotropic, lw=1, alpha=0.45, color="k")

    # Plot confidence bands
    colors = ["#FFD166", "#FF9F43", "#FF6B6B"]
    for i, n_sigma in enumerate(sigmas):
        c = colors[i % len(colors)]
        y_upper, y_lower = y + n_sigma * sigma_y, y - n_sigma * sigma_y
        e_iso_upper, e_iso_lower = (10**y_upper) * e_iso_norm, (10**y_lower) * e_iso_norm

        plt.fill_between(e_i_peak, e_iso_lower, e_iso_upper, color=c, alpha=0.1)
        plt.plot(e_i_peak, e_iso_lower, color=c, ls="--")
        plt.plot(e_i_peak, e_iso_upper, color=c, ls="--")

    # Formatting
    plt.xlabel(r"E$_\text{i,peak}$ [keV]", fontsize=12)
    plt.ylabel(r"E$_\text{iso}$ [erg]", fontsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlim(x_lim)
    plt.ylim(y_lim)


def plot_grbs_over_amati_relationship(
        grb_names: List[str],
        best_model_list,
        redshift_list: List[float],
        marker_list: List[str],
        n_grid: int = 10_000,
        n_sample: int = 10_000,
        seed_number: int = 0,
        unknown_redshift: bool = False,
) -> None:
    """
    Plot GRBs on the Amati plane.
    
    Parameters
    ----------
    grb_names : List[str]
        Names of the GRBs for labeling in the plot.
    best_model_list
        Nested list containing model objects for each GRB.
    redshift_list : List[float]
        Redshift values corresponding to each GRB.
    marker_list  : List[str]
        Marker styles for each GRB on the plot.
    n_grid : int, optional
        Number of grid points for MCMC sampling. Default is 10,000.
    n_sample : int, optional
        Number of samples for Monte Carlo simulations. Default is 10,000.
    seed_number : int, optional
        Random seed number for reproducibility. Default is 0.
    unknown_redshift : bool, optional
        If True, GRBs with unknown redshift are plotted with reduced opacity. Default is False.
    
    Notes
    -----
    The function evaluates E_peak and E_iso (with uncertainties) for each model using MCMC sampling.
    It supports SBPL and other spectral models and plots their median values with error bars on the Amati plane.
    """
    rng = np.random.default_rng(seed_number)

    ep_sc, ei_sc, col = [], [], []
    for index, k in enumerate(best_model_list):
        for index2, m in enumerate(k):
            m_name = m.name
            print(m_name)
            pc = m.get_parameter_set
            pc_names = [i.name for i in pc]
            # print(pc_names)
            cov_ = 0.5 * (m.covariance_matrix_value + m.covariance_matrix_value.T)
            if "sbpl" in m_name.lower():
                new_sample_size = int(1.5 * n_sample)
                vals = pc.get_populated_values(cov_, size=new_sample_size, rng=rng)
                mvd = {}
                for i, v in enumerate(pc_names):
                    mvd[v] = vals[:, i]
                mask = np.logical_and(
                    np.abs((mvd["index1_sbpl"] + mvd["index2_sbpl"] + 4) / (mvd["index1_sbpl"] - mvd["index2_sbpl"]))
                    < 1,
                    mvd["e_break_sbpl"] > 0,
                )
                mvd_filtered = {k: v[mask] for k, v in mvd.items()}

                if mvd_filtered["index1_sbpl"].shape[0] < n_sample:
                    raise ValueError("Not enough samples")

                idx = rng.choice(mvd_filtered["index1_sbpl"].shape[0], size=n_sample, replace=False)

                mvd_n_samples = {k: v[idx] for k, v in mvd_filtered.items()}

                vals = break_e_to_e_peak(index1_sbpl=mvd_n_samples["index1_sbpl"],
                                         index2_sbpl=mvd_n_samples["index2_sbpl"],
                                         break_energy_sbpl=mvd_n_samples["e_break_sbpl"])
                e_iso = mcmc_e_iso_sampler(m, redshift_list[index], n_samples=n_sample, n_grid=n_grid, method=2,
                                           samples=np.array(list(mvd_n_samples.values())).T,
                                           seed_number=seed_number + index2, rng=rng)
            else:
                name_split = m_name.lower().split("_")
                if len(name_split) > 1:
                    name_split = name_split[0] if "BB" in m_name else name_split[1]
                else:
                    name_split = m_name
                vals = pc.get_populated_values(cov_, size=n_sample, rng=rng)
                mvd = {}
                for i, v in enumerate(pc_names):
                    mvd[v] = vals[:, i]
                vals = mvd[f"e_peak_{name_split.lower()}"]

                e_iso = mcmc_e_iso_sampler(m, redshift_list[index], n_samples=n_sample, n_grid=n_grid, method=2,
                                           samples=np.array(list(mvd.values())).T, seed_number=seed_number + index2,
                                           rng=rng)

            e_peak_i = vals * (1 + redshift_list[index])

            p16_e_peak, p50_e_peak, p84_e_peak = np.percentile(e_peak_i, [16, 50, 84])
            p16_e_iso, p50_e_iso, p84_e_iso = np.percentile(e_iso, [16, 50, 84])

            x_err = np.array([[p50_e_peak - p16_e_peak], [p84_e_peak - p50_e_peak]])
            y_err = np.array([[p50_e_iso - p16_e_iso], [p84_e_iso - p50_e_iso]])

            col = (
                "r"
                if m.interval.kind == EpisodeTypes.T90
                else "b" if m.interval.kind in [EpisodeTypes.EX0, EpisodeTypes.EX1] else "g"
            )

            plt.errorbar(
                p50_e_peak,
                p50_e_iso,
                xerr=x_err,
                yerr=y_err,
                # capsize=5,
                fmt=marker_list[index],
                # ms=6,
                label=(
                    f"{grb_names[index] if not unknown_redshift else grb_names[-1]}"
                    if m.interval.kind is EpisodeTypes.T90
                    else ""
                ),
                color=col,
                alpha=0.5 if unknown_redshift else 1,
            )

            ep_sc.append(p50_e_peak)
            ei_sc.append(p50_e_iso)

    if unknown_redshift:
        plt.plot(np.array(ep_sc), np.array(ei_sc), f"{col}--", marker="D", alpha=0.5, ms=0)


def plot_unknown_redshift_grb(
        best_model, grb_name, z_values=(1, 2, 3, 4, 5, 6, 7), n_grid=10_0000, n_sample=10_000, seed_number=0
):
    """Plot the unknown redshift GRB."""
    temp_best = [[best_model]] * len(z_values)
    grb_name = [grb_name]
    plot_grbs_over_amati_relationship(grb_names=grb_name, best_model_list=temp_best, redshift_list=z_values,
                                      marker_list=["D"] * len(z_values), n_grid=n_grid, n_sample=n_sample,
                                      seed_number=seed_number, unknown_redshift=True)
