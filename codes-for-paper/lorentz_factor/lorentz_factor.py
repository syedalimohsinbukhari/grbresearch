"""
Minimum Lorentz Factor Calculator
===================================
Computes Gamma_min using the gamma-gamma opacity method.

Reference: Lithwick & Sari (2001), ApJ, 555, 540
           Abdo et al. (2009), Science, 323, 1688

Formula (Lithwick & Sari 2001, Limit A, Table 1 with redshift corrections):

    tau_hat = 2.1e11 * [(d_L/7Gpc)^2 * (0.511)^(-alpha+1) * f_1]
              / [(delta_T/0.1s) * (alpha-1)]

    Gamma_min = tau_hat^(1/(2a+2))
                * (E_max/511)^((a-1)/(2a+2))
                * (1+z)^((a-1)/(a+1))

    where:
        alpha    = Lithwick & Sari photon index (positive) = -beta_band
        f_1      = photon flux at 1 MeV [ph/cm^2/s/MeV]
        E_max    = highest LAT photon energy [keV]
        delta_T  = variability timescale [s]
        z        = redshift
        d_L      = luminosity distance [cm]

Outputs:
    lorentz_results.csv   — all computed values
    lorentz_table.tex     — LaTeX table for paper
"""

import numpy as np
import pandas as pd
from astropy.cosmology import FlatLambdaCDM

# ─── Cosmology ────────────────────────────────────────────────────────────────
cosmo = FlatLambdaCDM(H0=67.4, Om0=0.315)

# ─── Spectral flux at 1 MeV from model parameters ────────────────────────────

def f1_from_sbpl(amp, e_piv, index2):
    """
    Photon flux at 1 MeV from SBPL model.
    Uses high-energy power law: N(E) ~ amp * (E/e_piv)^index2

    Parameters
    ----------
    amp    : float  amplitude [ph/cm^2/s/keV]
    e_piv  : float  pivot energy [keV]
    index2 : float  high-energy index (negative, e.g. -2.25)

    Returns
    -------
    f_1    : float  photon flux at 1 MeV [ph/cm^2/s/MeV]
    """
    N_1MeV = amp * (1000.0 / e_piv)**index2   # ph/cm^2/s/keV at 1000 keV
    return N_1MeV * 1000.0                     # convert to ph/cm^2/s/MeV


def f1_from_band(amp, index1, index2, e_peak):
    """
    Photon flux at 1 MeV from Band model.
    Evaluates Band function at 1 MeV = 1000 keV.

    Parameters
    ----------
    amp    : float  amplitude [ph/cm^2/s/keV] at pivot 100 keV
    index1 : float  low-energy index (negative)
    index2 : float  high-energy index (negative)
    e_peak : float  spectral peak energy [keV]
    """
    E = 1000.0   # keV
    E_c = (index1 - index2) * e_peak / (index1 + 2)
    if E <= E_c:
        N = amp * (E/100)**index1 * np.exp(-E*(2 + index1)/e_peak)
    else:
        N = (amp
             * ((index1 - index2) * e_peak / ((index1 + 2) * 100))**(index1 - index2)
             * np.exp(index2 - index1)
             * (E/100)**index2)
    return N * 1000.0   # ph/cm^2/s/MeV


# ─── Gamma_min formula ───────────────────────────────────────────────────────

def compute_gamma_min(alpha_LS, f_1, E_max_keV, delta_T_s, z):
    """
    Compute minimum Lorentz factor (Lithwick & Sari 2001, Limit A).

    Parameters
    ----------
    alpha_LS  : float  L&S photon index (positive) = -beta_band (high-energy index)
    f_1       : float  photon flux at 1 MeV [ph/cm^2/s/MeV]
    E_max_keV : float  highest LAT photon energy [keV]
    delta_T_s : float  variability timescale [s]
    z         : float  redshift

    Returns
    -------
    gamma_min : float
    tau_hat   : float
    """
    d_L_cm = cosmo.luminosity_distance(z).cgs.value
    d_7Gpc = d_L_cm / (7.0 * 3.0857e27)

    tau_hat = (2.1e11
               * d_7Gpc**2
               * (0.511)**(-alpha_LS + 1)
               * f_1
               / ((delta_T_s / 0.1) * (alpha_LS - 1)))

    e1 = 1.0 / (2*alpha_LS + 2)
    e2 = (alpha_LS - 1) / (2*alpha_LS + 2)
    e3 = (alpha_LS - 1) / (alpha_LS + 1)

    gamma_min = tau_hat**e1 * (E_max_keV/511.0)**e2 * (1+z)**e3
    return gamma_min, tau_hat


# ─── INPUT DATA ──────────────────────────────────────────────────────────────
# Edit these values if parameters change.
# f_1 computed from T90 BEST model spectral parameters (results.json).
# E_GeV from LAT table (Table 2 in paper).
# t_v = duration of shortest well-resolved emission episode (Table 1).

