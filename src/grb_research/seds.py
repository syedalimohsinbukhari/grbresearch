"""Created on Aug 30 15:14:03 2025"""

from typing import Optional, Tuple

import numpy as np
from matplotlib import pyplot as plt
from uncertainties import correlated_values, unumpy

from . import GRB_COLORS, model_n_pars


def get_variance(jacobian_stack, cov):
    return np.einsum("ij,jk,ik->i", jacobian_stack, cov, jacobian_stack, optimize=True)


def powerlaw(energy, amp, e_piv, index1):
    return amp * (energy / e_piv)**index1


def smoothly_broken_power_law(energy, amp, e_piv, index1, break_energy, delta, index2):
    m = (index2 - index1) / 2
    b = (index1 + index2) / 2

    a = unumpy.log10(energy / break_energy) / delta
    beta = m * delta * unumpy.log(0.5 * (unumpy.exp(a) + unumpy.exp(-a)))

    a_piv = unumpy.log10(e_piv / break_energy) / delta
    beta_piv = m * delta * unumpy.log(0.5 * (unumpy.exp(a_piv) + unumpy.exp(-a_piv)))

    return amp * (energy / e_piv)**b * 10.0**(beta - beta_piv)


def band_function(energy, amp, e_peak, index1, index2):
    e_piv = 100.
    i1_minus_i2 = index1 - index2
    break_ = e_peak / (index1 + 2.0)
    transition_condition = i1_minus_i2 * break_

    f1 = _cpl_one(energy=energy, e_peak=e_peak, index1=index1, e_piv=e_piv)

    f21 = (i1_minus_i2 * break_) / e_piv
    f2 = f21**i1_minus_i2 * unumpy.exp(-i1_minus_i2) * _pl_one(energy=energy, e_piv=e_piv, index1=index2)

    return amp * np.where(energy < transition_condition, f1, f2)


def cutoff_powerlaw(energy, amp, e_peak, index1, e_piv):
    exp_ = -energy * (2 + index1)
    return amp * _pl_one(energy=energy, e_piv=e_piv, index1=index1) * unumpy.exp(exp_ / e_peak)


def black_body(energy, amp, temperature):
    kt_clip = np.clip(a=energy / temperature, a_min=0, a_max=325)
    return amp * energy**2 / (unumpy.exp(kt_clip) - 1)


def get_value(fit_file, n_parameters, full_cov, return_errors: bool = False):
    """
    Extract parameter values (and optionally errors) from the FITS file.

    - Value is stored at [0][0]
    - Error is stored at [0][1]

    If return_errors is False (default), returns a list of uncertainties.ufloat via
    correlated_values using full covariance. This preserves error correlations in
    downstream computations.

    If return_errors is True, returns a tuple (values, errors) where both are numpy arrays
    taken directly from the FITS (per-parameter 1-sigma errors), with 0.0 for frozen parameters.
    """
    values = [fit_file[2].data[f"PARAM{i}"][0][0] for i in range(n_parameters)]
    errors = [fit_file[2].data[f"PARAM{i}"][0][1] for i in range(n_parameters)]

    if return_errors:
        return np.array(object=values, dtype=float), np.array(object=errors, dtype=float)

    return correlated_values(nom_values=values, covariance_mat=full_cov)


def model_pl(x, model_values, model_string: str):
    model_string = model_string.lower()
    model_dict = {"cpl": cutoff_powerlaw, "band": band_function, "sbpl": smoothly_broken_power_law, "bb": black_body}
    model_init = model_string.split("_")[0] if model_string != "pl_bb" else model_string.split("_")[1]

    pl_ = powerlaw(x, *model_values[: model_n_pars["pl"]])
    model_ = model_dict[model_init](x, *model_values[model_n_pars["pl"]:])

    return pl_, model_, pl_ + model_


def model_bb(x, model_values, model_string: str):
    model_string = model_string.lower()
    model_dict = {"pl": powerlaw, "cpl": cutoff_powerlaw, "band": band_function, "sbpl": smoothly_broken_power_law}
    model_init = model_string.split("_")[0]

    model_ = model_dict[model_init](x, *model_values[: model_n_pars[model_init]])
    bb_ = black_body(x, *model_values[model_n_pars[model_init]:])

    return model_, bb_, model_ + bb_


