"""Created on Sep 20 12:48:47 2025"""

OK_THRESHOLD = 0.4
NOK_THRESHOLD = 1.0

GRB_COLORS = {"pl": "blue",
              "pl_bb": "blue",
              "cpl": "orange",
              "cpl_pl": "orange",
              "cpl_bb": "orange",
              "cpl_pl_bb": "orange",
              "band": "green",
              "band_pl": "green",
              "band_bb": "green",
              "band_pl_bb": "green",
              "sbpl": "red",
              "sbpl_pl": "red",
              "sbpl_bb": "red",
              "sbpl_pl_bb": "red",
              "bb": "purple"}

short_to_long = {
    "150210A": "GRB150210935",
    "110731A": "GRB110731465",
    "110721A": "GRB110721200",
    "080916C": "GRB080916009",
}

model_n_pars = {
    "pl": 3,
    "bb": 2,
    "cpl": 4,
    "band": 4,
    "sbpl": 6,
    "pl_bb": 5,
    "cpl_pl": 7,
    "cpl_bb": 6,
    "cpl_pl_bb": 9,
    "band_pl": 7,
    "band_bb": 6,
    "band_pl_bb": 9,
    "sbpl_pl": 9,
    "sbpl_bb": 8,
    "sbpl_pl_bb": 11,
}

pl_par = ["amp_pl", "e_piv_pl", "index1_pl"]
pl_par_second = ['amp_pl', 'e_piv_pl', 'add_index_pl']
cpl_par = ["amp_cpl", "e_peak_cpl", "index1_cpl", "e_piv_cpl"]
band_par = ["amp_band", "e_peak_band", "index1_band", "index2_band"]
sbpl_par = ["amp_sbpl", "e_piv_sbpl", "index1_sbpl", "e_break_sbpl", "delta_sbpl", "index2_sbpl"]
bb_par = ["amp_bb", "kt_bb"]

MODEL_PARAMETERS = {
    "pl": pl_par,
    "pl_bb": pl_par + bb_par,
    "band": band_par,
    "band_pl": pl_par_second + band_par,
    "band_bb": band_par + bb_par,
    "band_pl_bb": pl_par_second + band_par + bb_par,
    "cpl": cpl_par,
    "cpl_pl": pl_par_second + cpl_par,
    "cpl_bb": cpl_par + bb_par,
    "cpl_pl_bb": pl_par_second + cpl_par + bb_par,
    "sbpl": sbpl_par,
    "sbpl_bb": sbpl_par + bb_par,
    "sbpl_pl": pl_par_second + sbpl_par,
    "sbpl_pl_bb": pl_par_second + sbpl_par + bb_par,
}
