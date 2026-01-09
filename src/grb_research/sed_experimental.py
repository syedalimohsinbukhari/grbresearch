"""Created on Oct 08 12:17:32 2025"""

import numpy as np

from .grb_constants import model_n_pars


###############################################################################
# GRB FUNCTIONS
###############################################################################


def powerlaw(energy, amp, e_piv, index1):
    return amp * (energy / e_piv) ** index1


def smoothly_broken_power_law(energy, amp, e_piv, index1, break_energy, delta, index2):
    m = (index2 - index1) / 2
    b = (index1 + index2) / 2

    a = np.log10(energy / break_energy) / delta
    beta = m * delta * np.log(0.5 * (np.exp(a) + np.exp(-a)))

    a_piv = np.log10(e_piv / break_energy) / delta
    beta_piv = m * delta * np.log(0.5 * (np.exp(a_piv) + np.exp(-a_piv)))

    return amp * (energy / e_piv) ** b * 10.0 ** (beta - beta_piv)


def band_function(energy, amp, e_peak, index1, index2):
    e_piv = 100.0
    i1_minus_i2 = index1 - index2
    break_ = e_peak / (index1 + 2.0)
    transition_condition = i1_minus_i2 * break_

    f1 = _cpl_one(energy=energy, e_peak=e_peak, index1=index1, e_piv=e_piv)

    f21 = (i1_minus_i2 * break_) / e_piv
    f2 = f21**i1_minus_i2 * np.exp(-i1_minus_i2) * _pl_one(energy=energy, e_piv=e_piv, index1=index2)

    return amp * np.where(energy < transition_condition, f1, f2)


def cutoff_powerlaw(energy, amp, e_peak, index1, e_piv):
    exp_ = -energy * (2 + index1)
    return amp * _pl_one(energy=energy, e_piv=e_piv, index1=index1) * np.exp(exp_ / e_peak)


def black_body(energy, amp, temperature):
    return amp * energy**2 / np.expm1(energy / temperature)


##############################################################################
# ERROR PROPAGATED FUNCTIONS
##############################################################################


def _pl_grads(energy, amp, e_piv, index1):
    f = powerlaw(energy=energy, amp=amp, e_piv=e_piv, index1=index1)
    df_d1 = f / amp
    df_d2 = f * 0
    df_d3 = f * np.log(energy / e_piv)
    return np.array([df_d1, df_d2, df_d3])


def powerlaw_errors(energy, amp, e_piv, index1, cov, correlated=True):
    n_params = model_n_pars["pl"]
    grads = _pl_grads(energy=energy, amp=amp, e_piv=e_piv, index1=index1)
    return give_errors(cov=cov, grads=grads, n_params=n_params, correlated=correlated)


def smoothly_broken_power_law_errors(energy, amp, e_piv, index1, break_energy, delta, index2, cov, correlated=True):
    n_param = model_n_pars["sbpl"]
    grads = _sbpl_grads(
        energy=energy, amp=amp, e_piv=e_piv, index1=index1, break_energy=break_energy, delta=delta, index2=index2
    )
    return give_errors(cov=cov, grads=grads, n_params=n_param, correlated=correlated)


def _sbpl_grads(energy, amp, e_piv, index1, break_energy, delta, index2):
    log_of_10 = np.log(10.0)
    factor_a = np.log(e_piv / break_energy) / (delta * log_of_10)
    factor_b = np.log(energy / break_energy) / (delta * log_of_10)
    cosh_ = np.cosh(factor_a) / np.cosh(factor_b)
    b_minus_a = factor_b - factor_a

    f = smoothly_broken_power_law(
        energy=energy, amp=amp, e_piv=e_piv, index1=index1, break_energy=break_energy, delta=delta, index2=index2
    )
    df_d1 = f / amp
    df_d2 = f * 0
    df_d3 = f * 0.5 * delta * log_of_10 * (np.log(cosh_) + b_minus_a)
    df_d4 = f * ((index1 - index2) / (2 * break_energy))
    df_d5 = f * 0
    df_d6 = f * 0.5 * delta * log_of_10 * (np.log(1 / cosh_) + b_minus_a)

    return np.array([df_d1, df_d2, df_d3, df_d4, df_d5, df_d6])


def band_errors(energy, amp, e_peak, index1, index2, cov, correlated=True):
    n_param = model_n_pars["band"]
    grad1, grad2, transition_condition = _band_grads(
        energy=energy, amp=amp, e_peak=e_peak, index1=index1, index2=index2
    )

    err1 = give_errors(cov=cov, grads=grad1, n_params=n_param, correlated=correlated)
    err2 = give_errors(cov=cov, grads=grad2, n_params=n_param, correlated=correlated)

    return np.where(energy <= transition_condition, err1, err2)


