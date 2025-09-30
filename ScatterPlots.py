# -*- coding: utf-8 -*-
"""
Unified scatter plot generator for BAND, CPL, SBPL.
- Reads results.json (same folder)
- For each selected model, extracts time-binned parameters across all episodes
- Saves a CSV and a PNG scatter:
    * X = mid-time of episode (with horizontal half-duration error bars)
    * Y = E_peak (BAND/CPL) or E_break (SBPL) with vertical 1σ errors
    * TI (longest bin) = red ■ with duration in legend
    * TR inside TI = blue, distinct marker per episode, legend shows <shape> + duration
    * TR outside TI = grey, distinct marker per episode, legend shows <shape> + duration
Edit CONFIG below as needed.
"""

import os
import json
import math
from typing import Any, Dict, Tuple, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# --------------------------- CONFIG --------------------------- #
INPUT_JSON = "results.json"          # results file in the same directory
GRB_ID = "GRB080916009"              # target GRB
OUTDIR = "outputs"                   # output directory for CSV/PNG

# Which models to run. Choose any subset of {"BAND","CPL","SBPL"} or leave as-is for all.
MODELS_TO_RUN = ["CPL", "SBPL"]

# Colors
TI_COLOR = "C3"                      # red for time-integrated (longest)
TR_IN_COLOR = "C0"                   # blue for time-resolved inside TI
TR_OUT_COLOR = "0.6"                 # grey for time-resolved outside TI

DURATION_FMT = "{:.2f}s"             # legend duration formatting

# Distinct marker cycles (plenty of unique shapes; will cycle if more bins)
MARKERS_IN = ["o", "^", "v", "s", "D", "*", "<", ">", "X", "P", "h", "d"]
MARKERS_OUT = ["o", "^", "v", "s", "D", "*", "<", ">", "X", "P", "h", "d"]

# Map matplotlib marker -> Unicode-like symbol for legend text
MARKER_SYMBOL = {
    "o": "●",  "^": "▲",  "v": "▼",  "s": "■",
    "D": "◆",  "d": "◆",  "*": "★",  "<": "◄",
    ">": "►",  "X": "✕",  "P": "⬟",  "h": "⬢",
}
# -------------------------------------------------------------- #


def get_val_err(d: Dict[str, Any], key: str) -> Tuple[float, float]:
    """Extract value and 1σ error from a dict field: number OR [value, error]."""
    if not isinstance(d, dict) or key not in d:
        return float("nan"), float("nan")
    v = d[key]
    if isinstance(v, (int, float)):
        return float(v), float("nan")
    if isinstance(v, (list, tuple)) and len(v) == 2:
        try:
            return float(v[0]), float(v[1])
        except Exception:
            return float("nan"), float("nan")
    return float("nan"), float("nan")


def parse_episode_key(ep_key: str) -> Tuple[float, float, float, float]:
    """Parse episode key like '1.280_64.256' -> (t_start, t_end, t_mid, duration)."""
    try:
        t0, t1 = ep_key.split("_")
        t_start = float(t0)
        t_end = float(t1)
        t_mid = 0.5 * (t_start + t_end)
        duration = t_end - t_start
        return t_start, t_end, t_mid, duration
    except Exception:
        return math.nan, math.nan, math.nan, math.nan