def pl_model_bb(x, model_values, model_string: str):
    model_string = model_string.lower()
    model_dict = {"cpl": cutoff_powerlaw, "band": band_function, "sbpl": smoothly_broken_power_law}
    model_init = model_string.split("_")[0]

    pl_ = powerlaw(x, *model_values[: model_n_pars["pl"]])
    model_ = model_dict[model_init](x, *model_values[model_n_pars["pl"]: -model_n_pars["bb"]])
    bb_ = black_body(x, *model_values[-model_n_pars["bb"]:])

    return pl_, model_, bb_, pl_ + model_ + bb_


def plot_model(x, model_values, model_strings, styles, plot_labels=None,
               x_lims=None, x_label=None, y_lims=None, y_label=None, axis=None, use_ergs=False):
    kev_to_ergs = 1.60217662e-9 if use_ergs else 1.0
    if axis is None:
        f, ax = plt.subplots(figsize=(8, 6))
    else:
        ax = axis

    # -- convert keV to ergs if requested
    max_y = 1
    model_values = _swap(model_values)
    model_strings = _swap(model_strings)
    styles = _swap(styles)

    plot_labels = model_strings if plot_labels is None else plot_labels

    for index, (mv, label, style) in enumerate(zip(model_values, plot_labels, styles)):
        y_nom = unumpy.nominal_values(mv)
        y_err = unumpy.std_devs(mv)

        y_plot = y_nom * kev_to_ergs * x**2
        y_upper = (y_nom + y_err) * kev_to_ergs * x**2
        y_lower = (y_nom - y_err) * kev_to_ergs * x**2

        max_y = max(max_y, y_upper.max())
        max_y = max_y * kev_to_ergs if use_ergs else max_y

        # color = 'k' if index == 0 else GRB_COLORS[label.lower()]
        color = GRB_COLORS[model_strings[index].lower()]
        ax.loglog(x, y_plot, style, color=color, label=label)
        ax.fill_between(x=x, y1=y_lower, y2=y_upper, color=color, alpha=0.2)

    ax.set_xlim(x_lims)
    ax.set_ylim(y_lims)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(alpha=0.25, ls="--")
    ax.legend(loc="best")


def _swap(list_of_values):
    if isinstance(list_of_values, tuple):
        list_of_values = list(list_of_values)
    list_of_values.insert(0, list_of_values[-1])
    list_of_values = list_of_values[:-1]
    return list_of_values


def plot_single_model(x, model_values, model_string: str, plot_labels: str = None, x_lims: Optional[Tuple] = None,
                      x_label: Optional[str] = None, y_label: Optional[str] = None, use_ergs: bool = False, axis=None):
    plot_model(x=x, model_values=[model_values], model_strings=[model_string.replace("_", "+").upper()], styles=["-"],
               plot_labels=plot_labels, x_lims=x_lims, x_label=x_label, y_label=y_label, axis=axis, use_ergs=use_ergs)


def plot_double_model(x, model_values, model_string, plot_labels=None, x_lims=None, x_label=None, y_label=None,
                      axis=None, use_ergs=False):
    m1, m2 = model_string.split("_")
    if m2 == 'pl':
        m1, m2 = m2, m1

    m_string = [m1.upper(), m2.upper(), model_string.replace("_", "+").upper()]
    styles = ["--", "--", "-"]

    plot_model(x=x, model_values=model_values, model_strings=m_string, styles=styles, plot_labels=plot_labels,
               x_lims=x_lims, x_label=x_label, y_label=y_label, axis=axis, use_ergs=use_ergs)


