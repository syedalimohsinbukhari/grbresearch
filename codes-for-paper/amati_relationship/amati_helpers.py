"""Created on Jan 24 02:32:18 2026 — refactored Mar 27 2026"""

from typing import List, Sequence

import numpy as np
from numpy.typing import ArrayLike

from src.grb_research.grb_calculations import mcmc_e_iso_sampler
from src.grb_research.grb_time import EpisodeTypes
from src.grb_research.grb_utils import break_e_to_e_peak

# ---------------------------------------------------------------------------
# Episode visual style — single source of truth
# ---------------------------------------------------------------------------

EPISODE_COLORS: dict[EpisodeTypes, str] = {
    EpisodeTypes.T90: "k",
    EpisodeTypes.TR: "g",
    EpisodeTypes.EX0: "b",
    EpisodeTypes.EX1: "b",
    EpisodeTypes.SP: "r",
}


class EpisodeMarkerResolver:
    """
    Maps an episode interval to a matplotlib marker.

    T90 — GRB-specific marker passed at construction (the only dimension
            that differs across GRBs).
    EX0 — star ("*")
    EX1 — pentagon ("p")
    TR n — integer marker from TR_MARKERS, indexed by interval.index
    SP n — shape from SP_MARKERS, indexed by interval.index

    Parameters
    ----------
    t90_marker : str
        Marker to use for T90 episodes of this GRB.
    """

    TR_MARKERS: List = ["v", "<", ">", "h", "H", "8", "d"]
    EX_MARKERS: List[str] = ["*", "p"]
    SP_MARKERS: List[str] = ["s", "D", "P"]

    def __init__(self, t90_marker: str) -> None:
        self.t90_marker = t90_marker

    def resolve(self, interval) -> str:
        """Return the marker for *interval* based on its kind and index."""
        kind = interval.kind
        if kind is EpisodeTypes.T90:
            return self.t90_marker
        if kind is EpisodeTypes.EX0:
            return self.EX_MARKERS[0]
        if kind is EpisodeTypes.EX1:
            return self.EX_MARKERS[1]
        if kind is EpisodeTypes.TR:
            return self.TR_MARKERS[interval.index % len(self.TR_MARKERS)]
        if kind is EpisodeTypes.SP:
            return self.SP_MARKERS[interval.index % len(self.SP_MARKERS)]
        raise ValueError(f"Unrecognised EpisodeType: {kind}")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _episode_label(m) -> str:
    """Produce the legend label for a single model's episode."""
    if m.interval.kind in (EpisodeTypes.T90, EpisodeTypes.EX0, EpisodeTypes.EX1):
        return str(m.interval.kind)
    return f"{m.interval.kind}{m.interval.index}"


def _compute_ep_eiso(
    m, redshift: float, n_sample: int, n_grid: int, seed_number: int, rng
) -> tuple[ArrayLike, ArrayLike]:
    """
    Draw posterior samples of (E_peak_intrinsic, E_iso) for a single model.

    Returns
    -------
    ep_samples : array of shape (n_sample,)
        Intrinsic (observer-frame) E_peak samples in keV.
    eiso_samples : array of shape (n_sample,)
        E_iso samples in erg.
    """
    m_name = m.name
    pc = m.get_parameter_set
    pc_names = [p.name for p in pc]
    cov_ = 0.5 * (m.covariance_matrix_value + m.covariance_matrix_value.T)

    if "sbpl" in m_name.lower():
        raw = pc.get_populated_values(cov_, size=int(1.5 * n_sample), rng=rng)
        mvd = {v: raw[:, i] for i, v in enumerate(pc_names)}

        mask = np.logical_and(
            np.abs((mvd["index1_sbpl"] + mvd["index2_sbpl"] + 4) / (mvd["index1_sbpl"] - mvd["index2_sbpl"])) < 1,
            mvd["e_break_sbpl"] > 0,
        )
        mvd_f = {k: v[mask] for k, v in mvd.items()}
        if mvd_f["index1_sbpl"].shape[0] < n_sample:
            raise ValueError("Not enough valid SBPL samples after physical filter.")

        idx = rng.choice(mvd_f["index1_sbpl"].shape[0], size=n_sample, replace=False)
        mvd_s = {k: v[idx] for k, v in mvd_f.items()}

        ep_samples = break_e_to_e_peak(
            index1_sbpl=mvd_s["index1_sbpl"], index2_sbpl=mvd_s["index2_sbpl"], break_energy_sbpl=mvd_s["e_break_sbpl"]
        )
        samples_arr = np.array(list(mvd_s.values())).T

    else:
        name_split = m_name.lower().split("_")
        if len(name_split) > 1:
            name_split = name_split[0] if "BB" in m_name else name_split[1]
        else:
            name_split = m_name

        raw = pc.get_populated_values(cov_, size=n_sample, rng=rng)
        mvd = {v: raw[:, i] for i, v in enumerate(pc_names)}
        ep_samples = mvd[f"e_peak_{name_split.lower()}"]
        samples_arr = np.array(list(mvd.values())).T

    eiso_samples = mcmc_e_iso_sampler(
        m, redshift, n_samples=n_sample, n_grid=n_grid, method=2, samples=samples_arr, seed_number=seed_number, rng=rng
    )

    ep_intrinsic = ep_samples * (1 + redshift)
    return ep_intrinsic, eiso_samples


