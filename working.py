"""Created on Sep 20 12:49:29 2025"""

import json
import os
import sys
from datetime import datetime

import src.grb_research.core as grb_core
import src.grb_research.safe_good_best as sgb

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"cstat_run_{timestamp}.log"

orig_stdout, orig_stderr = sys.stdout, sys.stderr
with open(log_filename, "w", buffering=1) as log_file:
    sys.stdout = log_file
    sys.stderr = log_file
    ep_ext = "T90"
    tr_count, tex_count = 0, 0
    try:
        res_safe, res_unsafe, res_total = {}, {}, {}
        cwd_ = os.getcwd()
        outer_dirs = grb_core.get_directories_in_current_folder()
        for out_ in outer_dirs:
            inner_dirs = grb_core.get_directories_in_current_folder(f'{cwd_}/{out_}')
            for in_ in inner_dirs:
                cw_test = in_.split("__")[0].split("/")[-1]
                if '0' in cw_test:
                    ep_ext = "T90"
                elif "A" in cw_test or "B" in cw_test:
                    ep_ext = f"EX{tex_count}"
                else:
                    ep_ext = f"TR{tr_count}"
                print(f"\n[RUN] Started at {timestamp} on directory {cwd_}/{out_}/{in_}\n")
                cwd = f'{cwd_}/{out_}/{in_}'
                candidates = [m + ".fit" for m in sorted(sgb.ALLOWED_MODELS)]
                existing = [f for f in candidates if os.path.exists(os.path.join(cwd, f))]
                mapping = sgb.collect_model_cstat([os.path.join(cwd, f) for f in existing])
                for k, v in mapping.items():
                    print(f"{k}: {v[0]:.4f}/{v[1]}")
                mapping = {k: v[0] for k, v in mapping.items()}
                try:
                    base_filtered = sgb.filter_models_by_error(c_stats=mapping, folder_path=cwd,
                                                               candidates=["PL", "CPL", "BAND", "SBPL"])
                    if base_filtered:
                        best, best_c = sgb.pick_best_single_model(base_filtered)
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
                        best, best_c = sgb.pick_best_model(c_stats=mapping, candidates=group,
                                                           group_name=label, folder_path=cwd)
                        print(f"Best {label} model: {best} (cstat={best_c})")
                    except Exception as e:
                        print(f"Best {label} model unavailable ({e})")
                safe = list(sgb.list_safe_models(cwd))
                good = sgb.compute_good_models(c_stats=mapping, folder_path=cwd)
                unsafe = [m for m in mapping if m not in safe]
                good_names = [i[0] for i in list(good.values())]
                safe.sort()
                # good_names.sort()
                unsafe.sort()
                print(f"SAFE models: {sorted(safe)}")
                sgb.list_par_err(cwd_=cwd, fit_type=safe, string=1, is_good=good, result_dict=res_safe, ep_ext=ep_ext)
                print(f"GOOD models: {good}")
                print(f"UNSAFE models: {sorted(unsafe)}")
                sgb.list_par_err(cwd_=cwd, fit_type=unsafe, string=0, result_dict=res_unsafe, ep_ext=ep_ext)
                print(f"[RUN] Finished at {datetime.now().strftime('%Y%m%d_%H%M%S')}")
                res_total = grb_core.deep_merge(d=res_total, u=res_safe)
                res_total = grb_core.deep_merge(d=res_total, u=res_unsafe)
                pp = grb_core.flatten_results(res_total)
                with open("results.json", "w") as f:
                    json.dump(obj=grb_core.make_json_safe(res_total), fp=f, indent=4)
                if '0' in cw_test:
                    pass
                elif "A" in cw_test or "B" in cw_test:
                    tex_count += 1
                else:
                    tr_count += 1

            tr_count = 0
            tex_count = 0


    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        print(f"Logs written to {log_filename}")
