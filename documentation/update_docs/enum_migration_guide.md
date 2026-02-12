# Enum Migration Guide

**Date:** February 12, 2026  
**Status:** ✅ COMPLETE - Phase 1 & 2 Implemented

## Overview

The GRB model selection system has been refactored to use type-safe enums internally while maintaining 100% backward compatibility with string-based APIs. This migration improves code maintainability, provides better IDE support, and catches errors at import time rather than runtime.

## What Changed?

### New Enum-Based Infrastructure

1. **`ParameterDef` Dataclass** - Type-safe parameter definitions
2. **`ModelMetadata` Dataclass** - Complete model metadata in one place
3. **`GRBModelsCombinations` Properties** - Rich enum with metadata access
4. **`ModelGroupType` Enum** - Type-safe model groups
5. **Conversion Utilities** - `str_to_model()`, `normalize_model()`

### Auto-Generated Constants

All constants in `grb_constants.py` are now auto-generated from enums:
- `GRB_COLORS` → from `model.color`
- `model_n_pars` → from `model.total_params`
- `MODEL_PARAMETERS` → from `model.base_parameters`
- `ALLOWED_MODELS` → from `model.is_allowed`
- `SINGLE_MODEL_FREE_PARAMS` → from `model.free_params`
- `MODEL_GROUPS` → from `ModelGroupType.model_names`

## How to Use

### Option 1: Continue Using Strings (Backward Compatible)

```python
from src.grb_research.safe_good_best import compare_models, compute_free_params

# All existing code works unchanged
result = compare_models('CPL', 100.0, 'BAND', 95.0)
print(result)  # 'CPL'

free_params = compute_free_params('CPL')
print(free_params)  # 3
```

### Option 2: Use Enums (Recommended for New Code)

```python
from src.grb_research.grb_enums import GRBModelsCombinations
from src.grb_research.safe_good_best import compare_models

# Type-safe with autocomplete
model = GRBModelsCombinations.CPL
print(model.free_params)  # 3
print(model.color)  # 'orange'
print(model.latex_name)  # r'\cpl'

# Works with functions
result = compare_models(
    GRBModelsCombinations.CPL, 100.0,
    GRBModelsCombinations.BAND, 95.0
)
print(result)  # 'CPL'
```

### Option 3: Mix Strings and Enums

```python
from src.grb_research.grb_enums import GRBModelsCombinations
from src.grb_research.safe_good_best import compare_models

# Functions accept both
result = compare_models(
    'CPL', 100.0,  # string
    GRBModelsCombinations.BAND, 95.0  # enum
)
print(result)  # 'CPL'
```

## Benefits

### Type Safety

**Before:**
```python
# Typo only caught at runtime
model = "CPl"  # Wrong case
free_params = compute_free_params(model)  # Fails at runtime
```

**After:**
```python
# Typo caught at import/lint time
from src.grb_research.grb_enums import GRBModelsCombinations

model = GRBModelsCombinations.CPl  # IDE shows error immediately!
```

### IDE Autocomplete

**Before:**
```python
# Must remember exact string
model = "BAND"  # No autocomplete help
```

**After:**
```python
# IDE shows all options
model = GRBModelsCombinations.  # Autocomplete shows: PL, CPL, BAND, SBPL, etc.
```

### Rich Metadata Access

**Before:**
```python
from src.grb_research.grb_constants import (
    GRB_COLORS,
    SINGLE_MODEL_FREE_PARAMS,
    LATEX_MODEL_NAMES
)

color = GRB_COLORS[gmC.CPL]
free_params = SINGLE_MODEL_FREE_PARAMS['CPL']
latex = LATEX_MODEL_NAMES['CPL']
```

**After:**
```python
from src.grb_research.grb_enums import GRBModelsCombinations

model = GRBModelsCombinations.CPL
color = model.color
free_params = model.free_params
latex = model.latex_name
```

### Model Groups