def _plot_model_point(
    m,
    redshift: float,
    marker: str,
    color: str,
    n_grid: int,
    n_sample: int,
    seed_number: int,
    rng,
    alpha: float,
    label: str,
    axis,
) -> tuple[float, float]:
    """
    Compute and draw a single (E_peak, E_iso) point with error bars.

    Returns
    -------
    p50_ep, p50_eiso : float
        Median values, useful for building redshift tracks.
    """
    ep_s, ei_s = _compute_ep_eiso(m, redshift, n_sample, n_grid, seed_number, rng)

    p16_ep, p50_ep, p84_ep = np.percentile(ep_s, [16, 50, 84])
    p16_ei, p50_ei, p84_ei = np.percentile(ei_s, [16, 50, 84])

    x_err = np.array([[p50_ep - p16_ep], [p84_ep - p50_ep]])
    y_err = np.array([[p50_ei - p16_ei], [p84_ei - p50_ei]])

    axis.scatter(p50_ep, p50_ei, marker=marker, s=50, color=color, alpha=alpha, label=label, zorder=3)
    axis.errorbar(p50_ep, p50_ei, xerr=x_err, yerr=y_err, ms=0, color=color, alpha=alpha, zorder=2)

    return p50_ep, p50_ei


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def amati_relationship_dirirsa2019(
    e_iso_norm: float = 1e52,
    e_i_peak_norm: float = 950.0,
    k: float = 1.67,
    sigma_k: float = 0.16,
    m: float = 1.16,
    sigma_m: float = 0.37,
    sigma_ext: float = 0.47,
    sigmas: Sequence[int] = (1, 2, 3),
    x_lim: tuple = (10, 1e5),
    y_lim: tuple = (1e50, 1e55),
    num_points: int = 1_000,
    use_average: bool = False,
    axis=None,
) -> None:
    """Plot the Amati relation with confidence bands (FanaDirirsa et al. 2019)."""
    if axis is None:
        raise ValueError("An axis must be provided.")

    e_i_peak = np.logspace(np.log10(x_lim[0]), np.log10(x_lim[1]), num=num_points)
    x = np.log10(e_i_peak / e_i_peak_norm)
    y = k + m * x
    sigma_y = np.sqrt(sigma_k**2 + x**2 * sigma_m**2 + sigma_ext**2)

    if use_average:
        sigma_y = np.mean(sigma_y)
    e_isotropic = (10**y) * e_iso_norm

    axis.loglog(e_i_peak, e_isotropic, lw=1, alpha=0.45, color="k")

    band_colors = ["#FFD166", "#FF9F43", "#FF6B6B"]
    for i, n_sigma in enumerate(sigmas):
        c = band_colors[i % len(band_colors)]
        e_upper = (10 ** (y + n_sigma * sigma_y)) * e_iso_norm
        e_lower = (10 ** (y - n_sigma * sigma_y)) * e_iso_norm
        axis.fill_between(e_i_peak, e_lower, e_upper, color=c, alpha=0.1)
        axis.plot(e_i_peak, e_lower, color=c, ls="--")
        axis.plot(e_i_peak, e_upper, color=c, ls="--")

    axis.set_xlim(x_lim)
    axis.set_ylim(y_lim)


