"""
Script to generate LaTeX tables from GRB spectral analysis log files.

Usage:
    python generate_table_from_log.py <log_file> <output_file> [grb_name]

Examples:
    python generate_table_from_log.py cstat_run_20260204_172752.log table_110721A.tex GRB110721A
    python generate_table_from_log.py my_log.log my_table.tex
"""

import sys

from src.grb_research.log_to_latex_parser import parse_log_and_generate_table


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    log_file = sys.argv[1]
    output_file = sys.argv[2]
    grb_name = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        parse_log_and_generate_table(log_file, output_file, grb_name)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
