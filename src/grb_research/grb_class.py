"""Created on Dec 20 15:18:22 2025"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
# from pprint import pprint
from typing import Dict, Iterable, Optional, Tuple

import numpy as np

from src.grb_research import short_to_long


# print = pprint


class ModelSet:
    """A container for GRB spectral models."""

    def __init__(self, models: Iterable["GRBModel"]):
        self._models: Tuple[GRBModel, ...] = tuple(models)

        # Index by name (last one wins, which is usually fine)
        self._by_name: Dict[str, GRBModel] = {
            m.name: m for m in self._models
        }

    # ------------------
    # Core access
    # ------------------

    def __iter__(self):
        return iter(self._models)

    def __len__(self):
        return len(self._models)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._models[key]
        return self._by_name[key]

    def get(self, name: str):
        """Get a model by name, or None if not found."""
        return self._by_name.get(name.upper())

    # ------------------
    # Semantic access
    # ------------------

    @property
    def best(self) -> "ModelSet":
        """Return the BEST model, if any."""
        return ModelSet(m for m in self._models if m.status is GoodnessOfFit.BEST)

    @property
    def safe(self) -> "ModelSet":
        """Return all SAFE models."""
        return ModelSet(m for m in self._models if m.status is GoodnessOfFit.SAFE)

    @property
    def good(self) -> "ModelSet":
        """Return all GOOD models."""
        return self.safe

    @property
    def unsafe(self) -> "ModelSet":
        """Return all UNSAFE models."""
        return ModelSet(m for m in self._models if m.status is GoodnessOfFit.UNSAFE)

    @property
    def names(self) -> Tuple[str, ...]:
        """Get the names of all models in the set."""
        return tuple(self._by_name.keys())

    # ------------------
    # Repr
    # ------------------

    def __repr__(self) -> str:
        if not self._models:
            return "ModelSet(empty)"

        lines = ["ModelSet("]
        for m in self._models:
            lines.append(
                f"  {m.name:<8} "
                f"status={m.status.value:<6} "
                f"cstat/dof={m.cstat:.1f}/{m.dof}"
            )
        lines.append(")")
        return "\n".join(lines)


class EpisodeTypes(Enum):
    """Enum class for the different episodes type for GRBs."""
    T90 = "T90"
    EX0 = "EX0"
    EX1 = "EX1"
    TR = "TR"
    UNKNOWN = "UNKNOWN"

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


@dataclass
class TimeInterval:
    """Represents a single GRB time interval."""
    kind: EpisodeTypes
    start: Optional[float] = None
    end: Optional[float] = None
    index: Optional[int] = None  # Only valid for TR
    models: ModelSet = field(default_factory=dict)

    # Regex patterns
    _T90 = re.compile(r'T90\s+(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)')
    _EX = re.compile(r'(EX[01])\s+(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)')
    _TR = re.compile(r'TR(\d+)\s+(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)')

    def __post_init__(self):
        if self.kind is EpisodeTypes.TR:
            if self.index is None:
                raise ValueError("TR interval requires an index")
        else:
            if self.index is not None:
                raise ValueError(f"{self.kind.value} interval cannot have an index")

        if (self.start is None) ^ (self.end is None):
            raise ValueError("start and end must be set together")

        if self.start is not None and self.end is not None:
            if self.start > self.end:
                raise ValueError("start time cannot be greater than end time")

    # ---------- construction ----------

    def get_model_by_string(self, model_string) -> Optional["GRBModel"]:
        """Get the models associated with this time interval."""
        return self.models.get(model_string.upper())

    @property
    def get_safe_models(self) -> "ModelSet":
        """Get the safe models associated with this time interval."""
        return self.models.safe

    @property
    def get_best_model(self) -> "GRBModel":
        """Get the best models associated with this time interval."""
        return self.models.best[self.models.best.names[0]]

    @property
    def get_unsafe_models(self) -> "ModelSet":
        """Get the unsafe models associated with this time interval."""
        return self.models.unsafe

    def get_safe_models_without_best(self) -> "ModelSet":
        """Get the safe models excluding the best model."""
        return ModelSet([m for m in self.models.safe if not m.is_best])

    @classmethod
    def from_string(cls, s: str) -> "TimeInterval":
        """Create a TimeInterval from its string representation."""
        if m := cls._T90.match(s):
            return cls(
                kind=EpisodeTypes.T90,
                start=float(m[1]),
                end=float(m[2]),
            )

        if m := cls._EX.match(s):
            return cls(
                kind=EpisodeTypes(m[1]),
                start=float(m[2]),
                end=float(m[3]),
            )

        if m := cls._TR.match(s):
            return cls(
                kind=EpisodeTypes.TR,
                index=int(m[1]),
                start=float(m[2]),
                end=float(m[3]),
            )

        return cls(kind=EpisodeTypes.UNKNOWN)

    def to_string(self) -> str:
        """Convert TimeInterval to its string representation with 3 decimal places."""
        if self.start is None or self.end is None:
            return self.kind.value

        start_str = f"{self.start:.3f}"
        end_str = f"{self.end:.3f}"

        if self.is_t90:
            return f"T90 {start_str}_{end_str}"
        elif self.is_ex:
            return f"{self.kind.value} {start_str}_{end_str}"
        elif self.is_tr:
            return f"TR{self.index} {start_str}_{end_str}"
        else:
            return "UNKNOWN"

    # ---------- properties ----------

    @property
    def is_ex(self) -> bool:
        """Is an EX episode?"""
        return self.kind in {EpisodeTypes.EX0, EpisodeTypes.EX1}

    @property
    def is_t90(self) -> bool:
        """Is a T90 episode?"""
        return self.kind is EpisodeTypes.T90

    @property
    def is_tr(self) -> bool:
        """Is a TR episode?"""
        return self.kind is EpisodeTypes.TR

    @property
    def duration(self) -> Optional[float]:
        """Duration of the time interval, or None if undefined."""
        if self.start is None or self.end is None:
            return None
        return self.end - self.start

    # ---------- display ----------

    def __str__(self) -> str:
        if self.start is None or self.end is None:
            return self.kind.value

        label = (
            f"TR{self.index}"
            if self.kind is EpisodeTypes.TR
            else self.kind.value
        )
        return f"{label} ({self.start:.3f}-{self.end:.3f}s)"

    def __repr__(self) -> str:
        return (
            f"TimeInterval("
            f"kind={self.kind.name}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"index={self.index})"
        )


class TimeIntervalSet:
    """Semantic container for GRB time intervals."""

    def __init__(self, intervals: Iterable[TimeInterval]):
        self.intervals = tuple(intervals)

        self._by_kind = defaultdict(list)
        for i in self.intervals:
            self._by_kind[i.kind].append(i)

        # Enforce invariants
        if len(self._by_kind[EpisodeTypes.T90]) > 1:
            raise ValueError("Multiple T90 intervals found")

        if len(self._by_kind[EpisodeTypes.EX0]) > 1:
            raise ValueError("Multiple EX0 intervals found")

        if len(self._by_kind[EpisodeTypes.EX1]) > 1:
            raise ValueError("Multiple EX1 intervals found")

    # ---------- canonical access ----------

    @property
    def t90(self) -> Optional[TimeInterval]:
        """Get the T90 interval, if any."""
        return next(iter(self._by_kind[EpisodeTypes.T90]), None)

    @property
    def ex0(self) -> Optional[TimeInterval]:
        """Get the EX0 interval, if any."""
        return next(iter(self._by_kind[EpisodeTypes.EX0]), None)

    @property
    def ex1(self) -> Optional[TimeInterval]:
        """Get the EX1 interval, if any."""
        return next(iter(self._by_kind[EpisodeTypes.EX1]), None)

    @property
    def trs(self) -> tuple[TimeInterval, ...]:
        """Get all TR intervals, sorted by index."""
        return tuple(sorted(
            self._by_kind[EpisodeTypes.TR],
            key=lambda i: i.index
        ))

    @property
    def n_trs(self):
        """Get the number of TR intervals."""
        return len(self._by_kind[EpisodeTypes.TR])

    def tr(self, index: int) -> Optional[TimeInterval]:
        """Get the TR interval with the given index, if any."""
        for i in self._by_kind[EpisodeTypes.TR]:
            if i.index == index:
                return i
        return None

    def get_model(self, model_name):
        """Get all models for this GRB."""
        models = []
        for interval in self.intervals:
            print(interval)
            for model in interval.models:
                if model.name == model_name.upper():
                    models.append(model)
        return models

    # ---------- container behavior ----------

    def __iter__(self):
        return iter(self.intervals)

    def __len__(self):
        return len(self.intervals)

    def __repr__(self) -> str:
        if not self.intervals:
            return "TimeIntervalSet()"

        lines = ["TimeIntervalSet("]
        for interval in self.intervals:
            lines.append(f"    {interval!r},")
        lines.append(")")

        return "\n".join(lines)


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


class CovarianceMatrix:
    """Represents a covariance matrix for model parameters."""

    def __init__(self, matrix: np.ndarray):
        self.matrix = matrix

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self):
        return f"CM({self.matrix.shape[0]}x{self.matrix.shape[1]})"


@dataclass
class GRBModel:
    """Represents a GRB model with its parameters and fit statistics."""
    name: str
    interval: TimeInterval
    parameters: Dict = field(default_factory=dict)

    status: GoodnessOfFit = None
    cstat: float = None
    dof: int = None
    covariance_matrix: CovarianceMatrix = None

    def get_parameter_values(self, get_errors=False, get_both=False):
        """Get parameter values as a numpy array."""
        if get_both:
            return np.array([[v[0], v[1]] for v in self.parameters.values()])
        if get_errors:
            return np.array([v[1] for v in self.parameters.values()])
        return np.array([v[0] for v in self.parameters.values()])

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
    def from_dictionary(cls, name: str, data: Dict, interval: Optional[TimeInterval] = None) -> "GRBModel":
        """Create a SingleModel from its dictionary representation."""
        status = GoodnessOfFit(data['_status'])
        cstat = data['c-stat/dof'][0]
        dof = int(data['c-stat/dof'][1])
        cov_matrix = np.array(data['covariance_matrix'])
        aux_keys1 = ['_status', 'c-stat/dof', 'covariance_matrix']
        for aux_ in aux_keys1:
            data.pop(aux_)

        return cls(name,
                   interval,
                   {k: [v, e] for k, (v, e) in data.items()},
                   status, cstat, dof, CovarianceMatrix(cov_matrix))

    def __str__(self) -> str:
        return (f"model: {self.name},\n"
                f"interval: {self.interval.start} - {self.interval.end},\n"
                f"n_parameters: {len(self.parameters)},\n"
                f"cstat/dof: {self.cstat:.4f}/{self.dof},\n"
                f"covariance_matrix: {self.covariance_matrix}")

    def __repr__(self) -> str:
        params = ",\n        ".join(repr(p) for p in self.parameters)

        return (
            "GRBModel[\n"
            f"    name={self.name!r},\n"
            f"    interval={self.interval!r},\n"
            f"    parameters=(\n"
            f"        {params}\n"
            f"    ),\n"
            f"    cstat={self.cstat},\n"
            f"    dof={self.dof},\n"
            f"    covariance_matrix={self.covariance_matrix}\n"
            "]"
        )


@dataclass
class GRB:
    """Represents a GRB with its name and time intervals."""
    name: str
    intervals: TimeIntervalSet = field(default_factory=dict)

    # time_intervals: List[TimeInterval] = field(default_factory=list)

    @staticmethod
    def __interval_container(episode_level_keys) -> TimeIntervalSet:
        """Get the TimeIntervalSet for this GRB."""
        time_intervals = []
        for interval_str in episode_level_keys:
            interval = TimeInterval.from_string(interval_str)
            time_intervals.append(interval)
        return TimeIntervalSet(time_intervals)

    @classmethod
    def from_dictionary(cls, name: str, data: Dict) -> "GRB":
        """Create a GRB from its dictionary representation."""
        grb = cls(name=name)
        grb.intervals = grb.__interval_container(data.keys())
        for interval_ in grb.intervals:
            gm = []
            temp_data = data[interval_.to_string()]
            for m_name in temp_data.keys():
                temp_model = temp_data[m_name]
                gm.append(GRBModel.from_dictionary(m_name, temp_model, interval_))
            interval_.models = ModelSet(gm)

        return grb

    def __repr__(self):
        return f"GRB(name={self.name}, intervals={self.intervals})"

    def __str__(self):
        tr_eps = f'TR({self.intervals.n_trs})'
        ex1 = self.intervals.__getattribute__('ex0')
        try:
            ex2 = self.intervals.__getattribute__('ex1')
        except AttributeError:
            ex2 = None
        if ex2 is not None:
            ex_eps = f'{ex1.kind}/{tr_eps}/{ex2.kind}'
        else:
            ex_eps = f'{ex1.kind}/{tr_eps}'
        return (f"  GRBName: {self.name},\n"
                f"Intervals: {self.intervals.t90.kind}/{ex_eps}")


class GRBCatalog:
    """A catalog of GRBs."""

    def __init__(self, grb_list: Iterable[GRB]):
        self._grb_list: Dict[str, GRB] = {grb.name: grb for grb in grb_list}

    @classmethod
    def from_iterable(cls, grb_list: Iterable[str], data) -> "GRBCatalog":
        """Create a GRBCatalog from an iterable of GRBs."""
        grb_ = [short_to_long[i] for i in grb_list]
        eps_ = [data[i] for i in grb_]
        grb_data_ = [GRB.from_dictionary(i, j) for i, j in zip(grb_, eps_)]
        return GRBCatalog(grb_data_)

    def __getitem__(self, key: str) -> GRB:
        return self._grb_list[key]

    def get(self, name: str) -> Optional[GRB]:
        """Get a GRB by name, or None if not found."""
        return self._grb_list.get(name)

    def __iter__(self):
        return iter(self._grb_list.values())

    def __len__(self):
        return len(self._grb_list)

    def __repr__(self) -> str:
        if not self._grb_list:
            return "GRBCatalog(empty)"

        lines = ["GRBCatalog("]
        for grb in self._grb_list.values():
            lines.append(f"  {grb.name}")
        lines.append(")")
        return "\n".join(lines)

    def __str__(self):
        return self.__repr__()
