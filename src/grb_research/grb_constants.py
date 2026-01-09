"""Created on Jan 07 14:42:35 2026"""

__all__ = ["GRB_COLORS",
           "MODEL_PARAMETERS",
           "NOK_THRESHOLD",
           "OK_THRESHOLD",
           "kev_to_erg",
           "model_n_pars",
           "short_to_long"]

from .grb_enums import GRBModelsCombinations as gmC

OK_THRESHOLD = 0.4
NOK_THRESHOLD = 1.0

kev_to_erg = 1.6021766208e-09

GRB_COLORS = {gmC.PL: "blue",
              gmC.PL_BB: "blue",
              gmC.CPL: "orange",
              gmC.CPL_PL: "orange",
              gmC.CPL_BB: "orange",
              gmC.CPL_PL_BB: "orange",
              gmC.BAND: "green",
              gmC.BAND_PL: "green",
              gmC.BAND_BB: "green",
              gmC.BAND_PL_BB: "green",
              gmC.SBPL: "red",
              gmC.SBPL_PL: "red",
              gmC.SBPL_BB: "red",
              gmC.SBPL_PL_BB: "red",
              gmC.BB: "purple"}

short_to_long = {
    "150210A": "GRB150210935",
    "110731A": "GRB110731465",
    "110721A": "GRB110721200",
    "080916C": "GRB080916009",
}

model_n_pars = {
    gmC.PL: 3,
    gmC.BB: 2,
    gmC.CPL: 4,
    gmC.PL_BB: 5,
    gmC.CPL_PL: 7,
    gmC.CPL_BB: 6,
    gmC.CPL_PL_BB: 9,
    gmC.BAND: 4,
    gmC.BAND_PL: 7,
    gmC.BAND_BB: 6,
    gmC.BAND_PL_BB: 9,
    gmC.SBPL: 6,
    gmC.SBPL_PL: 9,
    gmC.SBPL_BB: 8,
    gmC.SBPL_PL_BB: 11,
}

pl_par = ["amp_pl", "e_piv_pl", "index1_pl"]
pl_par_second = ['amp_pl', 'e_piv_pl', 'add_index_pl']
cpl_par = ["amp_cpl", "e_peak_cpl", "index1_cpl", "e_piv_cpl"]
band_par = ["amp_band", "e_peak_band", "index1_band", "index2_band"]
sbpl_par = ["amp_sbpl", "e_piv_sbpl", "index1_sbpl", "e_break_sbpl", "delta_sbpl", "index2_sbpl"]
bb_par = ["amp_bb", "kt_bb"]

MODEL_PARAMETERS = {
    gmC.PL: pl_par,
    gmC.PL_BB: pl_par + bb_par,
    gmC.BAND: band_par,
    gmC.BAND_PL: pl_par_second + band_par,
    gmC.BAND_BB: band_par + bb_par,
    gmC.BAND_PL_BB: pl_par_second + band_par + bb_par,
    gmC.CPL: cpl_par,
    gmC.CPL_PL: pl_par_second + cpl_par,
    gmC.CPL_BB: cpl_par + bb_par,
    gmC.CPL_PL_BB: pl_par_second + cpl_par + bb_par,
    gmC.SBPL: sbpl_par,
    gmC.SBPL_BB: sbpl_par + bb_par,
    gmC.SBPL_PL: pl_par_second + sbpl_par,
    gmC.SBPL_PL_BB: pl_par_second + sbpl_par + bb_par,
}
