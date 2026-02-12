# Enum API Reference

**Date:** February 12, 2026  
**Module:** `src.grb_research.grb_enums`

## Overview

This document provides a complete reference for the enum-based API introduced in the GRB model selection system.

## Table of Contents

1. [Dataclasses](#dataclasses)
2. [GRBModelsCombinations Enum](#grbmodelscombinations-enum)
3. [ModelGroupType Enum](#modelgrouptype-enum)
4. [Conversion Utilities](#conversion-utilities)
5. [Usage Examples](#usage-examples)

---

## Dataclasses

### ParameterDef

Type-safe parameter definition.

```python
@dataclass(frozen=True)
class ParameterDef:
    name: str          # Parameter name (e.g., 'amplitude', 'peak_energy')
    is_fixed: bool     # Whether this parameter has a fixed value
    has_bounds: bool   # Whether this parameter has bounds constraints
```

**Example:**
```python
param = ParameterDef("amplitude", False, False)
print(param.name)  # 'amplitude'
print(param.is_fixed)  # False
```

### ModelMetadata

Complete metadata for a GRB spectral model.

```python
@dataclass(frozen=True)
class ModelMetadata:
    color: str                                # Plotting color
    total_params: int                         # Total parameters including fixed
    free_params: int                          # Free parameters for C-stat
    complexity_order: int                     # Complexity order (0=simplest)
    latex_name: str                           # LaTeX representation
    base_parameters: List[str]                # Parameter names (base usage)
    component_parameters: Optional[List[str]] # Parameter names (component usage)
    base_schema: List[ParameterDef]          # Parameter definitions (base)
    component_schema: Optional[List[ParameterDef]]  # Parameter definitions (component)
    is_standalone: bool                       # Can be used standalone
    is_allowed: bool                          # Is in ALLOWED_MODELS
```

**Example:**
```python
from src.grb_research.grb_enums import GRBModelsCombinations

metadata = GRBModelsCombinations.CPL.metadata
print(metadata.color)  # 'orange'
print(metadata.free_params)  # 3
```

---

## GRBModelsCombinations Enum

Enumeration of all GRB spectral models.

### Members

```python
class GRBModelsCombinations(Enum):
    PL = "pl"              # Power Law
    BB = "bb"              # Black Body (component only)
    PL_BB = "pl_bb"        # Power Law + Black Body
    
    CPL = "cpl"            # Cutoff Power Law
    CPL_PL = "cpl_pl"      # CPL + PL component
    CPL_BB = "cpl_bb"      # CPL + BB component
    CPL_PL_BB = "cpl_pl_bb"  # CPL + PL + BB
    
    BAND = "band"          # Band function
    BAND_PL = "band_pl"    # Band + PL component
    BAND_BB = "band_bb"    # Band + BB component
    BAND_PL_BB = "band_pl_bb"  # Band + PL + BB
    
    SBPL = "sbpl"          # Smoothly Broken Power Law
    SBPL_PL = "sbpl_pl"    # SBPL + PL component
    SBPL_BB = "sbpl_bb"    # SBPL + BB component
    SBPL_PL_BB = "sbpl_pl_bb"  # SBPL + PL + BB
```

### Properties

All properties are read-only and computed from the MODEL_METADATA mapping.

#### `.name_upper` → str

Get uppercase name of the model.

```python
model = GRBModelsCombinations.CPL
print(model.name_upper)  # 'CPL'
```

#### `.metadata` → ModelMetadata

Get complete metadata for this model.

```python
model = GRBModelsCombinations.BAND
metadata = model.metadata
print(metadata.free_params)  # 4
```

#### `.color` → str

Get plotting color.

```python
print(GRBModelsCombinations.PL.color)  # 'blue'
print(GRBModelsCombinations.CPL.color)  # 'orange'
print(GRBModelsCombinations.BAND.color)  # 'green'
print(GRBModelsCombinations.SBPL.color)  # 'red'
```

#### `.total_params` → int

Get total number of parameters (including fixed).

```python
print(GRBModelsCombinations.PL.total_params)  # 3
print(GRBModelsCombinations.CPL.total_params)  # 4
print(GRBModelsCombinations.BAND_PL_BB.total_params)  # 9
```

#### `.free_params` → int

Get number of free parameters (for C-stat comparison).

```python
print(GRBModelsCombinations.PL.free_params)  # 2
print(GRBModelsCombinations.CPL.free_params)  # 3
print(GRBModelsCombinations.BAND.free_params)  # 4
print(GRBModelsCombinations.SBPL.free_params)  # 4
```

#### `.complexity_order` → int

Get complexity order for single models (0=simplest).

```python
print(GRBModelsCombinations.PL.complexity_order)  # 0 (simplest)
print(GRBModelsCombinations.CPL.complexity_order)  # 1
print(GRBModelsCombinations.BAND.complexity_order)  # 2
print(GRBModelsCombinations.SBPL.complexity_order)  # 2
```

#### `.latex_name` → str

Get LaTeX representation for publications.

```python
print(GRBModelsCombinations.CPL.latex_name)  # r'\cpl'
print(GRBModelsCombinations.BAND_PL_BB.latex_name)  # r'\bandplbb'
```

#### `.base_parameters` → List[str]

Get parameter names when used as base model.

```python
params = GRBModelsCombinations.CPL.base_parameters
print(params)  # ['amp_cpl', 'e_peak_cpl', 'index1_cpl', 'e_piv_cpl']
```

#### `.component_parameters` → Optional[List[str]]

Get parameter names when used as component (PL only).

```python
# PL has different parameters when used as component
base_params = GRBModelsCombinations.PL.base_parameters
print(base_params)  # ['amp_pl', 'e_piv_pl', 'index1_pl']

comp_params = GRBModelsCombinations.PL.component_parameters
print(comp_params)  # ['amp_pl', 'e_piv_pl', 'add_index_pl']
```

#### `.base_schema` → List[ParameterDef]

Get parameter schema for base model usage.

```python
schema = GRBModelsCombinations.CPL.base_schema
for param_def in schema:
    print(f"{param_def.name}: fixed={param_def.is_fixed}")
# amplitude: fixed=False
# peak_energy: fixed=False
# index1: fixed=False
# e_pivot: fixed=True
```

#### `.component_schema` → Optional[List[ParameterDef]]

Get parameter schema for component usage.

```python
schema = GRBModelsCombinations.PL.component_schema
for param_def in schema:
    print(param_def.name)
# amplitude_pl
# e_pivot_pl
# index2_pl
```

#### `.is_standalone` → bool

Check if this can be used as a standalone model.

```python
print(GRBModelsCombinations.CPL.is_standalone)  # True
print(GRBModelsCombinations.BB.is_standalone)  # False (component only)
```

#### `.is_allowed` → bool

Check if this model is in ALLOWED_MODELS set.

```python
print(GRBModelsCombinations.CPL.is_allowed)  # True
print(GRBModelsCombinations.BB.is_allowed)  # False
```

---

## ModelGroupType Enum

Enumeration of model groups for GOOD model selection.

### Members

```python
class ModelGroupType(Enum):
    BASE = "BASE"    # Single models: PL, CPL, BAND, SBPL
    BB = "BB"        # Models with BB component
    PL = "PL"        # Models with PL component (not base)
    PLBB = "PLBB"    # Models with both PL and BB components
```

### Properties

#### `.models` → List[GRBModelsCombinations]

Get list of enum members in this group.

```python
from src.grb_research.grb_enums import ModelGroupType

base_enums = ModelGroupType.BASE.models
print(base_enums)
# [GRBModelsCombinations.PL, GRBModelsCombinations.CPL,
#  GRBModelsCombinations.BAND, GRBModelsCombinations.SBPL]
```

#### `.model_names` → List[str]

Get uppercase string names of models in this group.

```python
base_names = ModelGroupType.BASE.model_names
print(base_names)  # ['PL', 'CPL', 'BAND', 'SBPL']

bb_names = ModelGroupType.BB.model_names
print(bb_names)  # ['PL_BB', 'CPL_BB', 'BAND_BB', 'SBPL_BB']
```

---

## Conversion Utilities

### str_to_model()

Convert string to GRBModelsCombinations enum.

```python
def str_to_model(name: str) -> GRBModelsCombinations
```

**Parameters:**
- `name` (str): Model name (case-insensitive)

**Returns:**
- `GRBModelsCombinations`: The corresponding enum member

**Raises:**
- `TypeError`: If input is not a string
- `ValueError`: If model name is invalid

**Examples:**
```python
from src.grb_research.grb_enums import str_to_model

# Case-insensitive
model1 = str_to_model('CPL')
model2 = str_to_model('cpl')
model3 = str_to_model('Cpl')
assert model1 == model2 == model3

# Whitespace is stripped
model4 = str_to_model('  CPL  ')
assert model4 == model1

# Invalid model raises helpful error
try:
    str_to_model('INVALID')
except ValueError as e:
    print(e)
    # "Invalid model 'INVALID'. Valid models: BAND, BAND_BB, ...
    # Use string like 'CPL' or enum GRBModelsCombinations.CPL"
```

### model_to_str()

Convert model to uppercase string.

```python
def model_to_str(model: Union[str, GRBModelsCombinations]) -> str
```

**Parameters:**
- `model` (Union[str, GRBModelsCombinations]): Model as string or enum

**Returns:**
- `str`: Uppercase model name

**Raises:**
- `TypeError`: If input is neither string nor enum

**Examples:**
```python
from src.grb_research.grb_enums import GRBModelsCombinations, model_to_str

# From enum
name1 = model_to_str(GRBModelsCombinations.CPL)
print(name1)  # 'CPL'

# From string (normalizes case)
name2 = model_to_str('cpl')
print(name2)  # 'CPL'

# Strips whitespace
name3 = model_to_str('  cpl  ')
print(name3)  # 'CPL'
```

### normalize_model()

Normalize model input to enum.

```python
def normalize_model(model: Union[str, GRBModelsCombinations]) -> GRBModelsCombinations
```

**Parameters:**
- `model` (Union[str, GRBModelsCombinations]): Model as string or enum

**Returns:**
- `GRBModelsCombinations`: The model enum

**Raises:**
- `TypeError`: If input is neither string nor enum
- `ValueError`: If string model name is invalid

**Examples:**
```python
from src.grb_research.grb_enums import GRBModelsCombinations, normalize_model

# From string
m1 = normalize_model('CPL')
print(m1)  # GRBModelsCombinations.CPL

# From enum (returns unchanged)
m2 = normalize_model(GRBModelsCombinations.CPL)
print(m2)  # GRBModelsCombinations.CPL

# Both produce same result
assert m1 == m2

# Use in functions
def process(model: Union[str, GRBModelsCombinations]):
    m = normalize_model(model)  # Convert to enum
    return m.free_params

print(process('CPL'))  # 3
print(process(GRBModelsCombinations.CPL))  # 3
```

### accepts_string_or_enum()

Decorator to automatically convert string parameters to enums.

```python
def accepts_string_or_enum(*param_names)
```

**Parameters:**
- `*param_names` (str): Names of parameters to convert

**Returns:**
- Decorator function

**Examples:**
```python
from src.grb_research.grb_enums import accepts_string_or_enum, GRBModelsCombinations

@accepts_string_or_enum('model_a', 'model_b')
def compare_free_params(model_a, model_b):
    # model_a and model_b are guaranteed to be enums here
    return model_a.free_params < model_b.free_params

# Can call with strings
result1 = compare_free_params('PL', 'CPL')
print(result1)  # True (2 < 3)

# Or with enums
result2 = compare_free_params(
    GRBModelsCombinations.PL,
    GRBModelsCombinations.CPL
)
print(result2)  # True

# Or mix
result3 = compare_free_params('PL', GRBModelsCombinations.CPL)
print(result3)  # True
```

---

## Usage Examples

### Example 1: Iterating Over All Models

```python
from src.grb_research.grb_enums import GRBModelsCombinations

# Get all allowed models
for model in GRBModelsCombinations:
    if model.is_allowed:
        print(f"{model.name_upper}: {model.free_params} free params")
```

### Example 2: Filtering Models

```python
# Get all single models
single_models = [
    m for m in GRBModelsCombinations 
    if m in [GRBModelsCombinations.PL, GRBModelsCombinations.CPL,
             GRBModelsCombinations.BAND, GRBModelsCombinations.SBPL]
]

# Get all models with > 5 free parameters
complex_models = [m for m in GRBModelsCombinations if m.free_params > 5]

# Get all models with BB component
bb_models = [m for m in GRBModelsCombinations if 'BB' in m.name]
```

### Example 3: Building Lookup Tables

```python
# Color mapping for plotting
color_map = {m.name_upper: m.color for m in GRBModelsCombinations}

# Free params mapping
free_params_map = {m.name_upper: m.free_params for m in GRBModelsCombinations}

# LaTeX names for papers
latex_map = {m.name_upper: m.latex_name for m in GRBModelsCombinations}
```

### Example 4: Model Groups

```python
from src.grb_research.grb_enums import ModelGroupType

# Iterate over groups
for group in ModelGroupType:
    print(f"{group.value}: {group.model_names}")

# Get specific group
base_models = ModelGroupType.BASE.models
for model in base_models:
    print(f"{model.name_upper}: complexity={model.complexity_order}")
```

### Example 5: Type-Safe Function

```python
from typing import Union
from src.grb_research.grb_enums import GRBModelsCombinations, normalize_model

def get_model_info(model: Union[str, GRBModelsCombinations]) -> dict:
    """Get comprehensive model information.
    
    Parameters
    ----------
    model : Union[str, GRBModelsCombinations]
        Model name or enum.
        
    Returns
    -------
    dict
        Model information dictionary.
    """
    m = normalize_model(model)
    
    return {
        'name': m.name_upper,
        'color': m.color,
        'total_params': m.total_params,
        'free_params': m.free_params,
        'complexity': m.complexity_order,
        'latex': m.latex_name,
        'standalone': m.is_standalone,
        'allowed': m.is_allowed,
    }

# Use with string
info1 = get_model_info('CPL')

# Use with enum
info2 = get_model_info(GRBModelsCombinations.CPL)

# Both produce same result
assert info1 == info2
```

---

## Summary

The enum-based API provides:

✅ **Type Safety** - Catch errors at import time  
✅ **IDE Support** - Autocomplete for all properties  
✅ **Rich Metadata** - Access all model info from enum  
✅ **Backward Compatible** - Works with existing string-based code  
✅ **Better Errors** - Helpful messages for invalid inputs  
✅ **Cleaner Code** - Less dictionary lookups  

All functions accept both strings and enums, making migration gradual and non-breaking.

