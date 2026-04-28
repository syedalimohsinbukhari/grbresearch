import json
import pandas as pd
from pathlib import Path

# =========================
# 1. File paths (YOUR DATA)
# =========================
BASE_DIR = Path("/media/iqrasiddique/37894CDB5D15D24B/PhDWork/#ResearchWork/GDrive_Data/GRBResearch")

RESULT_FILE = BASE_DIR / "results.json"

# optional: if lorentz_factor.py outputs helper functions later
LORRENTZ_MODULE_PATH = BASE_DIR / "codes-for-paper/lorentz_factor"

# =========================
# 2. Load results.json
# =========================
with open(RESULT_FILE, "r") as f:
    data = json.load(f)

rows = []

print(type(data))
print(type(data[0]))
print(data[0])

# =========================
# 3. Parse GRB entries
# =========================
for grb in data:

    name = grb.get("name")
    z = grb.get("z")
    E_obs = grb.get("E_obs")

    # ---- rest-frame correction ----
    E_rest = None
    if E_obs is not None and z is not None:
        E_rest = E_obs * (1 + z)

    # ---- Lorentz fit results ----
    fit = grb.get("fit", {})

    lorentz_param = fit.get("lorentz_param")
    lorentz_error = fit.get("lorentz_error")
    chi2 = fit.get("chi2")

    rows.append({
        "GRB": name,
        "z": z,
        "E_obs": E_obs,
        "E_rest": E_rest,
        "lorentz_param": lorentz_param,
        "lorentz_error": lorentz_error,
        "chi2": chi2
    })

# =========================
# 4. Build DataFrame
# =========================
df = pd.DataFrame(rows)

# =========================
# 5. Clean data
# =========================
df = df.dropna(subset=["lorentz_param"])
df = df.sort_values(by="z")

# =========================
# 6. Save outputs
# =========================
out_csv = BASE_DIR / "lorentz_table.csv"
out_json = BASE_DIR / "lorentz_table.json"
out_tex = BASE_DIR / "lorentz_table.tex"

df.to_csv(out_csv, index=False)
df.to_json(out_json, orient="records")
df.to_latex(out_tex, index=False)

# =========================
# 7. Summary
# =========================
print("Done.")
print("Saved CSV:", out_csv)
print("Saved JSON:", out_json)
print("Saved LaTeX:", out_tex)

print("\nGRBs processed:", len(df))
print("Mean Lorentz parameter:", df["lorentz_param"].mean())