grb_inputs = [
    {
        "grb":       "GRB~080916C",
        "z":          4.35,
        "E_max_keV":  27428.8,          # 27.43 GeV — highest LAT photon
        "t_arr_s":    40.503,            # arrival time [s]
        "delta_T_s":  0.9,              # variability timescale [s]
        "model":      "SBPL_BB",
        "beta":       -2.251,           # index2_sbpl from T90 BEST
        # SBPL_BB spectral params (T90):
        "amp":        0.010460,         # ph/cm^2/s/keV
        "e_piv":      100.0,            # keV
        "index2":     -2.251,
        "spectral_type": "sbpl",
    },
    {
        "grb":       "GRB~110721A",
        "z":          0.3826,
        "E_max_keV":  6652.84,          # 6.65 GeV
        "t_arr_s":    4.496,
        "delta_T_s":  1.344,            # TR1 duration
        "model":      "BAND_BB",
        "beta":       -2.728,           # index2_band from T90 BEST
        # BAND_BB spectral params (T90):
        "amp":        0.016366,
        "index1":     -1.247,
        "index2":     -2.728,
        "e_peak":     2120.290,         # keV
        "spectral_type": "band",
    },
    {
        "grb":       "GRB~110731A",
        "z":          2.83,
        "E_max_keV":  965.33,           # 0.965 GeV
        "t_arr_s":    5.521,
        "delta_T_s":  1.984,            # TR2 duration
        "model":      "SBPL",
        "beta":       -2.320,           # index2_sbpl from T90 BEST
        # SBPL spectral params (T90):
        "amp":        0.041910,
        "e_piv":      100.0,
        "index2":     -2.320,
        "spectral_type": "sbpl",
    },
    {
        "grb":       "GRB~150210A",
        "z":          None,             # unknown redshift
        "E_max_keV":  1047.20,
        "t_arr_s":    2.023,
        "delta_T_s":  None,
        "model":      "SBPL",
        "beta":       -3.002,
        "spectral_type": "sbpl",
    },
]


# ─── COMPUTE ─────────────────────────────────────────────────────────────────

results = []

print(f"\n{'GRB':<15} {'alpha_LS':>9} {'f_1 [ph/cm2/s/MeV]':>20} {'tau_hat':>12} {'Gamma_min':>10}")
print("-" * 72)

for g in grb_inputs:

    # Compute f_1 from spectral model
    if g["z"] is None:
        f_1 = alpha_LS = tau_hat = gamma = None
        print(f"{g['grb']:<15} {'—':>9} {'—':>20} {'—':>12} {'—':>10}")
    else:
        if g["spectral_type"] == "sbpl":
            f_1 = f1_from_sbpl(g["amp"], g["e_piv"], g["index2"])
        else:
            f_1 = f1_from_band(g["amp"], g["index1"], g["index2"], g["e_peak"])

        alpha_LS = -g["index2"]
        gamma, tau_hat = compute_gamma_min(alpha_LS, f_1, g["E_max_keV"], g["delta_T_s"], g["z"])
        print(f"{g['grb']:<15} {alpha_LS:>9.3f} {f_1:>20.4e} {tau_hat:>12.3e} {gamma:>10.0f}")

    results.append({
        "GRB":           g["grb"],
        "z":             g["z"],
        "E_GeV":         g["E_max_keV"] / 1e3,
        "t_arr_s":       g["t_arr_s"],
        "t_v_s":         g["delta_T_s"],
        "model":         g["model"],
        "beta":          g["beta"],
        "alpha_LS":      alpha_LS,
        "f_1":           f_1,
        "tau_hat":       tau_hat,
        "Gamma_min":     gamma,
    })

# ─── SAVE CSV ────────────────────────────────────────────────────────────────

df = pd.DataFrame(results)
df.to_csv("lorentz_results.csv", index=False)
print("\nSaved: lorentz_results.csv")

# ─── GENERATE LaTeX TABLE ────────────────────────────────────────────────────

def fmt(val, fmt_str, fallback=r"\ldots"):
    return fallback if val is None else format(val, fmt_str)

rows = ""
for r in results:
    z_str     = fmt(r["z"],         ".4f")
    e_str     = fmt(r["E_GeV"],     ".2f")
    tarr_str  = fmt(r["t_arr_s"],   ".2f")
    tv_str    = fmt(r["t_v_s"],     ".3f")
    beta_str  = f"${r['beta']:.3f}$"
    gamma_str = fmt(r["Gamma_min"], ".0f")
    if r["Gamma_min"] is not None:
        gamma_str = f"${int(r['Gamma_min'])}$"
    else:
        gamma_str = r"\ldots"

    # AGN warning for 110721A
    if "110721A" in r["GRB"] and r["Gamma_min"] is not None:
        gamma_str += r"$^\dagger$"

    rows += (f"    {r['GRB']} & ${z_str}$ & ${e_str}$ & "
             f"${tarr_str}$ & ${tv_str}$ & {beta_str} & {gamma_str} \\\\\n")

latex = r"""\begin{table}
\centering
\small
\caption{Minimum bulk Lorentz factor $\Gamma_{\rm min}$ derived from
the gamma-gamma opacity condition for three GRBs with known redshifts.
$E_{\rm GeV}$ is the highest-energy LAT photon detected,
$t_{\rm arr}$ is its arrival time relative to $T_0$,
$t_{\rm v}$ is the variability timescale taken as the duration of
the shortest well-resolved emission episode,
$\beta$ is the high-energy photon index of the T90 best-fit model,
and $\Gamma_{\rm min}$ is the derived lower limit on the bulk Lorentz
factor~\citep{Lithwick2001}.
GRB~150210A has no measured redshift so $\Gamma_{\rm min}$ cannot be
computed.}
\label{tab:lorentz}
\begin{tabular}{lcccccc}
\toprule
GRB & $z$ & $E_{\rm GeV}$ [GeV] & $t_{\rm arr}$ [s] &
    $t_{\rm v}$ [s] & $\beta$ & $\Gamma_{\rm min}$ \\
\midrule
""" + rows + r"""\midrule
\multicolumn{7}{l}{\footnotesize
    $^\dagger$ Interpreted with caution due to AGN
    contamination~\citep{Grupe2011GCN12212SwiftAfterglowCandidateGRB110721A}.} \\
\bottomrule
\end{tabular}
\end{table}
"""

with open("lorentz_table.tex", "w") as f:
    f.write(latex)
print("Saved: lorentz_table.tex")