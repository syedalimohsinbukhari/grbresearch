"""Created on Dec 26 01:34:58 2025"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, TYPE_CHECKING, Union

import numpy as np

if TYPE_CHECKING:
    from .grb_model import ModelSet


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
    """Class representing a time interval with start and end times."""

    kind: EpisodeTypes
    start: Optional[float] = None
    end: Optional[float] = None
    index: Optional[int] = None
    models: Optional[ModelSet] = None

    # Regex patterns
    _T90 = re.compile(r"T90\s+(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)")
    _EX = re.compile(r"(EX[01])\s+(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)")
    _TR = re.compile(r"TR(\d+)\s+(-?\d+(?:\.\d+)?)_(-?\d+(?:\.\d+)?)")

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

    @classmethod
    def from_string(cls, s: str) -> "TimeInterval":
        """Create a TimeInterval from its string representation."""
        if m := cls._T90.match(s):
            return cls(EpisodeTypes.T90, float(m[1]), float(m[2]))

        if m := cls._EX.match(s):
            return cls(EpisodeTypes(m[1]), float(m[2]), float(m[3]))

        if m := cls._TR.match(s):
            return cls(EpisodeTypes.TR, float(m[2]), float(m[3]), int(m[1]))

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

    @property
    def half_difference(self):
        """Average difference between end and start times for midpoint and error calculations, or None if undefined."""
        if self.start is None or self.end is None:
            return None
        return 0.5 * (self.end - self.start)

    @property
    def midpoint(self) -> Optional[float]:
        """Midpoint of the time interval, or None if undefined."""
        if self.start is None or self.end is None:
            return None
        return 0.5 * (self.start + self.end)

    # ---------- display ----------

    def __str__(self) -> str:
        if self.start is None or self.end is None:
            return self.kind.value

        label = f"TR{self.index}" if self.kind is EpisodeTypes.TR else self.kind.value
        return f"{label} ({self.start:.3f}-{self.end:.3f}s)"

    def __repr__(self) -> str:
        return (
            f"TimeInterval("
            f"kind={self.kind.name}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"index={self.index})"
        )


@dataclass
class TimeIntervalSet:
    """Semantic container for GRB time intervals."""

    time_intervals: List[TimeInterval]

    def __post_init__(self):
        self._by_kind = defaultdict(list)

        for i in self.time_intervals:
            self._by_kind[i.kind].append(i)

        # Enforce invariants
        if len(self._by_kind[EpisodeTypes.T90]) > 1:
            raise ValueError("Multiple T90 intervals found")

        if len(self._by_kind[EpisodeTypes.EX0]) > 1:
            raise ValueError("Multiple EX0 intervals found")

        if len(self._by_kind[EpisodeTypes.EX1]) > 1:
            raise ValueError("Multiple EX1 intervals found")

        self._trs = tuple(sorted(self._by_kind.get(EpisodeTypes.TR, []), key=lambda i: i.index))

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
        return self._trs

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

    def extract_interval_arrays(
        self, *, return_include: tuple[str, ...] = (), exclude_ex: bool = False
    ) -> Tuple[np.ndarray, ...]:
        """
        Extract start and end times as numpy arrays.
        Additional derived arrays can be requested via `return_include`.

        Special key:
        - "all": include all derived quantities
        """
        filtered = [i for i in self.time_intervals if not (exclude_ex and i.is_ex)]

        st = np.array([i.start for i in filtered])
        ed = np.array([i.end for i in filtered])

        # Registry of derived quantities
        _derived = {
            "diff": lambda i: i.half_difference,
            "midpoint": lambda i: i.midpoint,
            "duration": lambda i: i.duration,
        }

        # Expand "all" into concrete keys
        if "all" in return_include:
            keys = tuple(_derived.keys())
        else:
            keys = return_include

        extra_arrays = []
        for key in keys:
            if key not in _derived:
                raise ValueError(f"Unknown derived quantity '{key}'. Allowed: {tuple(_derived)} or 'all'")
            extra_arrays.append(np.array([_derived[key](i) for i in filtered]))

        return st, ed, *extra_arrays

    def __iter__(self):
        return iter(self.time_intervals)

    def __getitem__(self, index: Union[int, slice]):
        return self.time_intervals[index]

    def __len__(self):
        return len(self.time_intervals)

    def __repr__(self) -> str:
        if not self.time_intervals:
            return "TimeIntervalSet()"

        lines = ["TimeIntervalSet("]
        for interval in self.time_intervals:
            lines.append(f"    {interval!r},")
        lines.append(")")

        return "\n".join(lines)
