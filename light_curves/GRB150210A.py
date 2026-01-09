"""Created on Mon Apr 4 10:07:22 2022"""

import os

from matplotlib import pyplot as plt

from make_lightcurve import make_lightcurves

source_name = "150210A"
t_05 = 0.064
t_95 = 31.360
trigger_time = 445299987.29

path_ = "GRB150210935"
cwd = os.getcwd()

os.chdir(f"{cwd}/{path_}")

dat = [f for f in os.listdir(f"{cwd}/{path_}") if f.endswith(".dat")]
dat = [i.split(".")[0] for i in dat]

dat_NaI = [i.split(".")[0] for i in dat if "n" in i]
dat_BGO = list(set(dat) ^ set(dat_NaI))

fit = [f for f in os.listdir(f"{cwd}/{path_}") if f.endswith(".fits")][0]
f, ax = make_lightcurves(
    src_name=f"GRB{source_name}",
    met_time=trigger_time,
    start=t_05,
    stop=t_95,
    nai_detector_list=dat_NaI,
    bgo_detector_list=dat_BGO,
    lat_gtrspgen=f"{cwd}/{path_}/{fit}",
)

times = [0.064, 0.832, 2.176, 3.328, 17.344, 31.36]
colors = ["r", "g", "gold", "b", "maroon", "cyan"]

for ax_i in ax:
    for index, ((start, end), color) in enumerate(zip(zip(times[:-1], times[1:]), colors)):
        if end != times[-1]:
            ax_i.axvline(end, color=colors[index + 1], ls="--")
        ax_i.axvspan(start, end, color=color, alpha=0.1)

[plt.savefig(f"GRB{source_name}_lightcurve.{i}", dpi=600) for i in ["png", "pdf"]]
plt.close()

os.chdir(cwd)
