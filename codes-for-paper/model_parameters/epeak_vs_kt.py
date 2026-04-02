"""Created on Apr 01 14:02:04 2026"""

import json
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from src.grb_research import GRBCatalog, find_project_root
from src.grb_research.grb_constants import (
    short_to_long, LEGEND_FONT_SIZE, LABEL_FONT_SIZE,
)
from src.grb_research.grb_time import EpisodeTypes
from src.grb_research.grb_utils import break_e_to_e_peak

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"
grb_name = ["080916C", "110721A"]

with open(result_file, "r") as f:
    data = json.load(f)

grb = GRBCatalog.from_iterable(grb_list=grb_name, data=data, name_mapping=short_to_long)

grb_full_name = [short_to_long[i] for i in grb_name]

t90_080916C = grb[grb_full_name[0]].get_model('SBPL_BB', interval=EpisodeTypes.T90)
ex0_080916C = grb[grb_full_name[0]].get_model('BAND_BB', interval=EpisodeTypes.EX0)
tr0_080916C = grb[grb_full_name[0]].get_model('BAND_BB', interval=EpisodeTypes.TR, tr_index=0)
tr1_080916C = grb[grb_full_name[0]].get_model('BAND_BB', interval=EpisodeTypes.TR, tr_index=1)
tr2_080916C = grb[grb_full_name[0]].get_model('SBPL_BB', interval=EpisodeTypes.TR, tr_index=2)

t90_110721A = grb[grb_full_name[1]].get_model('BAND_BB', interval=EpisodeTypes.T90)
ex0_110721A = grb[grb_full_name[1]].get_model('BAND_BB', interval=EpisodeTypes.EX0)
tr0_110721A = grb[grb_full_name[1]].get_model('BAND_BB', interval=EpisodeTypes.TR, tr_index=0)
tr1_110721A = grb[grb_full_name[1]].get_model('BAND_BB', interval=EpisodeTypes.TR, tr_index=1)
sp0_110721A = grb[grb_full_name[1]].get_model('BAND_BB', interval=EpisodeTypes.SP, tr_index=0)

from scipy.odr import ODR, Model, RealData


def linear(params, x):
    return params[0] * x + params[1]


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

    TR_MARKERS: List = ["v", "<", ">", "^", "d", "8", "h"]
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


def kt_extractor(model: Model):
    for i in model.parameters:
        if i.name.startswith("kt"):
            return i.error, i.value, i.error
    return None


def epeak_extractor(model: Model):
    for i in model.parameters:
        if i.name.startswith("e_peak"):
            return i.error, i.value, i.error
    return None


def sbpl_mask(index1_sbpl, index2_sbpl, e_break_sbpl):
    return np.logical_and(
        np.abs((index1_sbpl + index2_sbpl + 4) / (index1_sbpl - index2_sbpl)) < 1,
        e_break_sbpl > 0,
    )


def convert_sbpl_to_band(model: Model, n_sample=10_000, seed=None, rng=None):
    if seed is not None:
        rng = np.random.default_rng(seed)

    parameters = model.parameters
    cov_matrix = model.covariance_matrix_value
    raw = model.get_parameter_set.get_populated_values(cov_matrix, size=int(1.5 * n_sample), rng=rng)

    mvd = {v: raw[:, i] for i, v in enumerate([p.name for p in parameters])}

    mask = sbpl_mask(mvd["index1_sbpl"], mvd["index2_sbpl"], mvd["e_break_sbpl"])
    mvd_f = {k: v[mask] for k, v in mvd.items()}
    if mvd_f["index1_sbpl"].shape[0] < n_sample:
        raise ValueError("Not enough valid SBPL samples after physical filter.")

    idx = rng.choice(mvd_f["index1_sbpl"].shape[0], size=n_sample, replace=False)
    mvd_s = {k: v[idx] for k, v in mvd_f.items()}

    ep_samples = break_e_to_e_peak(
        index1_sbpl=mvd_s["index1_sbpl"], index2_sbpl=mvd_s["index2_sbpl"], break_energy_sbpl=mvd_s["e_break_sbpl"]
    )
    p = np.percentile(ep_samples, [16, 50, 84])
    return p[1] - p[0], p[1], p[2] - p[1]


