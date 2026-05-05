"""Created on Apr 28 07:04:07 2026"""

import numpy as np
import pandas as pd
from black import Path

from src.grb_research import find_project_root
from src.grb_research.grb_calculations import FluxFluenceCalculator
from src.grb_research.grb_core import prepare_grbs
from src.grb_research.grb_time import EpisodeTypes

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCE_ROOT = find_project_root()
RESULT_FILE = SOURCE_ROOT / "results.json"
GRB_LIST = ["080916C", "110731A", "140206B", "150210A"]
N_SAMPLES = 10_000
RANDOM_SEED = 12345

cur_dir = Path(__file__).parent


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def episode_label(model) -> str:
    """Produce the legend label for a single model's episode."""
    if model.interval.kind in (EpisodeTypes.T90, EpisodeTypes.EX0, EpisodeTypes.EX1):
        return str(model.interval.kind)
    return f"{model.interval.kind}{model.interval.index}"


def compute_flux_fluence(model, rng: np.random.Generator, n_samples: int = 10) -> dict:
    """Calculate flux and fluence with uncertainties for a single model."""
    fc = FluxFluenceCalculator(model, rng=rng, n_samples=n_samples)

    flux_val, flux_lo, flux_hi = fc.calculate('flux')
    fluence_val, fluence_lo, fluence_hi = fc.calculate('fluence', in_ergs=True)

    return {
        'grb_name': None,  # Will be filled in loop
        'ep_type': episode_label(model),
        'model_name': model.name,
        'flux': flux_val,
        'flux_lower': flux_lo,
        'flux_upper': flux_hi,
        'fluence': fluence_val,
        'fluence_lower': fluence_lo,
        'fluence_upper': fluence_hi,
    }


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

# Prepare GRB data
gc, grb_list_long, grb_objs, grb_best = prepare_grbs(
    GRB_LIST, RESULT_FILE, get_best=True
)

rng = np.random.default_rng(RANDOM_SEED)

# Count total models for progress bar
total_models = sum(len(models) for models in grb_best)

# Collect results
results = []

for grb_name, models in zip(grb_list_long, grb_best):
    print(f'{grb_name}')

    for model in models:
        print(f"{model.name}")

        row = compute_flux_fluence(model, rng, n_samples=N_SAMPLES)
        row['grb_name'] = grb_name
        results.append(row)

# Create DataFrame
flux_fluence_dataframe = pd.DataFrame(results)

# Save to CSV
output_path = cur_dir / "flux_fluence.csv"
flux_fluence_dataframe.to_csv(output_path, index=False)
