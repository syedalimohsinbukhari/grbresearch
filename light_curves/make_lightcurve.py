"""Created on Thu Mar 10 13:54:15 2022"""

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits

from light_curves import lightcurve_data


def make_lightcurves(
        src_name,
        met_time,
        start,
        stop,
        nai_detector_list,
        bgo_detector_list,
        lat_gtrspgen,
        low1=10,
        high1=50,
        low2=50,
        high2=900,
        low3=250,
        high3=40_000,
        no_lat=False
):
    print(f"Reading the data for {low1} keV to {high1} keV energy range")
    data_nai_1 = [lightcurve_data(dat_file=f"{i}.dat", energy_low=low1, energy_high=high1) for i in nai_detector_list]

    t, r1, b1 = np.stack(arrays=np.array(data_nai_1), axis=1)

    t = t[0]
    r1 = np.sum(a=r1, axis=0)
    b1 = np.sum(a=b1, axis=0)

    print(f"Reading the data for {low2} keV to {high2} keV energy range")
    data_nai_2 = [lightcurve_data(dat_file=f"{i}.dat", energy_low=low2, energy_high=high2) for i in nai_detector_list]

    _, r2, b2 = np.stack(arrays=np.array(data_nai_2), axis=1)

    r2 = np.sum(a=r2, axis=0)
    b2 = np.sum(a=b2, axis=0)

    print(f"Reading the data for {low3} keV to {high3 / 1e3} MeV energy range")
    data_bgo = [lightcurve_data(dat_file=f"{i}.dat", energy_low=low3, energy_high=high3) for i in bgo_detector_list]

    _, r3, b3 = np.stack(arrays=np.array(data_bgo), axis=1)

    r3 = np.sum(a=r3, axis=0)
    b3 = np.sum(a=b3, axis=0)

    f, ax = plt.subplots(nrows=3 if no_lat else 5, ncols=1, sharex=True, figsize=(10, 8) if no_lat else (8, 10))

    ax[0].set_title(f"{src_name}")
    ax[0].plot(t, r1 - b1, "k", label=f"NaI: {low1} keV - {high1} keV", drawstyle="steps")
    ax[1].plot(t, r2 - b2, "k", label=f"NaI: {low2} keV - {high2} keV", drawstyle="steps")
    ax[2].plot(t, r3 - b3, "k", label=f"BGO: {low3} keV - {high3 / 1e3} MeV", drawstyle="steps")

    if not no_lat:
        print("Reading the data for > 100 MeV")
        lat = fits.open(lat_gtrspgen)[1].data

        ene_lat, t_lat, p_lat = zip(*sorted(zip(lat["ENERGY"], lat["TIME"], lat[f"{src_name}"])))

        ene_lat, t_lat, p_lat = np.array(ene_lat), np.array(t_lat), np.array(p_lat)

        lt_1gev = ene_lat <= 1000
        gt_1gev = ene_lat > 1000

        lt_1gev_lt9 = np.logical_and(ene_lat < 1000, p_lat < 0.9)
        lt_1gev_gt9 = np.logical_and(ene_lat < 1000, p_lat > 0.9)

        gt_1gev_lt9 = np.logical_and(ene_lat > 1000, p_lat < 0.9)
        gt_1gev_gt9 = np.logical_and(ene_lat > 1000, p_lat > 0.9)

        sub_time = t_lat - met_time

        _, hist_bins = np.histogram(a=sub_time, bins=32)

        ax[3].hist(sub_time[lt_1gev], bins=hist_bins, ec="k", fc="none", label="LAT: 100 MeV - 1 GeV")
        a3 = ax[3].twinx()
        a3.scatter(sub_time[lt_1gev_lt9], ene_lat[lt_1gev_lt9], marker=".", fc="w", ec="r")
        a3.scatter(sub_time[lt_1gev_gt9], ene_lat[lt_1gev_gt9], marker=".", fc="r", ec="r")
        ax[3].set_ylim(bottom=0.1)

        ax[4].hist(sub_time[gt_1gev], bins=hist_bins, ec="k", fc="none", label="LAT: > 1 GeV")
        a4 = ax[4].twinx()
        a4.scatter(sub_time[gt_1gev_lt9], ene_lat[gt_1gev_lt9], marker=".", fc="w", ec="r")
        a4.scatter(sub_time[gt_1gev_gt9], ene_lat[gt_1gev_gt9], marker=".", fc="r", ec="r")

        [i.set_ylabel("Energy [MeV]", rotation=-90, labelpad=20) for i in [a3, a4]]

    [i.grid("both", zorder=-1, ls=":", lw=1) for i in ax]

    [i.axvline(start, color="r", ls="--") for i in ax]
    [i.axvline(stop, color="r", ls="--") for i in ax]

    if np.logical_and(stop - start > 2, stop - start <= 10):
        plt.xlim(start - 3, stop + 3)
    elif stop - start > 10:
        plt.xlim(start - 5, stop + 5)
    else:
        plt.xlim(start - 0.512, stop + 0.512)

    if not no_lat:
        [i.set_ylabel("Counts/s") for i in ax[:-2]]
        [i.set_ylabel("No. of photons") for i in ax[-2:]]
    else:
        [i.set_ylabel("Counts/s") for i in ax]

    ax[-1].set_xlabel("Time since trigger " + r"[T$_0$]")
    [i.legend(loc=1, frameon=False) for i in ax]
    f.tight_layout()

    return f, ax