**Before:**
```python
from src.grb_research.grb_constants import MODEL_GROUPS

base_models = MODEL_GROUPS['BASE']  # ['PL', 'CPL', 'BAND', 'SBPL']
```

**After:**
```python
from src.grb_research.grb_enums import ModelGroupType

# Type-safe access
base_models = ModelGroupType.BASE.model_names  # ['PL', 'CPL', 'BAND', 'SBPL']
base_enums = ModelGroupType.BASE.models  # [GRBModelsCombinations.PL, ...]
```

## Migration Examples

### Example 1: Model Comparison

**Before (Still Works):**
```python
def select_best_model(models, cstats):
    best = models[0]
    best_cstat = cstats[0]
    
    for model, cstat in zip(models[1:], cstats[1:]):
        winner = compare_models(best, best_cstat, model, cstat)
        if winner == model:
            best, best_cstat = model, cstat
    
    return best
```

**After (Type-Safe):**
```python
from src.grb_research.grb_enums import GRBModelsCombinations

def select_best_model(
    models: List[Union[str, GRBModelsCombinations]], 
    cstats: List[float]
) -> str:
    best = models[0]
    best_cstat = cstats[0]
    
    for model, cstat in zip(models[1:], cstats[1:]):
        winner = compare_models(best, best_cstat, model, cstat)
        if winner == (model if isinstance(model, str) else model.name_upper):
            best, best_cstat = model, cstat
    
    return best if isinstance(best, str) else best.name_upper
```

### Example 2: Filtering Models

**Before (Still Works):**
```python
single_models = ['PL', 'CPL', 'BAND', 'SBPL']
filtered = [m for m in all_models if m in single_models]
```

**After (Type-Safe):**
```python
from src.grb_research.grb_enums import GRBModelsCombinations, ModelGroupType

# Option 1: Using ModelGroupType
single_models = ModelGroupType.BASE.model_names
filtered = [m for m in all_models if m in single_models]

# Option 2: Using enum property
single_enums = [m for m in GRBModelsCombinations if m.complexity_order < 3]
single_names = [m.name_upper for m in single_enums]
```

### Example 3: Accessing Model Metadata

**Before (Still Works):**
```python
from src.grb_research.grb_constants import (
    GRB_COLORS,
    MODEL_PARAMETERS,
    SINGLE_MODEL_FREE_PARAMS
)

def get_model_info(model_name):
    return {
        'color': GRB_COLORS.get(gmC[model_name.upper()]),
        'params': MODEL_PARAMETERS.get(gmC[model_name.upper()]),
        'free_params': SINGLE_MODEL_FREE_PARAMS.get(model_name.upper())
    }
```

**After (Cleaner):**
```python
from src.grb_research.grb_enums import str_to_model

def get_model_info(model_name: str):
    model = str_to_model(model_name)
    return {
        'color': model.color,
        'params': model.base_parameters,
        'free_params': model.free_params
    }
```

## Conversion Utilities

### `str_to_model(name: str) -> GRBModelsCombinations`

Convert string to enum (case-insensitive):

```python
from src.grb_research.grb_enums import str_to_model

model = str_to_model('cpl')  # Case-insensitive
print(model)  # GRBModelsCombinations.CPL
print(model.free_params)  # 3

# Invalid model raises helpful error
try:
    str_to_model('INVALID')
except ValueError as e:
    print(e)
    # "Invalid model 'INVALID'. Valid models: BAND, BAND_BB, ...
    # Use string like 'CPL' or enum GRBModelsCombinations.CPL"
```

### `normalize_model(model: Union[str, GRBModelsCombinations]) -> GRBModelsCombinations`

Accept both strings and enums:

```python
from src.grb_research.grb_enums import GRBModelsCombinations, normalize_model

# Works with strings
m1 = normalize_model('CPL')
print(m1)  # GRBModelsCombinations.CPL

# Works with enums (returns unchanged)
m2 = normalize_model(GRBModelsCombinations.CPL)
print(m2)  # GRBModelsCombinations.CPL

# Same result
print(m1 == m2)  # True
```