def model_key_lookup(models: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Case-insensitive fetch of a model dict (BAND/CPL/SBPL)."""
    if not isinstance(models, dict):
        return {}
    for k in (model, model.capitalize(), model.lower()):
        if k in models and isinstance(models[k], dict):
            return models[k]
    # also try mixed-case common variants
    for k in models:
        if isinstance(k, str) and k.upper() == model.upper() and isinstance(models[k], dict):
            return models[k]
    return {}


def y_key_and_label(model: str) -> Tuple[str, str]:
    """Return the parameter key and y-label for the chosen model."""
    mu = model.upper()
    if mu == "BAND":
        return "e_peak_band", r"$E_{\rm peak}$ (keV)"
    if mu == "CPL":
        return "e_peak_cpl", r"$E_{\rm peak}$ (keV)"
    if mu == "SBPL":
        return "e_break_sbpl", r"$E_{\rm break}$ (keV)"
    raise ValueError("Unknown model: must be BAND, CPL, or SBPL")


def collect_rows(results: Dict[str, Any], grb_id: str, model: str) -> pd.DataFrame:
    """Build a DataFrame of chosen model parameters across episodes for the given GRB."""
    if grb_id not in results:
        raise KeyError(f"{grb_id} not found in results.json keys.")

    ykey, ylab = y_key_and_label(model)
    rows: List[Dict[str, Any]] = []

    for ep_key, models in results[grb_id].items():
        mdl = model_key_lookup(models, model)
        if not mdl:
            continue

        t_start, t_end, t_mid, duration = parse_episode_key(ep_key)
        yval, yerr = get_val_err(mdl, ykey)

        rows.append(
            dict(
                GRB=grb_id,
                model=model.upper(),
                episode=ep_key,
                t_start_s=t_start,
                t_end_s=t_end,
                t_mid_s=t_mid,
                duration_s=duration,
                Y_value=yval,
                Y_err=yerr,
                y_label=ylab,
            )
        )

    df = pd.DataFrame(rows)
    if df.empty:
        # It's okay if a model is missing; caller can skip plotting.
        return df

    # Keep chronological order (helps legend ordering)
    df = df.sort_values(by=["t_start_s", "t_mid_s"], na_position="last").reset_index(drop=True)
    return df


def _xerr_from_bounds(starts: np.ndarray, ends: np.ndarray) -> np.ndarray:
    """Symmetric x-error = half of the bin width."""
    return 0.5 * (ends - starts)


def plot_one_model(df: pd.DataFrame, grb_id: str, model: str, out_png: str) -> None:
    """Scatter with TI highlighted, inside/outside TI colored & per-episode markers; legend shows symbol + duration."""
    # Identify TI (longest duration)
    ti_idx = df["duration_s"].idxmax()
    df_ti = df.loc[[ti_idx]]
    df_tr = df.drop(index=ti_idx)

    ti_start = float(df_ti["t_start_s"].iloc[0])
    ti_end = float(df_ti["t_end_s"].iloc[0])
    ti_dur = float(df_ti["duration_s"].iloc[0])

    # Split TR: fully inside TI vs outside TI window
    inside_mask = (df_tr["t_start_s"] >= ti_start) & (df_tr["t_end_s"] <= ti_end)
    df_tr_in = df_tr.loc[inside_mask].sort_values("t_start_s")
    df_tr_out = df_tr.loc[~inside_mask].sort_values("t_start_s")

    y_label = df["y_label"].iloc[0]

    fig, ax = plt.subplots(figsize=(10, 5.2))

    # --- TR inside: per-episode markers & legend entries ---
    for i, (_, r) in enumerate(df_tr_in.iterrows()):
        mkr = MARKERS_IN[i % len(MARKERS_IN)]
        sym = MARKER_SYMBOL.get(mkr, mkr)
        x = float(r["t_mid_s"]); y = float(r["Y_value"])
        xerr = _xerr_from_bounds(np.array([r["t_start_s"]]), np.array([r["t_end_s"]]))
        yerr = np.array([r["Y_err"]], dtype=float)
        label_txt = f"{sym} {DURATION_FMT.format(float(r['duration_s']))}"
        ax.errorbar([x], [y], xerr=xerr, yerr=yerr,
                    fmt=mkr, capsize=3, color=TR_IN_COLOR, markersize=7,
                    linestyle="None", label=label_txt)

    # --- TR outside: per-episode markers & legend entries (grey) ---
    for i, (_, r) in enumerate(df_tr_out.iterrows()):
        mkr = MARKERS_OUT[i % len(MARKERS_OUT)]
        sym = MARKER_SYMBOL.get(mkr, mkr)
        x = float(r["t_mid_s"]); y = float(r["Y_value"])
        xerr = _xerr_from_bounds(np.array([r["t_start_s"]]), np.array([r["t_end_s"]]))
        yerr = np.array([r["Y_err"]], dtype=float)
        label_txt = f"{sym} {DURATION_FMT.format(float(r['duration_s']))} (outside TI)"
        ax.errorbar([x], [y], xerr=xerr, yerr=yerr,
                    fmt=mkr, capsize=3, color=TR_OUT_COLOR, markersize=7,
                    linestyle="None", label=label_txt)

    # --- TI point ---
    xti = df_ti["t_mid_s"].values; yti = df_ti["Y_value"].values
    xerr_ti = _xerr_from_bounds(df_ti["t_start_s"].values, df_ti["t_end_s"].values)
    yerr_ti = df_ti["Y_err"].values
    ti_label = f"{MARKER_SYMBOL.get('s', '■')} Time-integrated: {DURATION_FMT.format(ti_dur)}"
    ax.errorbar(xti, yti, xerr=xerr_ti, yerr=yerr_ti,
                fmt="s", capsize=3, color=TI_COLOR, markersize=8,
                linestyle="None", label=ti_label)

    # Axes & aesthetics
    ax.set_xlabel("Mid-time of episode (s since T0)")
    ax.set_ylabel(y_label)
    ax.set_title(f"{grb_id} — {model.upper()} model: {y_label} vs time (per episode)")
    ax.grid(True, which="both", alpha=0.3)

    ax.legend(loc="best", frameon=True)

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main():
    # Load JSON
    with open(INPUT_JSON, "r") as f:
        results = json.load(f)

    os.makedirs(OUTDIR, exist_ok=True)

    for model in MODELS_TO_RUN:
        df = collect_rows(results, GRB_ID, model)
        if df.empty:
            print(f"[SKIP] No {model.upper()} entries found for {GRB_ID}.")
            continue

        # Save CSV
        out_csv = os.path.join(OUTDIR, f"{GRB_ID}_{model.upper()}_params.csv")
        df.to_csv(out_csv, index=False)

        # Plot
        out_png = os.path.join(OUTDIR, f"{GRB_ID}_{model.upper()}_Y_vs_time.png")
        plot_one_model(df, GRB_ID, model, out_png)

        print(f"[OK] {model.upper()}: Saved CSV: {out_csv}")
        print(f"[OK] {model.upper()}: Saved plot: {out_png}")


if __name__ == "__main__":
    main()
