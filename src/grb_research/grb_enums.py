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
    # New additions for enum-based API
    "ParameterDef",
    "ModelMetadata",
    "ModelGroupType",
    "str_to_model",
    "model_to_str",
    "normalize_model",
    "accepts_string_or_enum",
]

from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Dict, List, Optional, Union

# ==================== Dataclasses for Model Metadata ====================


@dataclass(frozen=True)
class ParameterDef:
    """Definition of a parameter in a spectral model.

    Attributes
    ----------
    name : str
        Parameter name (e.g., 'amplitude', 'peak_energy').
    is_fixed : bool
        Whether this parameter has a fixed value.
    has_bounds : bool
        Whether this parameter has bounds constraints.
    """

    name: str
    is_fixed: bool
    has_bounds: bool
    only_positive: bool


@dataclass(frozen=True)
class ModelMetadata:
    """Complete metadata for a GRB spectral model.

    Attributes
    ----------
    color : str
        Color for plotting (e.g., 'blue', 'orange').
    total_params : int
        Total number of parameters including fixed ones.
    free_params : int
        Number of free parameters for C-stat comparison.
    complexity_order : int
        Complexity ordering for single models (0=simplest).
    latex_name : str
        LaTeX representation for publications.
    base_parameters : List[str]
        Parameter names when used as a base model.
    component_parameters : Optional[List[str]]
        Parameter names when used as a component (e.g., PL as a component).
    base_schema : List[ParameterDef]
        Parameter definitions for base model usage.
    component_schema : Optional[List[ParameterDef]]
        Parameter definitions for component usage.
    is_standalone : bool
        Whether this can be used as a standalone model.
    is_allowed : bool
        Whether this model is in the ALLOWED_MODELS set.
    """

    color: str
    total_params: int
    free_params: int
    complexity_order: int
    latex_name: str
    base_parameters: List[str]
    component_parameters: Optional[List[str]]
    base_schema: List[ParameterDef]
    component_schema: Optional[List[ParameterDef]]
    is_standalone: bool
    is_allowed: bool


class GRBModelsCombinations(Enum):
    """Enumeration of GRB models."""

    PL = "pl"
    BB = "bb"
    PL_BB = "pl_bb"

    CPL = "cpl"
    # CPL_PL = "cpl_pl"
    CPL_BB = "cpl_bb"
    CPL_PL_BB = "cpl_pl_bb"

    BAND = "band"
    # BAND_PL = "band_pl"
    BAND_BB = "band_bb"
    BAND_PL_BB = "band_pl_bb"

    SBPL = "sbpl"
    # SBPL_PL = "sbpl_pl"
    SBPL_BB = "sbpl_bb"
    SBPL_PL_BB = "sbpl_pl_bb"

    @property
    def name_upper(self) -> str:
        """Return the uppercase name of the model."""
        return self.name

    @property
    def metadata(self) -> ModelMetadata:
        """Get the metadata for this model."""
        return MODEL_METADATA[self]

    @property
    def color(self) -> str:
        """Get the plotting color for this model."""
        return self.metadata.color

    @property
    def total_params(self) -> int:
        """Get the total number of parameters."""
        return self.metadata.total_params

    @property
    def free_params(self) -> int:
        """Get the number of free parameters for C-stat comparison."""
        return self.metadata.free_params

    @property
    def complexity_order(self) -> int:
        """Get the complexity order for single models."""
        return self.metadata.complexity_order

    @property
    def latex_name(self) -> str:
        """Get the LaTeX representation."""
        return self.metadata.latex_name

    @property
    def base_parameters(self) -> List[str]:
        """Get parameter names when used as base model."""
        return self.metadata.base_parameters

    @property
    def component_parameters(self) -> Optional[List[str]]:
        """Get parameter names when used as component."""
        return self.metadata.component_parameters

    @property
    def base_schema(self) -> List[ParameterDef]:
        """Get parameter schema for base model usage."""
        return self.metadata.base_schema

    @property
    def component_schema(self) -> Optional[List[ParameterDef]]:
        """Get parameter schema for component usage."""
        return self.metadata.component_schema

    @property
    def is_standalone(self) -> bool:
        """Check if this can be used as a standalone model."""
        return self.metadata.is_standalone

    @property
    def is_allowed(self) -> bool:
        """Check if this model is in ALLOWED_MODELS."""
        return self.metadata.is_allowed


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
    MARGINAL = "MARGINAL"
    UNKNOWN = "UNKNOWN"

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


# ==================== Model Metadata Mapping ====================

