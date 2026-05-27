"""Created on Sep 20 12:48:47 2025"""

from pathlib import Path

from matplotlib import pyplot as plt

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


def update_style():
    """Update style for publication-ready figures."""
    plt.rcParams.update({
        'font.family': 'serif',
        'font.size': 10,
        'axes.labelsize': 10,
        'axes.titlesize': 12,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.grid': True,
        'grid.alpha': 0.25,
        'grid.linestyle': ':',
        'axes.axisbelow': True,
    })