## Best Practices

### 1. Use Enums for Internal Logic

```python
# ✅ Good: Type-safe internal logic
def analyze_model(model: GRBModelsCombinations):
    if model.is_standalone:
        return model.free_params
    return None

# ❌ Avoid: String comparisons
def analyze_model(model: str):
    if model in ALLOWED_MODELS:
        return SINGLE_MODEL_FREE_PARAMS.get(model)
    return None
```

### 2. Accept Both at API Boundaries

```python
# ✅ Good: Flexible public API
def process_model(model: Union[str, GRBModelsCombinations]) -> Dict:
    m = normalize_model(model)  # Convert to enum internally
    return {
        'name': m.name_upper,
        'color': m.color,
        'free_params': m.free_params
    }
```

### 3. Use Type Hints

```python
# ✅ Good: Clear type expectations
def compare_with_threshold(
    model_a: Union[str, GRBModelsCombinations],
    model_b: Union[str, GRBModelsCombinations],
    threshold: float
) -> str:
    ...

# ❌ Avoid: No type hints
def compare_with_threshold(model_a, model_b, threshold):
    ...
```

### 4. Leverage Properties

```python
# ✅ Good: Use enum properties
model = GRBModelsCombinations.CPL
if model.is_allowed and model.free_params > 2:
    process(model)

# ❌ Avoid: Manual lookups
model_str = 'CPL'
if model_str in ALLOWED_MODELS and SINGLE_MODEL_FREE_PARAMS.get(model_str, 0) > 2:
    process(model_str)
```

## Common Patterns

### Pattern 1: Iterating Over Models

```python
from src.grb_research.grb_enums import GRBModelsCombinations

# Get all allowed models
allowed = [m for m in GRBModelsCombinations if m.is_allowed]

# Get all single models
singles = [m for m in GRBModelsCombinations 
           if m in [GRBModelsCombinations.PL, GRBModelsCombinations.CPL,
                   GRBModelsCombinations.BAND, GRBModelsCombinations.SBPL]]

# Get all models with BB component
bb_models = [m for m in GRBModelsCombinations if 'BB' in m.name]
```

### Pattern 2: Conditional Logic

```python
model = GRBModelsCombinations.CPL

if model.is_standalone:
    print(f"{model.name_upper} can be used alone")

if model.complexity_order < 2:
    print(f"{model.name_upper} is a simple model")

if model.free_params > 3:
    print(f"{model.name_upper} has many free parameters")
```

### Pattern 3: Building Dictionaries

```python
# Build a mapping of models to their metadata
metadata_map = {
    m.name_upper: {
        'color': m.color,
        'free_params': m.free_params,
        'latex': m.latex_name
    }
    for m in GRBModelsCombinations if m.is_allowed
}
```

## Error Messages

Enum-based code provides better error messages:

**Invalid Model:**
```
ValueError: Invalid model 'CPl'. Valid models: BAND, BAND_BB, BAND_PL, ... 
Use string like 'CPL' or enum GRBModelsCombinations.CPL
```

**Type Error:**
```
TypeError: Expected str or GRBModelsCombinations, got int
```

## Backward Compatibility Guarantees

✅ All existing string-based code continues to work  
✅ All dictionary exports unchanged  
✅ `working.py` requires zero modifications  
✅ Public function signatures accept strings  
✅ Return values remain strings where expected  

## Summary

- **Use enums internally** for type safety and better IDE support
- **Accept both strings and enums** at public API boundaries
- **Return strings** to maintain backward compatibility
- **Leverage enum properties** instead of dictionary lookups
- **Add type hints** to make the API clear

This migration provides immediate benefits (better errors, autocomplete) while maintaining complete backward compatibility.