# Define all model metadata
MODEL_METADATA: Dict[GRBModelsCombinations, ModelMetadata] = {
    # PL - Power Law
    GRBModelsCombinations.PL: ModelMetadata(
        color="blue",
        total_params=3,
        free_params=2,
        complexity_order=0,
        latex_name=r"\pl",
        base_parameters=["amp_pl", "e_piv_pl", "index1_pl"],
        component_parameters=["amp_pl", "e_piv_pl", "add_index_pl"],
        base_schema=[
            ParameterDef("amplitude", False, False, True),
            ParameterDef("e_pivot", True, False, True),
            ParameterDef("index1", False, False, False),
        ],
        component_schema=[
            ParameterDef("amplitude_pl", False, False, True),
            ParameterDef("e_pivot_pl", True, False, True),
            ParameterDef("index2_pl", False, False, False),
        ],
        is_standalone=True,
        is_allowed=True,
    ),
    # BB - Black Body (component only)
    GRBModelsCombinations.BB: ModelMetadata(
        color="purple",
        total_params=2,
        free_params=2,
        complexity_order=99,  # Not a single model
        latex_name=r"\bb",
        base_parameters=["amp_bb", "kt_bb"],
        component_parameters=["amp_bb", "kt_bb"],
        base_schema=[
            ParameterDef("amplitude_bb", False, False, True),
            ParameterDef("kt_temperature", False, False, True),
        ],
        component_schema=[
            ParameterDef("amplitude_bb", False, False, True),
            ParameterDef("kt_temperature", False, False, True),
        ],
        is_standalone=False,
        is_allowed=False,
    ),
    # PL_BB - Power Law + Black Body
    GRBModelsCombinations.PL_BB: ModelMetadata(
        color="blue",
        total_params=5,
        free_params=4,
        complexity_order=99,
        latex_name=r"\plbb",
        base_parameters=["amp_pl", "e_piv_pl", "index1_pl", "amp_bb", "kt_bb"],
        component_parameters=None,
        base_schema=[],  # Composite - built dynamically
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # CPL - Cutoff Power Law
    GRBModelsCombinations.CPL: ModelMetadata(
        color="orange",
        total_params=4,
        free_params=3,
        complexity_order=1,
        latex_name=r"\cpl",
        base_parameters=["amp_cpl", "e_peak_cpl", "index1_cpl", "e_piv_cpl"],
        component_parameters=None,
        base_schema=[
            ParameterDef("amplitude", False, False, True),
            ParameterDef("peak_energy", False, False, True),
            ParameterDef("index1", False, False, False),
            ParameterDef("e_pivot", True, False, True),
        ],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # CPL_PL
    # GRBModelsCombinations.CPL_PL: ModelMetadata(
    #     color="orange",
    #     total_params=7,
    #     free_params=5,
    #     complexity_order=99,
    #     latex_name=r"\cplpl",
    #     base_parameters=["amp_pl", "e_piv_pl", "add_index_pl", "amp_cpl", "e_peak_cpl", "index1_cpl", "e_piv_cpl"],
    #     component_parameters=None,
    #     base_schema=[],
    #     component_schema=None,
    #     is_standalone=True,
    #     is_allowed=True,
    # ),
    # CPL_BB
    GRBModelsCombinations.CPL_BB: ModelMetadata(
        color="orange",
        total_params=6,
        free_params=5,
        complexity_order=99,
        latex_name=r"\cplbb",
        base_parameters=["amp_cpl", "e_peak_cpl", "index1_cpl", "e_piv_cpl", "amp_bb", "kt_bb"],
        component_parameters=None,
        base_schema=[],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # CPL_PL_BB
    GRBModelsCombinations.CPL_PL_BB: ModelMetadata(
        color="orange",
        total_params=9,
        free_params=7,
        complexity_order=99,
        latex_name=r"\cplplbb",
        base_parameters=[
            "amp_pl",
            "e_piv_pl",
            "add_index_pl",
            "amp_cpl",
            "e_peak_cpl",
            "index1_cpl",
            "e_piv_cpl",
            "amp_bb",
            "kt_bb",
        ],
        component_parameters=None,
        base_schema=[],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # BAND
    GRBModelsCombinations.BAND: ModelMetadata(
        color="green",
        total_params=4,
        free_params=4,
        complexity_order=2,
        latex_name=r"\band",
        base_parameters=["amp_band", "e_peak_band", "index1_band", "index2_band"],
        component_parameters=None,
        base_schema=[
            ParameterDef("amplitude", False, False, True),
            ParameterDef("peak_energy", False, False, True),
            ParameterDef("index1", False, False, False),
            ParameterDef("index2", False, False, False),
        ],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # BAND_PL
    # GRBModelsCombinations.BAND_PL: ModelMetadata(
    #     color="green",
    #     total_params=7,
    #     free_params=6,
    #     complexity_order=99,
    #     latex_name=r"\bandpl",
    #     base_parameters=["amp_pl", "e_piv_pl", "add_index_pl", "amp_band", "e_peak_band", "index1_band", "index2_band"],
    #     component_parameters=None,
    #     base_schema=[],
    #     component_schema=None,
    #     is_standalone=True,
    #     is_allowed=True,
    # ),
    # BAND_BB
    GRBModelsCombinations.BAND_BB: ModelMetadata(
        color="green",
        total_params=6,
        free_params=6,
        complexity_order=99,
        latex_name=r"\bandbb",
        base_parameters=["amp_band", "e_peak_band", "index1_band", "index2_band", "amp_bb", "kt_bb"],
        component_parameters=None,
        base_schema=[],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # BAND_PL_BB
    GRBModelsCombinations.BAND_PL_BB: ModelMetadata(
        color="green",
        total_params=9,
        free_params=8,
        complexity_order=99,
        latex_name=r"\bandplbb",
        base_parameters=[
            "amp_pl",
            "e_piv_pl",
            "add_index_pl",
            "amp_band",
            "e_peak_band",
            "index1_band",
            "index2_band",
            "amp_bb",
            "kt_bb",
        ],
        component_parameters=None,
        base_schema=[],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # SBPL - Smoothly Broken Power Law
    GRBModelsCombinations.SBPL: ModelMetadata(
        color="red",
        total_params=6,
        free_params=4,
        complexity_order=2,
        latex_name=r"\sbpl",
        base_parameters=["amp_sbpl", "e_piv_sbpl", "index1_sbpl", "e_break_sbpl", "delta_sbpl", "index2_sbpl"],
        component_parameters=None,
        base_schema=[
            ParameterDef("amplitude", False, False, True),
            ParameterDef("e_pivot", True, False, True),
            ParameterDef("index1", False, False, False),
            ParameterDef("break_energy", False, False, True),
            ParameterDef("delta", True, False, True),
            ParameterDef("index2", False, False, False),
        ],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # SBPL_PL
    # GRBModelsCombinations.SBPL_PL: ModelMetadata(
    #     color="red",
    #     total_params=9,
    #     free_params=6,
    #     complexity_order=99,
    #     latex_name=r"\sbplpl",
    #     base_parameters=[
    #         "amp_pl",
    #         "e_piv_pl",
    #         "add_index_pl",
    #         "amp_sbpl",
    #         "e_piv_sbpl",
    #         "index1_sbpl",
    #         "e_break_sbpl",
    #         "delta_sbpl",
    #         "index2_sbpl",
    #     ],
    #     component_parameters=None,
    #     base_schema=[],
    #     component_schema=None,
    #     is_standalone=True,
    #     is_allowed=True,
    # ),
    # SBPL_BB
    GRBModelsCombinations.SBPL_BB: ModelMetadata(
        color="red",
        total_params=8,
        free_params=6,
        complexity_order=99,
        latex_name=r"\sbplbb",
        base_parameters=[
            "amp_sbpl",
            "e_piv_sbpl",
            "index1_sbpl",
            "e_break_sbpl",
            "delta_sbpl",
            "index2_sbpl",
            "amp_bb",
            "kt_bb",
        ],
        component_parameters=None,
        base_schema=[],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
    # SBPL_PL_BB
    GRBModelsCombinations.SBPL_PL_BB: ModelMetadata(
        color="red",
        total_params=11,
        free_params=8,
        complexity_order=99,
        latex_name=r"\sbplplbb",
        base_parameters=[
            "amp_pl",
            "e_piv_pl",
            "add_index_pl",
            "amp_sbpl",
            "e_piv_sbpl",
            "index1_sbpl",
            "e_break_sbpl",
            "delta_sbpl",
            "index2_sbpl",
            "amp_bb",
            "kt_bb",
        ],
        component_parameters=None,
        base_schema=[],
        component_schema=None,
        is_standalone=True,
        is_allowed=True,
    ),
}


# Validate that all models have metadata
def _validate_model_metadata():
    """Validate that all GRBModelsCombinations members have complete metadata."""
    missing = []
    for model in GRBModelsCombinations:
        if model not in MODEL_METADATA:
            missing.append(model.name)

    if missing:
        raise ValueError(
            f"Missing metadata for models: {', '.join(missing)}. "
            f"All GRBModelsCombinations members must have MODEL_METADATA entries."
        )

    # Validate metadata completeness
    for model, metadata in MODEL_METADATA.items():
        if metadata.is_standalone and not metadata.base_parameters:
            raise ValueError(f"Standalone model {model.name} must have base_parameters")


# Run validation at module import
_validate_model_metadata()


# ==================== Model Group Type Enum ====================


class ModelGroupType(Enum):
    """Enumeration of model groups for GOOD model selection."""

    BASE = "BASE"
    BB = "BB"
    # PL = "PL"
    PLBB = "PLBB"

    @property
    def models(self) -> List[GRBModelsCombinations]:
        """Get the list of models in this group."""
        return _MODEL_GROUP_MAPPINGS[self]

    @property
    def model_names(self) -> List[str]:
        """Get the uppercase string names of models in this group."""
        return [m.name_upper for m in self.models]


# Define model group memberships
_MODEL_GROUP_MAPPINGS: Dict[ModelGroupType, List[GRBModelsCombinations]] = {
    ModelGroupType.BASE: [
        GRBModelsCombinations.PL,
        GRBModelsCombinations.CPL,
        GRBModelsCombinations.BAND,
        GRBModelsCombinations.SBPL,
    ],
    ModelGroupType.BB: [
        GRBModelsCombinations.PL_BB,
        GRBModelsCombinations.CPL_BB,
        GRBModelsCombinations.BAND_BB,
        GRBModelsCombinations.SBPL_BB,
    ],
    # ModelGroupType.PL: [GRBModelsCombinations.CPL_PL, GRBModelsCombinations.BAND_PL, GRBModelsCombinations.SBPL_PL],
    ModelGroupType.PLBB: [
        GRBModelsCombinations.CPL_PL_BB,
        GRBModelsCombinations.BAND_PL_BB,
        GRBModelsCombinations.SBPL_PL_BB,
    ],
}


# ==================== Conversion Utilities ====================


def str_to_model(name: str) -> GRBModelsCombinations:
    """Convert string to GRBModelsCombinations enum.

    Parameters
    ----------
    name : str
        Model name (case-insensitive, e.g., 'cpl', 'CPL', 'Cpl').

    Returns
    -------
    GRBModelsCombinations
        The corresponding enum member.

    Raises
    ------
    ValueError
        If the model name is invalid.
    """
    if not isinstance(name, str):
        raise TypeError(f"Expected str, got {type(name).__name__}")

    name_upper = name.strip().upper()

    try:
        return GRBModelsCombinations[name_upper]
    except KeyError:
        allowed = sorted(m.name_upper for m in GRBModelsCombinations if m.is_allowed)
        raise ValueError(
            f"Invalid model '{name}'. "
            f"Valid models: {', '.join(allowed)}. "
            f"Use string like 'CPL' or enum GRBModelsCombinations.CPL"
        )


def model_to_str(model: Union[str, GRBModelsCombinations]) -> str:
    """Convert model to uppercase string.

    Parameters
    ----------
    model : Union[str, GRBModelsCombinations]
        Model as string or enum.

    Returns
    -------
    str
        Uppercase model name.

    Examples
    --------
    >>> model_to_str(GRBModelsCombinations.CPL)
    'CPL'
    >>> model_to_str('cpl')
    'CPL'
    """
    if isinstance(model, str):
        return model.strip().upper()
    elif isinstance(model, GRBModelsCombinations):
        return model.name_upper
    else:
        raise TypeError(f"Expected str or GRBModelsCombinations, got {type(model).__name__}")


def normalize_model(model: Union[str, GRBModelsCombinations]) -> GRBModelsCombinations:
    """Normalize model input to enum.

    Converts string to enum, or returns enum unchanged.

    Parameters
    ----------
    model : Union[str, GRBModelsCombinations]
        Model as string or enum.

    Returns
    -------
    GRBModelsCombinations
        The model enum.
    """
    if isinstance(model, str):
        return str_to_model(model)
    elif isinstance(model, GRBModelsCombinations):
        return model
    else:
        raise TypeError(f"Expected str or GRBModelsCombinations, got {type(model).__name__}")


def accepts_string_or_enum(*param_names):
    """Decorator to convert string parameters to enums.

    Automatically converts specified string parameters to GRBModelsCombinations
    before calling the decorated function.

    Parameters
    ----------
    *param_names : str
        Names of parameters to convert.

    Examples
    --------
    >>> @accepts_string_or_enum('model_a', 'model_b')
    ... def compare(model_a, model_b):
    ...     # model_a and model_b are now guaranteed to be enums
    ...     return model_a.free_params < model_b.free_params
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect

            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Convert specified parameters
            for param_name in param_names:
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if value is not None and isinstance(value, str):
                        bound.arguments[param_name] = str_to_model(value)

            return func(*bound.args, **bound.kwargs)

        return wrapper

    return decorator
