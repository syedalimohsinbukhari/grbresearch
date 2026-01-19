"""Created on Sep 20 12:48:47 2025"""

from pathlib import Path

from .grb_calculations import IsotropicEnergy
from .grb_core import GRB, GRBCatalog
from .grb_model import Model, ModelSet
from .grb_sed import SpectralModels
from .grb_time import TimeInterval, TimeIntervalSet


def find_project_root(marker="results.json"):
    """Find the root of the project."""
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / marker).exists():
            return parent
    raise RuntimeError("Project root not found")


sbpl_e_peak_indices = {"sbpl": (0, 7), "sbpl_bb": (0, -2), "sbpl_pl": (3, 10), "sbpl_pl_bb": (3, 10)}
