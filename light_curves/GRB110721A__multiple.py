"""Created on Mon Apr 4 10:07:22 2022"""

import os

from matplotlib import pyplot as plt

from make_lightcurve import make_lightcurves

source_name = "110721A"
t_05 = 0.000
t_95 = 21.824
trigger_time = 332916465.76

path_ = "GRB110721200"
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

times = [0.000, 1.344, 6.8, 10.688, 21.824]
colors = ["r", "g", "gold", "b", "maroon", "cyan"]

for ax_i in ax:
    for index, ((start, end), color) in enumerate(zip(zip(times[:-1], times[1:]), colors)):
        if end != times[-1]:
            ax_i.axvline(end, color=color, ls="--")
        ax_i.axvspan(start, end, color=color, alpha=0.1)

# plt.show()
[plt.savefig(f"GRB{source_name}_lightcurve__BRK.{i}", dpi=600) for i in ["png", "pdf"]]
plt.close()

os.chdir(cwd)
