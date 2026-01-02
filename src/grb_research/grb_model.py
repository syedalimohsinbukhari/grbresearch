"""Created on Dec 26 14:20:28 2025"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from .grb_atomic import CovarianceMatrix, Parameter
from .grb_time import TimeInterval


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


@dataclass
class Model:
    """Represents a GRB model with its parameters and fit statistics."""

    name: str
    parameters: List[Parameter]
    _interval: Optional[TimeInterval] = None

    status: Optional[GoodnessOfFit] = None
    cstat: Optional[float] = None
    dof: Optional[int] = None
    covariance_matrix: Optional[CovarianceMatrix] = None

    def get_parameter_values(self, get_errors=False, get_both=False):
        """Get parameter values as a numpy array."""
        if get_both:
            return np.array([[v.value, v.error] for v in self.parameters])
        if get_errors:
            return np.array([v.error for v in self.parameters])
        return np.array([v.value for v in self.parameters])

    @property
    def is_best(self):
        """Check if the model is the best fit."""
        return self.status is GoodnessOfFit.BEST

    @property
    def is_good(self):
        """Check if the model is a good fit."""
        return self.status is GoodnessOfFit.GOOD

    @property
    def is_unsafe(self):
        """Check if the model is unsafe."""
        return self.status is GoodnessOfFit.UNSAFE

    @property
    def get_reduced_cstat(self):
        """Get the reduced c-statistic (cstat/dof)."""
        return self.cstat / self.dof

    @property
    def covariance_matrix_value(self):
        """Get the covariance matrix."""
        return self.covariance_matrix.matrix

    @classmethod
    def from_dictionary(cls, name: str, data: Dict, interval: TimeInterval) -> "Model":
        """Create a SingleModel from its dictionary representation."""
        status = GoodnessOfFit(data["_status"])
        cstat = data["c-stat/dof"][0]
        dof = int(data["c-stat/dof"][1])
        cov_matrix = np.array(data["covariance_matrix"])
        aux_keys1 = ["_status", "c-stat/dof", "covariance_matrix"]
        for aux_ in aux_keys1:
            data.pop(aux_)

        return cls(
            name, [Parameter(k, v, e) for k, (v, e) in data.items()], interval, status, cstat, dof, CovarianceMatrix(cov_matrix)
        )

    def __str__(self) -> str:
        safety = GoodnessOfFit.BEST if self.is_best else GoodnessOfFit.SAFE if self.is_good else GoodnessOfFit.UNSAFE
        return (
            f"model: {self.name},\n"
            f"_status: {safety}\n"
            f"n_parameters: {len(self.parameters)},\n"
            f"cstat/dof: {self.cstat:.4f}/{self.dof},\n"
            f"covariance_matrix: {self.covariance_matrix}"
        )

    def __repr__(self) -> str:
        safety = GoodnessOfFit.BEST if self.is_best else GoodnessOfFit.SAFE if self.is_good else GoodnessOfFit.UNSAFE
        params = ",\n        ".join(repr(p) for p in self.parameters)

        return (
            "Model[\n"
            f"    name={self.name!r},\n"
            f"    _status: {safety}\n"
            f"    parameters=(\n"
            f"        {params}\n"
            f"    ),\n"
            f"    cstat={self.cstat},\n"
            f"    dof={self.dof},\n"
            f"    covariance_matrix={self.covariance_matrix}"
            "]"
        )


@dataclass
class ModelSet:
    """A container for GRB spectral models."""

    _models: List[Model]

    def __post_init__(self):
        self._by_name: Dict[str, Model] = {m.name: m for m in self._models}

    def __repr__(self) -> str:
        if not self._models:
            return "ModelSet(empty)"

        lines = ["ModelSet("]
        for m in self._models:
            lines.append(f"\tModel({m.name}, status={m.status.value}, cstat/dof={m.cstat:.3f}/{m.dof}),")
        lines.append(")")
        return "\n".join(lines)

    def __getitem__(self, key: Union[int, str]) -> Model:
        if isinstance(key, int):
            return self._models[key]
        return self._by_name[key]

    def __iter__(self):
        return iter(self._models)

    def __len__(self):
        return len(self._models)

    @property
    def best(self) -> Model:
        """Return the BEST model, if any."""
        return [m for m in self._models if m.status is GoodnessOfFit.BEST][0]

    @property
    def safe(self) -> "ModelSet":
        """Return all SAFE models."""
        safe_models: List[Model] = [m for m in self._models if m.status is GoodnessOfFit.SAFE]
        return ModelSet(safe_models)

    @property
    def good(self) -> "ModelSet":
        """Return all GOOD models."""
        return self.safe

    @property
    def unsafe(self) -> "ModelSet":
        """Return all UNSAFE models."""
        unsafe_models: List[Model] = [m for m in self._models if m.status is GoodnessOfFit.UNSAFE]
        return ModelSet(unsafe_models)

    @property
    def names(self) -> Tuple[str, ...]:
        """Get the names of all models in the set."""
        return tuple(self._by_name.keys())

    def get(self, name: str):
        """Get a model by name, or None if not found."""
        return self._by_name.get(name.upper())
