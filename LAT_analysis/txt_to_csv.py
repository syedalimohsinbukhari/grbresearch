"""Created on Jun 13 19:21:38 2026"""

import re
from pathlib import Path
from typing import Any


def parse_key_value_file(file_path: Path) -> dict[str, str]:
    """Parse comma-separated key/value records from a file."""
    data = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ', ' in line:
                key, value = line.split(', ', 1)
                data[key.strip()] = value.strip()
    return data


def parse_interval_from_directory_name(dir_name: str) -> tuple[str, str]:
    """
    Parse interval bounds from directory name like Ep*__{start}_{end}.
    Convert leading 'm' to '-'.
    Returns (start, end) as strings preserving original precision.
    """
    match = re.match(r'^Ep\w*__([m\-]?[\d.]+)_([\d.]+)$', dir_name)
    if not match:
        raise ValueError(f"Malformed directory name: {dir_name}")

    start_str = match.group(1)
    end_str = match.group(2)

    # Convert m prefix to minus sign
    if start_str.startswith('m'):
        start_str = '-' + start_str[1:]

    return start_str, end_str


def find_companion_files(epoch_dir: Path) -> tuple[Path, Path]:
    """
    Find the analysis and fit result files in the epoch directory.
    Raises error if missing or duplicate files are found.
    """
    analysis_files = list(epoch_dir.glob('*_analysis_result_*.txt'))
    fit_files = list(epoch_dir.glob('*_fit_results_*.txt'))

    if len(analysis_files) == 0:
        raise FileNotFoundError(f"Missing analysis file in {epoch_dir}")
    if len(analysis_files) > 1:
        raise ValueError(f"Duplicate analysis files in {epoch_dir}: {analysis_files}")

    if len(fit_files) == 0:
        raise FileNotFoundError(f"Missing fit file in {epoch_dir}")
    if len(fit_files) > 1:
        raise ValueError(f"Duplicate fit files in {epoch_dir}: {fit_files}")

    return analysis_files[0], fit_files[0]


def process_epoch(epoch_dir: Path) -> dict[str, Any]:
    """Process a single epoch directory and extract required data."""
    start_str, end_str = parse_interval_from_directory_name(epoch_dir.name)

    analysis_file, fit_file = find_companion_files(epoch_dir)

    analysis_data = parse_key_value_file(analysis_file)
    fit_data = parse_key_value_file(fit_file)

    # Required fields from analysis file
    required_analysis = ['# of Events', '# of P > 0.9', 'P > 0.9 Max (E) MeV', 'Arrival Time (s)', 'TS']
    for field in required_analysis:
        if field not in analysis_data:
            raise ValueError(f"Missing required field '{field}' in {analysis_file}")

    # Required fields from fit file
    required_fit = ['Index', 'Index Error']
    for field in required_fit:
        if field not in fit_data:
            raise ValueError(f"Missing required field '{field}' in {fit_file}")

    return {
        'start': start_str,
        'end': end_str,
        'start_num': float(start_str),
        'end_num': float(end_str),
        'events': analysis_data['# of Events'],
        'high_probability_events': analysis_data['# of P > 0.9'],
        'max_energy': float(analysis_data['P > 0.9 Max (E) MeV']),
        'arrival_time': float(analysis_data['Arrival Time (s)']),
        'ts': float(analysis_data['TS']),
        'index': float(fit_data['Index']),
        'index_error': float(fit_data['Index Error'])
    }


def format_latex_row(epoch_data: dict[str, Any]) -> str:
    """Format a single epoch's data as a LaTeX table row."""
    return (
        f"\\sirangeDuration{{{epoch_data['start']}}}{{{epoch_data['end']}}} & "
        f"{epoch_data['events']} & "
        f"{epoch_data['high_probability_events']} & "
        f"{epoch_data['max_energy']:.2f} & "
        f"{epoch_data['arrival_time']:.3f} & "
        f"{epoch_data['ts']:.3f} & "
        f"{epoch_data['index']:.2f}({epoch_data['index_error']:.2f}) \\\\"
    )


def process_grb_directory(grb_dir: Path) -> None:
    """Process all epoch directories in a GRB directory and generate LaTeX output."""
    # Find all epoch directories
    epoch_dirs = [d for d in grb_dir.iterdir() if d.is_dir() and d.name.startswith('Ep')]

    if not epoch_dirs:
        print(f"No epoch directories found in {grb_dir}")
        return

    # Find Ep0 directory for output naming
    ep0_dirs = [d for d in epoch_dirs if d.name.startswith('Ep0__')]
    if len(ep0_dirs) != 1:
        raise ValueError(f"Expected exactly one Ep0 directory in {grb_dir}, found {len(ep0_dirs)}")

    ep0_start, ep0_end = parse_interval_from_directory_name(ep0_dirs[0].name)

    # Process all epochs
    epochs_data = []
    for epoch_dir in epoch_dirs:
        try:
            epoch_data = process_epoch(epoch_dir)
            epochs_data.append(epoch_data)
        except Exception as e:
            raise RuntimeError(f"Error processing {epoch_dir}: {e}") from e

    # Sort by start time, then end time
    epochs_data.sort(key=lambda x: (x['start_num'], x['end_num']))

    # Generate LaTeX rows
    latex_rows = [format_latex_row(epoch_data) for epoch_data in epochs_data]

    # Write output file
    output_filename = f"lat_analysis_{ep0_start}_{ep0_end}.tex"
    output_path = grb_dir / output_filename

    with open(output_path, 'w') as f:
        f.write('\n'.join(latex_rows) + '\n')

    print(f"Generated {output_path} with {len(latex_rows)} rows")


def main():
    """Process all GRB directories under LAT_analysis."""
    script_dir = Path(__file__).parent

    # Find all GRB directories (immediate subdirectories)
    grb_dirs = [d for d in script_dir.iterdir() if d.is_dir()]

    if not grb_dirs:
        print("No GRB directories found")
        return

    for grb_dir in sorted(grb_dirs):
        print(f"\nProcessing {grb_dir.name}...")
        try:
            process_grb_directory(grb_dir)
        except Exception as e:
            print(f"ERROR processing {grb_dir.name}: {e}")
            raise


if __name__ == '__main__':
    main()
