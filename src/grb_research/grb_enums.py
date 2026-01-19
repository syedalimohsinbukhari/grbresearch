"""Created on Jan 07 14:43:25 2026"""

from __future__ import annotations

__all__ = [
    "GRBModelsCombinations",
    "PowerLawParameters",
    "BlackBodyParameters",
    "CutOffPowerLawParameters",
    "BandGRBParameters",
    "SmoothlyBrokenPowerLawParameters",
    "ModelStatus",
    "GoodnessOfFit",
]

from enum import Enum


class GRBModelsCombinations(Enum):
    """Enumeration of GRB models."""

    PL = "pl"
    BB = "bb"
    PL_BB = "pl_bb"

    CPL = "cpl"
    CPL_PL = "cpl_pl"
    CPL_BB = "cpl_bb"
    CPL_PL_BB = "cpl_pl_bb"

    BAND = "band"
    BAND_PL = "band_pl"
    BAND_BB = "band_bb"
    BAND_PL_BB = "band_pl_bb"

    SBPL = "sbpl"
    SBPL_PL = "sbpl_pl"
    SBPL_BB = "sbpl_bb"
    SBPL_PL_BB = "sbpl_pl_bb"


class PowerLawParameters(Enum):
    """Enumeration of power law parameters."""

    AMP_PL = "amp_pl"
    INDEX_1_PL = "index1_pl"
    E_PIV_PL = "e_piv_pl"
    INDEX_ADD_PL = "add_index_pl"


class BlackBodyParameters(Enum):
    """Enumeration of black body parameters."""

    AMP_BB = "amp_bb"
    KT_BB = "kt_bb"


class CutOffPowerLawParameters(Enum):
    """Enumeration of cutoff power law parameters."""

    AMP_CPL = "amp_cpl"
    PEAK_ENERGY_CPL = "e_peak_cpl"
    INDEX_1_CPL = "index1_cpl"
    E_PIV_CPL = "e_piv_cpl"


class BandGRBParameters(Enum):
    """Enumeration of band GRB parameters."""

    AMP_BAND = "amp_band"
    PEAK_ENERGY_BAND = "e_peak_band"
    INDEX_1_BAND = "index1_band"
    INDEX_2_BAND = "index2_band"


class SmoothlyBrokenPowerLawParameters(Enum):
    """Enumeration of smoothly broken power law parameters."""

    AMP_SBPL = "amp_sbpl"
    E_PIV_SBPL = "e_piv_sbpl"
    INDEX_1_SBPL = "index1_sbpl"
    BREAK_ENERGY_SBPL = "e_break_sbpl"
    DELTA_SBPL = "delta_sbpl"
    INDEX_2_SBPL = "index2_sbpl"


class ModelStatus(Enum):
    """Custom flags for model evaluation"""

    INVALID = -2
    UNNECESSARY = -1
    REJECTED = 0
    ACCEPTED = 1


class GoodnessOfFit(Enum):
    """Enum class for goodness of fit types."""

    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    GOOD = SAFE
    BEST = "BEST"
    UNKNOWN = "UNKNOWN"

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"