# for model_ in ['SBPL_BB', 'BAND_BB', 'BAND_BB', 'BAND_BB', 'SBPL_BB']:
#     print(f'{model_}: {convert_sbpl_to_band(t90_080916C, seed=1234)}')
# print(f'{convert_sbpl_to_band(t90_080916C, seed=1234)}')

kt_values = []
sbpl_ep_values, ep_values = [], []
marker = []
for model_ in [t90_080916C, ex0_080916C, tr0_080916C, tr1_080916C, tr2_080916C]:
    model_: Model = model_
    kt_values.append(kt_extractor(model_))
    if model_.name == 'SBPL_BB':
        ep_values.append(convert_sbpl_to_band(model_, seed=1234))
    elif 'BAND' in model_.name or 'CPL' in model_.name:
        ep_values.append(epeak_extractor(model_))
    else:
        raise ValueError(">" + model_.name + "< is not expected for this GRB.")
    marker.append(EpisodeMarkerResolver(t90_marker="o").resolve(model_.interval))

kt_values, ep_values = np.array(kt_values), np.array(ep_values)

f, ax = plt.subplots(2, 1, figsize=(6, 8), sharex=True)

bb_status = ["full", "full", "full", "kT_only", "full"]

for kt, ep, mkr, model_, status in zip(kt_values, ep_values, marker,
                                       [t90_080916C, ex0_080916C, tr0_080916C, tr1_080916C, tr2_080916C],
                                       bb_status):
    idx = "" if model_.interval.index is None else f'{model_.interval.index}'
    label = f'{model_.interval.kind.value}{idx}' + r"$_\text{" + model_.name.replace("_", "+") + r"}$"
    # print(f"{kt[0]=} {kt[1]=} {kt[2]=}")
    # print(f"{ep[0]=} {ep[1]=} {ep[2]=}")
    ax[0].errorbar(
        kt[1],
        ep[1],
        xerr=[[kt[0]], [kt[2]]],
        yerr=[[ep[0]], [ep[2]]],
        fmt=mkr,
        mfc='w' if status == "kT_only" else None,
        ms=8,
        capsize=5,
        color="r" if model_.interval.is_t90 else "g" if model_.interval.is_tr else "k" if model_.interval.is_sp else "b",
        linestyle="--" if status == "kT_only" else "-",
        label=label,
    )

x, y = kt_values, ep_values
mask_ = [x == "full" for x in bb_status]

kt_centers = x[:, 1][mask_]
ep_centers = y[:, 1][mask_]

kt_errors_lo = x[:, 0][mask_]
kt_errors_hi = x[:, 2][mask_]

ep_errors_lo = y[:, 0][mask_]
ep_errors_hi = y[:, 2][mask_]

kt_errors = 0.5 * (kt_errors_lo + kt_errors_hi)
ep_errors = 0.5 * (ep_errors_lo + ep_errors_hi)

data = RealData(kt_centers, ep_centers, sx=kt_errors, sy=ep_errors)
odr = ODR(data, Model(linear), beta0=[1, 1])
result = odr.run()
kt_fine = np.linspace(kt_centers.min(), kt_centers.max(), 200)

# Full uncertainty propagation
cov = result.cov_beta  # 2x2 covariance matrix
y_fit = linear(result.beta, kt_fine)
y_var = (
    kt_fine ** 2 * cov[0, 0] +  # slope variance
    cov[1, 1] +  # intercept variance
    2 * kt_fine * cov[0, 1]  # covariance term (can be negative)
)

y_err = np.sqrt(np.maximum(y_var, 0))

ax[0].plot(kt_fine, y_fit, color="#8B0000", ls='-')
ax[0].fill_between(kt_fine,
                   y_fit - y_err,
                   y_fit + y_err,
                   color="#8B0000", alpha=0.2)

ax[0].annotate(
    f"$E_{{\\rm peak}} = {result.beta[0]:+.1f}({result.sd_beta[0]:.1f})"
    f"\\cdot kT {result.beta[1]:+.1f}({result.sd_beta[1]:.1f})$",
    xy=(0.05, 0.92), xycoords='axes fraction',
    fontsize=LEGEND_FONT_SIZE, color="#8B0000"
)