def plot_triple_model(x, model_values, model_string, plot_labels=None, x_lims=None, x_label=None, y_label=None,
                      use_ergs: bool = False):
    m1, m2, m3 = model_string.split("_")

    m_string = [m2.upper(), m1.upper(), m3.upper(), model_string.replace("_", "+").upper()]
    styles = ["--", "--", "--", "-"]

    plot_model(x=x, model_values=model_values, model_strings=m_string, styles=styles, plot_labels=plot_labels,
               x_lims=x_lims, x_label=x_label, y_label=y_label, use_ergs=use_ergs)


# def preamble(energy, ep_folder_path, model_string, err_check=False, par_constraint=0.4, arg_dict=None):
#     if arg_dict is None:
#         arg_dict = {}
#     x_lim = arg_dict.get("x_lim", (10, 1e7))
#
#     x_label = arg_dict.get("x_label", "Energy (keV)")
#     y_label = arg_dict.get("y_label", "Flux (erg cm$^{-2}$ s$^{-1}$ keV$^{-1}$)")
#
#     model_dict = {"pl": powerlaw, "bb": black_body, "cpl": cutoff_powerlaw, "band": band_function,
#                   "sbpl": smoothly_broken_power_law}
#
#     plot_dispatch = {1: plot_single_model, 2: plot_double_model, 3: plot_triple_model}
#
#     fit_path = f"{ep_folder_path}/{model_string.upper()}.fit"
#
#     ff = fits.open(fit_path)
#     n_params = model_n_pars[model_string]
#     cov_ = ff[2].data["COVARMAT"][0]
#     params = get_value(fit_file=ff, n_parameters=n_params, full_cov=cov_)
#
#     parts = model_string.split("_")
#     n_parts = len(parts)
#
#     if n_parts not in plot_dispatch:
#         raise ValueError(f"Unsupported model type: {model_string}")
#
#     models_to_plot = []
#
#     model_values = get_value(fit_file=ff, n_parameters=model_n_pars[model_string], full_cov=ff[2].data["COVARMAT"][0])
#
#     if n_parts == 1:
#         model = model_dict[parts[0]](energy, *params)
#         models_to_plot = model
#     elif n_parts == 2:
#         if parts[1] == "pl":
#             c1, c2, model = model_pl(x=energy, model_values=model_values, model_string=model_string)
#             c1, c2 = c2, c1
#         elif parts[1] == "bb":
#             c1, c2, model = model_bb(x=energy, model_values=model_values, model_string=model_string)
#         else:
#             raise ValueError(f"Unsupported model type: {model_string}")
#         models_to_plot = [c1, c2, model]
#     elif n_parts == 3:
#         c1, c2, c3, model = pl_model_bb(x=energy, model_values=model_values, model_string=model_string)
#         models_to_plot = [c2, c1, c3, model]
#
#     plot_dispatch[n_parts](
#         x=energy,
#         model_values=models_to_plot,
#         model_string=model_string,
#         x_lims=x_lim,
#         x_label=x_label,
#         y_label=y_label,
#     )
#
#     if err_check:
#         nominal = np.array([p.nominal_value for p in params])
#         errors = np.array([p.std_dev for p in params])
#         rel_unc = np.abs(errors / nominal) * 100
#
#         mask = errors <= par_constraint * np.abs(nominal)
#         print("\nParameter Error Check:\n")
#         for i, (v, e, r, ok) in enumerate(zip(nominal, errors, rel_unc, mask)):
#             print(f"Param {i}: {v:.4g} ± {e:.4g} ({r:.1f}%) -> {'OK' if ok else 'HIGH UNCERTAINTY'}")
#         print(f"Summary: {np.sum(mask)}/{len(mask)} parameters within {par_constraint * 100:.0f}%")
#
#     ff.close()
#     plt.savefig(f"{ep_folder_path}/{model_string.upper()}.png")
#     print(f"[SAVED] as {ep_folder_path}/{model_string.upper()}.png")
#     plt.close()


###############################################################################
# AUXILIARY FUNCTIONS
###############################################################################

def _pl_one(energy, e_piv, index1):
    return (energy / e_piv)**index1


def _cpl_one(energy, e_peak, index1, e_piv):
    return cutoff_powerlaw(energy=energy, amp=1, e_peak=e_peak, index1=index1, e_piv=e_piv)
