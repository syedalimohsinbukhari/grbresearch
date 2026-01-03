"""Created on Dec 20 00:42:44 2025"""

from enum import Enum
from typing import Dict


class ModelStatus(Enum):
    """Custom flags for model evaluation"""

    INVALID = -2  # Cannot be evaluated (missing BASE)
    UNNECESSARY = -1  # Simpler model failed, consider me instead
    REJECTED = 0  # Failed comparison
    ACCEPTED = 1  # Passed comparison
    # DOMINANT = 2  # Significantly better (for standout performers)


def analyze_model_hierarchy(is_good: Dict) -> Dict[str, ModelStatus]:
    """
    Analyze model hierarchy with custom flags based on comparison rules.

    Rules:
    1. BASE must be present in model name for comparison
    2. BASE -> BASE_XX requires >25 improvement
    3. BASE -> BASE_XX_YY requires:
       - >50 if both BASE_XX and BASE_YY are REJECTED
       - >25 from best BASE_XX/BASE_YY if either is ACCEPTED
    """

    # Extract BASE information
    base_name, base_value = is_good["BASE"]

    # Initialize result dictionary
    results = {}

    # Track which models contain BASE
    base_containing_models = {}
    other_models = {}

    # Separate models that contain BASE from those that don't
    for key, (model_name, value) in is_good.items():
        if key == "BASE":
            continue

        if base_name in model_name:
            base_containing_models[model_name] = value
        else:
            other_models[model_name] = value

    # Initialize results for non-BASE containing models
    for model_name in other_models:
        results[model_name] = ModelStatus.INVALID.value

    # If no models contain BASE, mark BASE as ACCEPTED and return
    if not base_containing_models:
        results[base_name] = ModelStatus.ACCEPTED.value
        return results

    # Step 1: Evaluate single-extension models (BASE_XX)
    single_extension = {}
    double_extension = {}

    for model_name, value in base_containing_models.items():
        # Count additional components (assuming underscore separation)
        additional_components = model_name.count("_") - base_name.count("_")

        if additional_components == 1:
            single_extension[model_name] = value
        elif additional_components == 2:
            double_extension[model_name] = value

    # Evaluate single extension models
    accepted_single = {}
    for model_name, value in single_extension.items():
        diff = base_value - value
        if diff > 25:
            results[model_name] = ModelStatus.ACCEPTED.value
            accepted_single[model_name] = value
        else:
            results[model_name] = ModelStatus.REJECTED.value

    # Step 2: Evaluate double extension models (BASE_XX_YY)
    base_accepted = True  # Assume BASE is accepted initially

    for model_name, value in double_extension.items():
        # Determine if this is a combined model (contains two extensions)
        # Extract the two extensions
        suffix = model_name.replace(base_name + "_", "")
        extensions = suffix.split("_")

        # Find corresponding single extension models
        relevant_singles = []
        for ext in extensions:
            single_name = f"{base_name}_{ext}"
            if single_name in single_extension:
                relevant_singles.append(single_name)

        if len(relevant_singles) == 2:
            # This is a combination of two single extensions
            single1_status = results.get(relevant_singles[0], ModelStatus.REJECTED.value)
            single2_status = results.get(relevant_singles[1], ModelStatus.REJECTED.value)

            if single1_status == ModelStatus.ACCEPTED.value or single2_status == ModelStatus.ACCEPTED.value:
                # At least one single extension was accepted
                # Compare against the best accepted single
                best_single_value = float("inf")
                for single_name in relevant_singles:
                    if results.get(single_name) == ModelStatus.ACCEPTED.value:
                        best_single_value = min(best_single_value, base_containing_models[single_name])

                if best_single_value - value > 25:
                    results[model_name] = ModelStatus.ACCEPTED.value
                    base_accepted = False  # BASE is beaten
                else:
                    results[model_name] = ModelStatus.REJECTED.value
            else:
                # Neither single extension was accepted
                # Compare directly against BASE
                if base_value - value > 50:
                    results[model_name] = ModelStatus.ACCEPTED.value
                    base_accepted = False  # BASE is beaten
                else:
                    results[model_name] = ModelStatus.REJECTED.value
        else:
            # Not a clear combination, use default comparison
            if base_value - value > 50:
                results[model_name] = ModelStatus.ACCEPTED.value
                base_accepted = False
            else:
                results[model_name] = ModelStatus.REJECTED.value

    # Step 3: Handle BASE status
    if not base_accepted:
        results[base_name] = ModelStatus.UNNECESSARY.value
    else:
        # Check if any single extension was accepted
        any_accepted = any(results.get(model) == ModelStatus.ACCEPTED.value for model in single_extension.keys())

        if any_accepted:
            results[base_name] = ModelStatus.UNNECESSARY.value
        else:
            results[base_name] = ModelStatus.ACCEPTED.value

    # Add remaining base-containing models that weren't processed
    for model_name, value in base_containing_models.items():
        if model_name not in results:
            # Default comparison for other models
            additional_components = model_name.count("_") - base_name.count("_")
            threshold = 50 if additional_components >= 2 else 25

            if base_value - value > threshold:
                results[model_name] = ModelStatus.ACCEPTED.value
            else:
                results[model_name] = ModelStatus.REJECTED.value

    return results