def plot_grbs_over_amati_relationship(
    best_model_list,
    redshift_list: List[float],
    t90_marker_list: List[str],
    n_grid: int = 10_000,
    n_sample: int = 10_000,
    seed_number: int = 0,
    alpha: float = 1.0,
    axis=None,
) -> None:
    """
    Plot one or more GRBs on the Amati plane.

    Parameters
    ----------
    best_model_list : list of ModelSet
        One ModelSet per GRB; each ModelSet is an iterable of Model objects.
    redshift_list : list of float
        Redshift for each GRB, aligned with best_model_list.
    t90_marker_list : list of str
        Matplotlib marker string for T90 of each GRB (the only per-GRB
        marker dimension). All other episode types use fixed global markers
        defined in EpisodeMarkerResolver.
    n_grid : int
        Grid resolution for E_iso integration.
    n_sample : int
        Posterior sample count.
    seed_number : int
        Base RNG seed; incremented per model to keep runs reproducible.
    alpha : float
        Scatter / errorbar opacity.
    axis : matplotlib Axes
        Target axes object. Required.
    """
    if axis is None:
        raise ValueError("An axis must be provided.")

    rng = np.random.default_rng(seed_number)

    for index, (models, redshift, t90_marker) in enumerate(zip(best_model_list, redshift_list, t90_marker_list)):
        resolver = EpisodeMarkerResolver(t90_marker=t90_marker)
        for index2, m in enumerate(models):
            _plot_model_point(
                m=m,
                redshift=redshift,
                marker=resolver.resolve(m.interval),
                color=EPISODE_COLORS[m.interval.kind],
                n_grid=n_grid,
                n_sample=n_sample,
                seed_number=seed_number + index2,
                rng=rng,
                alpha=alpha,
                label=_episode_label(m),
                axis=axis,
            )


def plot_unknown_redshift_grb(
    models,
    t90_marker: str,
    z_values: Sequence[float] = (1, 3, 5, 7),
    n_grid: int = 10_000,
    n_sample: int = 10_000,
    seed_number: int = 0,
    axis=None,
) -> None:
    """
    Plot a GRB with unknown redshift across several assumed z values.

    For each episode in *models*, four points are drawn (one per entry in
    z_values) and connected by a dashed line to show the locus of the burst
    on the Amati plane as a function of assumed redshift. Each episode uses
    the same marker scheme as in plot_grbs_over_amati_relationship so the
    reader can match episodes across panels.

    Parameters
    ----------
    models : ModelSet
        All episode models for the unknown-redshift GRB.
    t90_marker : str
        Matplotlib marker for the T90 episode of this GRB.
    z_values : sequence of float
        Redshift values to evaluate. Defaults to (1, 3, 5, 7).
    n_grid, n_sample, seed_number : int
        Passed through to the sampler.
    axis : matplotlib Axes
        Target axes object. Required.
    """
    if axis is None:
        raise ValueError("An axis must be provided.")

    rng = np.random.default_rng(seed_number)
    resolver = EpisodeMarkerResolver(t90_marker=t90_marker)

    for ep_idx, m in enumerate(models):
        color = EPISODE_COLORS[m.interval.kind]
        marker = resolver.resolve(m.interval)

        ep_track: List[float] = []
        ei_track: List[float] = []

        for z_idx, z in enumerate(z_values):
            # Label only on the first redshift so the legend has one entry
            # per episode, not one per (episode × z).
            label = _episode_label(m) if z_idx == 0 else ""

            ep, ei = _plot_model_point(
                m=m,
                redshift=z,
                marker=marker,
                color=color,
                n_grid=n_grid,
                n_sample=n_sample,
                seed_number=seed_number + ep_idx * len(z_values) + z_idx,
                rng=rng,
                alpha=0.75,
                label=label,
                axis=axis,
            )
            ep_track.append(ep)
            ei_track.append(ei)

        # Connect the z-track for this episode on the correct axis
        axis.plot(ep_track, ei_track, ls="--", color=color, alpha=0.5, zorder=1)
