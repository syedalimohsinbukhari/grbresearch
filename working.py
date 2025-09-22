"""Created on Sep 20 12:49:29 2025"""

import os
import sys
from datetime import datetime

from src.grb_research import get_directories_in_current_folder, safe_good_best

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"cstat_run_{timestamp}.log"

orig_stdout, orig_stderr = sys.stdout, sys.stderr
with open(log_filename, "w", buffering=1) as log_file:
    sys.stdout = log_file
    sys.stderr = log_file
    try:
        cwd_ = os.getcwd()
        outer_dirs = get_directories_in_current_folder()
        for out_ in outer_dirs:
            inner_dirs = get_directories_in_current_folder(f'{cwd_}/{out_}')
            for in_ in inner_dirs:
                print(f"\n[RUN] Started at {timestamp} on directory {cwd_}/{out_}/{in_}\n")
                cwd = f'{cwd_}/{out_}/{in_}'
                candidates = [m + ".fit" for m in sorted(safe_good_best.ALLOWED_MODELS)]
                existing = [f for f in candidates if os.path.exists(os.path.join(cwd, f))]
                mapping = safe_good_best.collect_model_cstat([os.path.join(cwd, f) for f in existing])
                for k, v in mapping.items():
                    print(f"{k}: {v[0]:.4f}/{v[1]}")
                mapping = {k: v[0] for k, v in mapping.items()}
                try:
                    base_filtered = safe_good_best.filter_models_by_error(cstats=mapping, folder_path=cwd,
                                                                          candidates=["PL", "CPL", "BAND", "SBPL"])
                    if base_filtered:
                        best, best_c = safe_good_best.pick_best_single_model(base_filtered)
                        print(f"Best single model: {best} (cstat={best_c})")
                    else:
                        print("Best single model: none")
                except Exception as e:
                    print(f"Best single model unavailable ({e})")
                for label, group in {
                    "+BB": ["PL_BB", "CPL_BB", "BAND_BB", "SBPL_BB"],
                    "+PL": ["CPL_PL", "BAND_PL", "SBPL_PL"],
                    "+PL+BB": ["CPL_PL_BB", "BAND_PL_BB", "SBPL_PL_BB"]
                }.items():
                    try:
                        best, best_c = safe_good_best.pick_best_model(cstats=mapping, candidates=group,
                                                                      group_name=label,
                                                                      folder_path=cwd)
                        print(f"Best {label} model: {best} (cstat={best_c})")
                    except Exception as e:
                        print(f"Best {label} model unavailable ({e})")
                safe = list(safe_good_best.list_safe_models(cwd))
                good = safe_good_best.compute_good_models(cstats=mapping, folder_path=cwd)
                unsafe = [m for m in mapping if m not in safe]
                safe.sort()
                unsafe.sort()
                print(f"SAFE models: {sorted(safe)}")
                safe_good_best.list_par_err(cwd_=cwd, fit_type=safe, string='SAFE')
                print(f"GOOD models: {good}")
                print(f"UNSAFE models: {sorted(unsafe)}")
                safe_good_best.list_par_err(cwd_=cwd, fit_type=unsafe, string='UNSAFE')
                print(f"[RUN] Finished at {datetime.now().strftime('%Y%m%d_%H%M%S')}")
    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        print(f"Logs written to {log_filename}")