def _band_grads(energy, amp, e_peak, index1, index2):
    e_piv = 100.0
    i1_minus_i2 = index1 - index2
    i1p2 = index1 + 2.0
    break_ = e_peak / i1p2

    f = band_function(energy=energy, amp=amp, e_peak=e_peak, index1=index1, index2=index2)

    df_1_d1 = f / amp
    df_1_d2 = f * (energy * i1p2 * (1 / e_peak**2))
    df_1_d3 = f * (np.log(energy / e_piv) - (energy / e_peak))
    df_1_d4 = f * 0

    df_2_d1 = f / amp
    df_2_d2 = f * ((index1 - 2 * index2) / e_peak)

    log_num, log_den = e_peak * i1_minus_i2, e_piv * i1p2
    df_2_d3 = f * (index1 * np.log(log_num / log_den) + (-i1_minus_i2 / i1p2))
    df_2_d4 = f * (np.log(energy / e_peak) - np.log(log_num / log_den))

    grad1 = np.array([df_1_d1, df_1_d2, df_1_d3, df_1_d4])
    grad2 = np.array([df_2_d1, df_2_d2, df_2_d3, df_2_d4])

    return grad1, grad2, i1_minus_i2 * break_


def cpl_errors(energy, amp, e_peak, index1, e_piv, cov, correlated=True):
    n_params: int = model_n_pars["cpl"]
    grads = _cpl_grads(energy=energy, amp=amp, e_peak=e_peak, index1=index1, e_piv=e_piv)

    return give_errors(cov=cov, grads=grads, n_params=n_params, correlated=correlated)


def _cpl_grads(energy, amp, e_peak, index1, e_piv):
    f = cutoff_powerlaw(energy=energy, amp=amp, e_peak=e_peak, index1=index1, e_piv=e_piv)
    df_d1 = f / amp
    df_d2 = f * (energy * (2 + index1) / e_peak**2)
    df_d3 = f * (np.log(energy / e_piv) - (energy / e_peak))
    df_d4 = f * 0
    return np.array([df_d1, df_d2, df_d3, df_d4])


def _bb_grads(energy, amp, temperature):
    f = black_body(energy=energy, amp=amp, temperature=temperature)
    df_d1 = f / amp

    df_d21 = f / temperature**2
    df_d2 = df_d21 * (energy + f / (amp * energy))

    return np.array([df_d1, df_d2])


def blackbody_errors(energy, amp, temperature, cov, correlated=True):
    n_params = model_n_pars["bb"]
    grads = _bb_grads(energy=energy, amp=amp, temperature=temperature)

    return give_errors(cov=cov, grads=grads, n_params=n_params, correlated=correlated)


###############################################################################
# OTHER FUNCTIONS
###############################################################################


def broken_powerlaw(energy, amp, e_piv, index1, break_energy, index2):
    f1 = (energy / e_piv) ** index1
    f2 = (break_energy / e_piv) ** index1 * (energy / break_energy) ** index2
    return amp * np.where(energy <= break_energy, f1, f2)


def broken_powerlaw_two_breaks(energy, amp, e_piv, index1, break_energy1, index12, break_energy2, index2):
    f1 = (energy / e_piv) ** index1
    f2 = (break_energy1 / e_piv) ** index1 * (energy / break_energy1) ** index2

    f31 = _pl_one(energy=break_energy1, e_piv=e_piv, index1=index1)
    f32 = _pl_one(energy=break_energy1, e_piv=break_energy2, index1=index12)
    f33 = _pl_one(energy=energy, e_piv=break_energy2, index1=index2)
    f3 = f31 * f32 * f33
    return amp * np.where(energy <= break_energy1, f1, np.where(energy <= break_energy2, f2, f3))


def cutoff_powerlaw_old(energy, amp, temperature, index1, e_piv):
    return amp * _pl_one(energy=energy, e_piv=e_piv, index1=index1) * np.exp(-energy / temperature)


###############################################################################
# AUXILIARY FUNCTIONS
###############################################################################


def _pl_one(energy, e_piv, index1):
    return (energy / e_piv) ** index1


def _cpl_one(energy, e_peak, index1, e_piv):
    return cutoff_powerlaw(energy=energy, amp=1, e_peak=e_peak, index1=index1, e_piv=e_piv)


def convert_cutoff_param(value, index1, convert_to="e_peak"):
    if convert_to.lower() == "e_peak":
        return value * (2 + index1)
    elif convert_to.lower() == "temperature":
        return value / (2 + index1)
    else:
        raise ValueError("convert_to must be 'e_peak' or 'temperature'")


def give_errors(cov, grads, n_params, correlated: bool):
    if not correlated:
        cov = np.diag(np.diag(cov))

    grads_2d = np.abs(grads.reshape(n_params, -1))
    error_sq = np.einsum("ij,ik,jk->k", cov, grads_2d, grads_2d)

    return np.sqrt(error_sq)
