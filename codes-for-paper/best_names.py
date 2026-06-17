"""Created on Apr 23 11:29:24 2026"""

import json

from src.grb_research import GRBCatalog, find_project_root, ModelSet
from src.grb_research.grb_constants import short_to_long

SOURCE_ROOT = find_project_root()
result_file = SOURCE_ROOT / "results.json"
grb_name = ["080916C", "131014A", "140206B", "231129C"]

with open(result_file, "r") as f:
    data = json.load(f)

grb = GRBCatalog.from_iterable(grb_list=grb_name, data=data, name_mapping=short_to_long)

with open("best_names.txt", "w") as f:
    for idx, _ in enumerate(grb):
        f.write(f" GRB{grb_name[idx]} ".center(51, "=") + "\n")
        p: ModelSet = _.get_all_best_models()
        for model_ in p:
            m_idx = model_.interval.index
            # m_idx = m_idx + 1 if m_idx is not None else None
            if m_idx is not None:
                f.write(f"{model_.interval.kind}{m_idx}: {model_.name}\n")
            else:
                f.write(f"{model_.interval.kind}: {model_.name}\n")
