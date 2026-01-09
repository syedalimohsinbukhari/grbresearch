"""Created on Dec 26 14:40:22 2025"""

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from .grb_model import GoodnessOfFit, Model, ModelSet
from .grb_time import EpisodeTypes, TimeInterval, TimeIntervalSet


@dataclass
class GRB:
    name: str
    intervals: Optional[TimeIntervalSet] = None

    @classmethod
    def from_dictionary(cls, name: str, data: Dict) -> "GRB":
        """
        Create a GRB instance from a nested dictionary representation.

        Parameters
        ----------
        cls : type
            The GRB class.
        name : str
            The name for the created GRB.
        data : Dict
            Mapping where keys are time-interval strings and values are dictionaries mapping model names to model dictionaries.

        Returns
        -------
        GRB
            A `GRB` instance whose `intervals` attribute is a `TimeIntervalSet` populated from the provided keys and whose `models` attribute on
            each `TimeInterval` is set to a `ModelSet` constructed from the nested model dictionaries.

        Raises
        ------
        KeyError
            If an expected interval key referenced during model construction is missing in `data`.
        """
        grb = cls(name=name)
        grb.intervals = grb.__interval_container(data.keys())
        for interval_ in grb.intervals:
            gm = []
            temp_data = data[interval_.to_string()]
            for m_name in temp_data.keys():
                gm.append(Model.from_dictionary(m_name, temp_data[m_name], interval_))
            interval_.models = ModelSet(gm)

        return grb

    def __repr__(self):
        return f"GRB(name={self.name}, intervals={self.intervals})"

    def __str__(self):
        tr_eps = f"TR({self.intervals.n_trs})"
        ex1 = self.intervals.ex0
        ex2 = self.intervals.ex1
        if ex2 is not None:
            ex_eps = f"{ex1.kind}/{tr_eps}/{ex2.kind}"
        else:
            ex_eps = f"{ex1.kind}/{tr_eps}"
        return f"  GRBName: {self.name},\n" f"Intervals: {self.intervals.t90.kind}/{ex_eps}"

    @staticmethod
    def __interval_container(episode_keys):
        time_intervals = []
        for interval_str in episode_keys:
            interval = TimeInterval.from_string(interval_str)
            time_intervals.append(interval)
        return TimeIntervalSet(time_intervals)

    def get_all_best_models(self):
        """Get the best model for each interval."""
        m_total = []
        for i in self.intervals:
            for m in i.models:
                if m.status is GoodnessOfFit.BEST:
                    m_total.append(m)
        return ModelSet(m_total)

    def get_model(self, model_name, interval=None, tr_index=None):
        all_models = []
        for interval_ in self.intervals:
            if interval and interval_.kind != interval:
                continue

            if tr_index is not None and interval_.kind is EpisodeTypes.TR:
                if interval_.index != tr_index:
                    continue

            model = interval_.models.get(model_name)
            if model:
                all_models.append(model)

        return ModelSet(all_models)


@dataclass
class GRBCatalog:
    grb_list: Iterable[GRB]

    def __post_init__(self):
        self._grb_list: Dict[str, GRB] = {grb.name: grb for grb in self.grb_list}

    def __getitem__(self, key: str) -> GRB:
        return self._grb_list[key]

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

    @classmethod
    def from_iterable(cls, grb_list: Iterable[str], data: dict, name_mapping: dict) -> "GRBCatalog":
        """Construct a GRBCatalog object from iterable"""
        grb_ = [name_mapping[i] for i in grb_list]
        eps_ = [data[i] for i in grb_]
        grb_data_ = [GRB.from_dictionary(name=i, data=j) for i, j in zip(grb_, eps_)]
        return GRBCatalog(grb_data_)

    def get_grb(self, name: str) -> Optional[GRB]:
        """Get the GRB from catalog by name."""
        return self._grb_list.get(name)
