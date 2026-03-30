"""Created on Jan 07 14:42:35 2026

NOTE: Most constants in this file are AUTO-GENERATED FROM ENUMS.
See grb_enums.py for the source of truth for model metadata.
This file maintains backward compatibility with existing code.
"""

__all__ = [
    "MODEL_COLORS",
    "MODEL_PARAMETERS",
    "NOK_THRESHOLD",
    "OK_THRESHOLD",
    "kev_to_erg",
    "model_n_pars",
    "short_to_long",
    "MODEL_ORDER",
    "LATEX_MODEL_NAMES",
    "ALLOWED_MODELS",
    "SINGLE_MODEL_FREE_PARAMS",
    "SINGLE_MODEL_ORDER",
    "COMPONENT_FREE_PARAMS",
    "BASE_PARAM_SCHEMAS",
    "COMPONENT_PARAM_SCHEMAS",
    "MODEL_GROUPS",
    "GRB_COLORS",
    "LABEL_FONT_SIZE",
    "LEGEND_TITLE_FONT_SIZE",
    "LEGEND_FONT_SIZE",
    "TICK_FONT_SIZE",
]

from .grb_enums import GRBModelsCombinations as gmC
from .grb_enums import ModelGroupType

LABEL_FONT_SIZE = 12
LEGEND_FONT_SIZE = 11
LEGEND_TITLE_FONT_SIZE = LEGEND_FONT_SIZE
TICK_FONT_SIZE = 12

OK_THRESHOLD = 0.4
NOK_THRESHOLD = 1.0

kev_to_erg = 1.6021766208e-09

GRB_COLORS = ["#0072B2", "#E69F00", "#CC79A7", "#009E73"]
GRB_EP_COLOR = {"T90": "r", "TR": "g", "EX": "b"}

# ==================== AUTO-GENERATED FROM ENUMS - DO NOT EDIT DIRECTLY ====================

MODEL_COLORS = {m: m.color for m in gmC}

short_to_long = {
    "150210A": "GRB150210935",
    "110731A": "GRB110731465",
    "110721A": "GRB110721200",
    "080916C": "GRB080916009",
}

# AUTO-GENERATED FROM ENUMS - DO NOT EDIT DIRECTLY
model_n_pars = {m: m.total_params for m in gmC}

# AUTO-GENERATED FROM ENUMS - DO NOT EDIT DIRECTLY
MODEL_PARAMETERS = {m: m.base_parameters for m in gmC}

# Keep the original order for backward compatibility
MODEL_ORDER = [
    "PL",
    "PL_BB",
    "SBPL",
    # "SBPL_PL",
    "SBPL_BB",
    "SBPL_PL_BB",
    "BAND",
    # "BAND_PL",
    "BAND_BB",
    "BAND_PL_BB",
    "CPL",
    # "CPL_PL",
    "CPL_BB",
    "CPL_PL_BB",
]

# AUTO-GENERATED FROM ENUMS - DO NOT EDIT DIRECTLY
LATEX_MODEL_NAMES = {m.name_upper: m.latex_name for m in gmC}

# ==================== Model Selection Configuration ====================
# AUTO-GENERATED FROM ENUMS - DO NOT EDIT DIRECTLY

ALLOWED_MODELS = {m.name_upper for m in gmC if m.is_allowed}

# Single models only (PL, CPL, BAND, SBPL)
SINGLE_MODEL_FREE_PARAMS = {m.name_upper: m.free_params for m in gmC if m in [gmC.PL, gmC.CPL, gmC.BAND, gmC.SBPL]}

SINGLE_MODEL_ORDER = {m.name_upper: m.complexity_order for m in gmC if m in [gmC.PL, gmC.CPL, gmC.BAND, gmC.SBPL]}

# Component-free parameters (PL and BB when used as components)
COMPONENT_FREE_PARAMS = {"PL": 2, "BB": 2}

# ==================== Parameter Schemas for FITS Reading ====================
# AUTO-GENERATED FROM ENUMS - DO NOT EDIT DIRECTLY

# Convert ParameterDef to tuples for backward compatibility
BASE_PARAM_SCHEMAS = {
    m.name_upper: [(p.name, p.is_fixed, p.has_bounds) for p in m.base_schema]
    for m in gmC
    if m.base_schema and m in [gmC.PL, gmC.CPL, gmC.BAND, gmC.SBPL]
}

COMPONENT_PARAM_SCHEMAS = {
    "PL": [(p.name, p.is_fixed, p.has_bounds) for p in gmC.PL.component_schema],
    "BB": [(p.name, p.is_fixed, p.has_bounds) for p in gmC.BB.base_schema],
}

# ==================== Model Groups for GOOD Selection ====================
# AUTO-GENERATED FROM ENUMS - DO NOT EDIT DIRECTLY

MODEL_GROUPS = {group.value: group.model_names for group in ModelGroupType}