kt_values = []
sbpl_ep_values, ep_values = [], []
marker = []
for model_ in [t90_110721A, ex0_110721A, tr0_110721A, tr1_110721A, sp0_110721A]:
    model_: Model = model_
    kt_values.append(kt_extractor(model_))
    if model_.name == 'SBPL_BB':
        ep_values.append(convert_sbpl_to_band(model_, seed=1234))
    elif 'BAND' in model_.name or 'CPL' in model_.name:
        ep_values.append(epeak_extractor(model_))
    else:
        raise ValueError(">" + model_.name + "< is not expected for this GRB.")
    marker.append(EpisodeMarkerResolver(t90_marker="o").resolve(model_.interval))

kt_values, ep_values = np.array(kt_values), np.array(ep_values)
bb_status = ["full", "kT_only", "kT_only", "full", "full"]

for kt, ep, mkr, model_, status in zip(kt_values, ep_values, marker,
                                       [t90_110721A, ex0_110721A, tr0_110721A, tr1_110721A, sp0_110721A],
                                       bb_status):
    idx = "" if model_.interval.index is None else f'{model_.interval.index}'
    label = f'{model_.interval.kind.value}{idx}' + r"$_\text{" + model_.name.replace("_", "+") + r"}$"
    # print(f"{kt[0]=} {kt[1]=} {kt[2]=}")
    # print(f"{ep[0]=} {ep[1]=} {ep[2]=}")
    ax[1].errorbar(
        kt[1],
        ep[1],
        xerr=[[kt[0]], [kt[2]]],
        yerr=[[ep[0]], [ep[2]]],
        fmt=mkr,
        mfc='w' if status == "kT_only" else None,
        ms=8,
        capsize=5,
        color="r" if model_.interval.is_t90 else "g" if model_.interval.is_tr else "k" if model_.interval.is_sp else "b",
        linestyle="--" if status == "kT_only" else "-",
        label=label,
    )

x, y = kt_values, ep_values

kt_centers = x[:, 1]
ep_centers = y[:, 1]

kt_errors_lo = x[:, 0]
kt_errors_hi = x[:, 2]

ep_errors_lo = y[:, 0]
ep_errors_hi = y[:, 2]

kt_errors = 0.5 * (kt_errors_lo + kt_errors_hi)
ep_errors = 0.5 * (ep_errors_lo + ep_errors_hi)

data = RealData(kt_centers, ep_centers, sx=kt_errors, sy=ep_errors)
odr = ODR(data, Model(linear), beta0=[1, 1])
result = odr.run()

kt_fine = np.linspace(kt_centers.min(), kt_centers.max(), 200)

# Full uncertainty propagation
cov = result.cov_beta  # 2x2 covariance matrix
y_fit = linear(result.beta, kt_fine)
y_var = (
    kt_fine ** 2 * cov[0, 0] +  # slope variance
    cov[1, 1] +  # intercept variance
    2 * kt_fine * cov[0, 1]  # covariance term (can be negative)
)

y_err = np.sqrt(np.maximum(y_var, 0))

ax[1].plot(kt_fine, y_fit, color="#8B0000", ls='-')
ax[1].fill_between(kt_fine,
                   y_fit - y_err,
                   y_fit + y_err,
                   color="#8B0000", alpha=0.2)

ax[1].annotate(
    f"$E_{{\\rm peak}} = {result.beta[0]:+.1f}({result.sd_beta[0]:.1f})"
    f"\\cdot kT {result.beta[1]:+.1f}({result.sd_beta[1]:.1f})$",
    xy=(0.05, 0.92), xycoords='axes fraction',
    fontsize=LEGEND_FONT_SIZE, color="#8B0000"
)

ax[1].set_xlabel("kT [keV]", fontsize=LABEL_FONT_SIZE)
[i.set_ylabel(r"$E_\text{peak}$ [keV]", fontsize=LABEL_FONT_SIZE) for i in ax]
[i.legend(fontsize=LEGEND_FONT_SIZE) for i in ax]
[i.grid(True, which="both", alpha=0.5, ls="--") for i in ax]
f.tight_layout()
# plt.show()

for i in ['png', 'pdf']:
    plt.savefig(f"epeak_vs_kt.{i}", dpi=300)
plt.close()
