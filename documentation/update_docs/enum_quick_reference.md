# Enum-Based API Quick Reference

**Quick start guide for using the new enum-based API**

## TL;DR

✅ **Old string-based code still works - no changes needed**  
✨ **New enum-based code provides type safety and better IDE support**

## Basic Usage

### Option 1: Keep Using Strings (Backward Compatible)

```python
from src.grb_research.safe_good_best import compare_models

result = compare_models('CPL', 100.0, 'BAND', 95.0)
print(result)  # 'CPL'
```

### Option 2: Use Enums (Recommended)

```python
from src.grb_research.grb_enums import GRBModelsCombinations as Models

model = Models.CPL
print(model.free_params)  # 3
print(model.color)  # 'orange'
```

## Quick Examples

### Get Model Info

```python
from src.grb_research.grb_enums import GRBModelsCombinations

cpl = GRBModelsCombinations.CPL

# All metadata in one place
print(cpl.name_upper)      # 'CPL'
print(cpl.color)           # 'orange'
print(cpl.free_params)     # 3
print(cpl.total_params)    # 4
print(cpl.complexity_order) # 1
print(cpl.latex_name)      # r'\cpl'
print(cpl.is_allowed)      # True
```

### Convert Between String and Enum

```python
from src.grb_research.grb_enums import str_to_model, model_to_str

# String to enum
model = str_to_model('CPL')  # GRBModelsCombinations.CPL

# Enum to string
name = model_to_str(model)   # 'CPL'
```

### Get Model Groups

```python
from src.grb_research.grb_enums import ModelGroupType

# Get BASE group models
base_names = ModelGroupType.BASE.model_names
print(base_names)  # ['PL', 'CPL', 'BAND', 'SBPL']

# Get as enums
base_enums = ModelGroupType.BASE.models
for model in base_enums:
    print(f"{model.name_upper}: {model.free_params} params")
```

### Filter Models

```python
from src.grb_research.grb_enums import GRBModelsCombinations

# All allowed models
allowed = [m for m in GRBModelsCombinations if m.is_allowed]

# Simple models (complexity < 2)
simple = [m for m in GRBModelsCombinations if m.complexity_order < 2]

# Models with > 5 free parameters
complex_models = [m for m in GRBModelsCombinations if m.free_params > 5]
```

## Common Patterns

### Pattern: Check if model is allowed

**Before:**
```python
if model_name in ALLOWED_MODELS:
    process(model_name)
```

**After:**
```python
model = str_to_model(model_name)
if model.is_allowed:
    process(model)
```

### Pattern: Get model color

**Before:**
```python
from src.grb_research.grb_constants import GRB_COLORS
color = GRB_COLORS[gmC.CPL]
```

**After:**
```python
from src.grb_research.grb_enums import GRBModelsCombinations
color = GRBModelsCombinations.CPL.color
```

### Pattern: Get free parameters

**Before:**
```python
from src.grb_research.grb_constants import SINGLE_MODEL_FREE_PARAMS
free_params = SINGLE_MODEL_FREE_PARAMS.get('CPL', 0)
```

**After:**
```python
from src.grb_research.grb_enums import GRBModelsCombinations
free_params = GRBModelsCombinations.CPL.free_params
```

## Properties Reference

| Property | Type | Example Value |
|----------|------|---------------|
| `.name_upper` | str | `'CPL'` |
| `.color` | str | `'orange'` |
| `.total_params` | int | `4` |
| `.free_params` | int | `3` |
| `.complexity_order` | int | `1` |
| `.latex_name` | str | `r'\cpl'` |
| `.base_parameters` | List[str] | `['amp_cpl', ...]` |
| `.is_standalone` | bool | `True` |
| `.is_allowed` | bool | `True` |

## Available Models

```python
GRBModelsCombinations.PL        # Power Law
GRBModelsCombinations.CPL       # Cutoff Power Law
GRBModelsCombinations.BAND      # Band Function
GRBModelsCombinations.SBPL      # Smoothly Broken Power Law
GRBModelsCombinations.PL_BB     # PL + Black Body
GRBModelsCombinations.CPL_BB    # CPL + BB
GRBModelsCombinations.CPL_PL    # CPL + PL
GRBModelsCombinations.CPL_PL_BB # CPL + PL + BB
# ... and more
```

## Model Groups

```python
ModelGroupType.BASE   # ['PL', 'CPL', 'BAND', 'SBPL']
ModelGroupType.BB     # ['PL_BB', 'CPL_BB', 'BAND_BB', 'SBPL_BB']
ModelGroupType.PL     # ['CPL_PL', 'BAND_PL', 'SBPL_PL']
ModelGroupType.PLBB   # ['CPL_PL_BB', 'BAND_PL_BB', 'SBPL_PL_BB']
```

## Error Messages

Invalid model names now give helpful errors:

```python
try:
    model = str_to_model('INVALID')
except ValueError as e:
    print(e)
# "Invalid model 'INVALID'. Valid models: BAND, BAND_BB, ...
# Use string like 'CPL' or enum GRBModelsCombinations.CPL"
```

## Documentation

- **Full Guide:** `documentation/update_docs/enum_migration_guide.md`
- **API Reference:** `documentation/update_docs/enum_api_reference.md`
- **Implementation:** `documentation/update_docs/enum_implementation_summary.md`

## Benefits

✅ Type safety - catch errors at import time  
✅ IDE autocomplete - see all options  
✅ Better errors - helpful messages  
✅ Cleaner code - `model.color` vs dict lookup  
✅ 100% backward compatible - no breaking changes  

## Questions?

See the full migration guide for more examples and detailed explanations.

