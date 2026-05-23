"""Created on Feb 08 2026

Log file parser to generate LaTeX tables from GRB spectral analysis log files.
"""

import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .grb_constants import LATEX_MODEL_NAMES, MODEL_ORDER, short_to_long


# LaTeX model name mapping


class LogParser:
    """Parser for GRB spectral analysis log files."""

    # Model order for LaTeX table rows

    def __init__(self, log_file_path: str):
        """Initialize parser with log file path.

        Parameters
        ----------
        log_file_path : str
            Path to the log file to parse.
        """
        self.log_file_path = Path(log_file_path)
        self.log_content = self._read_log_file()
        self.episodes = []

        # Multi-GRB tracking
        self.current_grb: Optional[str] = None
        self.grb_data: Dict[str, List[Dict]] = {}
        self.grb_pattern = re.compile(r'/GRB(\d+)/Ep\d+__')

    def _read_log_file(self) -> str:
        """Read the entire log file content."""
        with open(self.log_file_path, "r") as f:
            return f.read()

    def parse(self) -> List[Dict]:
        """Parse the log file and extract all episode data.

        Returns
        -------
        List[Dict]
            List of episode dictionaries containing parsed data.
        """
        # Split by RUN blocks
        run_blocks = re.split(r"\[RUN\] Started at \d+_\d+ on directory (.+?)\n", self.log_content)

        # Process blocks (skip the first empty element)
        for i in range(1, len(run_blocks), 2):
            if i + 1 < len(run_blocks):
                directory_path = run_blocks[i].strip()
                block_content = run_blocks[i + 1]

                # Extract GRB identifier and episode name from path
                grb_match = self.grb_pattern.search(directory_path)
                if grb_match:
                    grb_id = grb_match.group(1)

                    # Check if this is an Ep0 episode (new GRB boundary)
                    if 'Ep0__' in directory_path:
                        self.current_grb = grb_id
                        if grb_id not in self.grb_data:
                            self.grb_data[grb_id] = []

                episode_data = self._parse_episode_block(directory_path, block_content)
                if episode_data:
                    self.episodes.append(episode_data)

                    # Also add to GRB-specific collection if we have a current GRB
                    if self.current_grb is not None:
                        self.grb_data[self.current_grb].append(episode_data)

        return self.episodes

    def _parse_episode_block(self, directory_path: str, block_content: str) -> Optional[Dict]:
        """Parse a single RUN block to extract episode information.

        Parameters
        ----------
        directory_path : str
            The directory path from the RUN header.
        block_content : str
            The content of this RUN block.

        Returns
        -------
        Optional[Dict]
            Episode data dictionary or None if parsing fails.
        """
        # Extract GRB name and episode info from directory path
        # Example: /path/to/GRB110721200/Ep0__0.000_21.824
        path_parts = directory_path.split("/")
        grb_name = None
        episode_dir = None

        for part in path_parts:
            if part.startswith("GRB"):
                grb_name = part
            elif part.startswith("Ep"):
                episode_dir = part

        if not grb_name or not episode_dir:
            return None

        # Parse episode name and time range
        episode_name, time_range = self._parse_episode_info(episode_dir)

        # Extract SAFE models list
        safe_models = self._extract_safe_models(block_content, "SAFE")
        if not safe_models:
            return None

        best_models = self._extract_safe_models(block_content, "BEST")
        if not best_models:
            return None

        # Extract parameters for each SAFE model
        model_parameters = {}
        for model in safe_models:
            params = self._extract_model_parameters(block_content, model, is_safe=True)
            if params:  # Only include models with actual parameter data
                model_parameters[model] = params

        for model in best_models:
            params = self._extract_model_parameters(block_content, model, is_safe=True)
            if params:
                model_parameters[model] = params

        # Extract UNSAFE models and filter those with all errors <= 50%
        unsafe_models = self._extract_unsafe_models(block_content)
        for model in unsafe_models:
            params = self._extract_model_parameters(block_content, model, is_safe=False)
            if params and self._check_all_errors_below_threshold(params, 50.0):
                model_parameters[model] = params

        return {
            "grb_name": grb_name,
            "episode_name": episode_name,
            "time_range": time_range,
            "safe_models": safe_models,
            "model_parameters": model_parameters,
        }

    def _parse_episode_info(self, episode_dir: str) -> Tuple[str, Tuple[float, float]]:
        """Parse episode directory name to extract episode name and time range.

        Parameters
        ----------
        episode_dir : str
            Episode directory name (e.g., 'Ep0__0.000_21.824').

        Returns
        -------
        Tuple[str, Tuple[float, float]]
            Episode name and (start_time, end_time) tuple.
        """
        # Extract episode identifier and time range
        # Format: EpX__start_end, EpXA__start_end, or EpXA__m0.384_1.344 (m prefix for negative)
        match = re.match(r"Ep(\d+)([A-Z]?)__m?([\d.]+)_([\d.]+)", episode_dir)
        if not match:
            return "Unknown", (0.0, 0.0)

        ep_num = match.group(1)
        ep_suffix = match.group(2)
        start_time_str = match.group(3)
        end_time = float(match.group(4))

        # Handle negative start time (prefixed with 'm' instead of '-')
        if "__m" in episode_dir:
            start_time = -float(start_time_str)
        else:
            start_time = float(start_time_str)

        # Determine an episode name based on rules
        if ep_num == "0":
            episode_name = "Time integrated"
        elif ep_suffix in ["A", "B"]:
            episode_name = f"Episode EX--{ep_suffix}"
        elif ep_suffix in ["X", "Y", "Z"]:
            # X, Y, Z are sub-episodes, treat as regular episodes
            roman = self._to_roman(int(ep_num))
            episode_name = f"Episode {roman}-{ep_suffix}"
        else:
            # Convert to Roman numerals for regular episodes
            roman = self._to_roman(int(ep_num))
            episode_name = f"Episode {roman}"

        return episode_name, (start_time, end_time)

    def _to_roman(self, num: int) -> str:
        """Convert integer to a Roman numeral."""
        val_to_roman = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
        result = []
        for value, numeral in val_to_roman:
            count = num // value
            if count:
                result.append(numeral * count)
                num -= value * count
        return "".join(result)

    def _extract_safe_models(self, block_content: str, type_: str) -> List[str]:
        """Extract the list of SAFE models from the block content.

        Parameters
        ----------
        block_content : str
            The content of a RUN block.

        Returns
        -------
        List[str]
            List of SAFE model names.
        """
        match = re.search(fr"{type_} models: \[(.+?)\]", block_content)
        if not match:
            return []

        # Extract model names and clean them
        models_str = match.group(1)
        models = [m.strip().strip("'\"") for m in models_str.split(",")]
        return models

    def _extract_unsafe_models(self, block_content: str) -> List[str]:
        """Extract the list of UNSAFE models from the block content.

        Parameters
        ----------
        block_content : str
            The content of a RUN block.

        Returns
        -------
        List[str]
            List of UNSAFE model names.
        """
        match = re.search(r"(?:UNSAFE|MARGINAL) models: \[(.+?)\]", block_content)
        if not match:
            return []

        # Extract model names and clean them
        models_str = match.group(1)
        models = [m.strip().strip("'\"") for m in models_str.split(",")]
        return models

    def _extract_model_parameters(self, block_content: str, model: str, is_safe: bool = True) -> Optional[Dict]:
        """Extract parameters for a specific model.

        Parameters
        ----------
        block_content : str
            The content of a RUN block.
        model : str
            Model name (e.g., 'BAND', 'PL_BB').
        is_safe : bool, optional
            Whether this is a SAFE model (True) or UNSAFE model (False).

        Returns
        -------
        Optional[Dict]
            Dictionary of parameter names to (value, error, error_percentage) tuples, or None.
        """
        # Find the parameter details section for this model
        model_type = r"(?:SAFE|BEST)" if is_safe else r"(?:UNSAFE|MARGINAL)"
        pattern = rf"\[{model_type}\] {model} parameter details:\n(.*?)(?=\[SAFE\]|\[BEST\]|\[UNSAFE\]|\[MARGINAL\]|SAFE models:$)"
        match = re.search(pattern, block_content, re.DOTALL)

        if not match:
            return None

        param_section = match.group(1)

        # Check if the section is empty (no actual parameters)
        if not param_section.strip() or param_section.strip() == "":
            return None

        parameters = {}
        elevated_constrains = 0

        # Extract each parameter line
        # Format: "   parameter_name = value(error) , percentage %"
        if is_safe:
            param_lines = re.findall(r"\s+(\w+)\s+=\s+([\d.e+-]+)\(([\d.e+-]+)\)", param_section)
            for param_name, value, error in param_lines:
                parameters[param_name] = (float(value), float(error), None)
        else:
            # For UNSAFE models, also capture error percentage (including scientific notation like "1.79e+04 %")
            param_lines = re.findall(r"\s+(\w+)\s+=\s+([\d.e+-]+)\(([\d.e+-]+)\)\s*,\s*([\d.e+-]+)\s*%", param_section)
            elevated_constrains = 0
            for param_name, value, error, error_pct in param_lines:
                if np.logical_and(40 < float(error_pct), float(error_pct) < 50):
                    elevated_constrains += 1
                parameters[param_name] = (float(value), float(error), float(error_pct))

        # Special handling for c-stat/dof (format: cstat/dof)
        cstat_match = re.search(r"c-stat/dof\s+=\s+([\d.]+)/([\d.]+)", param_section)
        if cstat_match:
            parameters["cstat"] = float(cstat_match.group(1))
            parameters["dof"] = float(cstat_match.group(2))

        return parameters if (parameters and elevated_constrains <= 1) else None

    def _check_all_errors_below_threshold(self, parameters: Dict, threshold: float) -> bool:
        """Check if all parameter error percentages are below the threshold.

        Parameters
        ----------
        parameters : Dict
            Parameter dictionary with (value, error, error_percentage) tuples.
        threshold : float
            Error percentage threshold (e.g., 50.0 for 50%).

        Returns
        -------
        bool
            True if all errors are below threshold, False otherwise.
        """
        for param_name, param_data in parameters.items():
            # Skip non-parameter entries (cstat, dof)
            if param_name in ["cstat", "dof"]:
                continue

            # Check if the error percentage exists and is within the threshold
            if len(param_data) >= 3 and param_data[2] is not None:
                if param_data[2] > threshold:
                    return False

        return True

    def generate_multiple_latex_tables(self, output_dir: str = None) -> List[str]:
        """Generate separate LaTeX table files for each GRB found in the log.

        Parameters
        ----------
        output_dir : str, optional
            Directory to write output files. If None, uses the log file's directory.

        Returns
        -------
        List[str]
            List of generated output file paths.
        """
        if not self.grb_data:
            print("No GRB data found. Make sure to call parse() first.")
            return []

        if output_dir is None:
            output_dir = self.log_file_path.parent
        else:
            output_dir = Path(output_dir)

        output_files = []

        for grb_id, episodes in self.grb_data.items():
            short_name = [k for k, v in short_to_long.items() if f'GRB{grb_id}' == v][0]
            if not episodes:
                continue

            # Convert GRB ID to standard format (e.g., 110721200 -> GRB110721A)
            # grb_name = self._format_grb_name(grb_id)
            grb_name = f'GRB{short_name}'
            # Generate table for this GRB
            generator = LaTeXTableGenerator(episodes, grb_name)
            table_content = generator.generate_table()

            # Write to file
            output_file = output_dir / f"{short_name}.tex"
            with open(output_file, "w") as f:
                f.write(table_content)

            output_files.append(str(output_file))
            print(f"Generated {output_file} with {len(episodes)} episodes")

        print(f"\nTotal: Generated {len(output_files)} LaTeX table(s)")
        return output_files

    def _format_grb_name(self, grb_id: str) -> str:
        """Format GRB identifier to standard name.

        Parameters
        ----------
        grb_id : str
            Raw GRB identifier (e.g., '110721200').

        Returns
        -------
        str
            Formatted GRB name (e.g., 'GRB110721A').
        """
        # Extract the first 6 digits (date)
        if len(grb_id) >= 6:
            date_part = grb_id[:6]
            # For standard format, just add 'A' suffix
            return f"GRB{date_part}A"
        return f"GRB{grb_id}"


class LaTeXTableGenerator:
    """Generate LaTeX tables from parsed episode data."""

    def __init__(self, episodes: List[Dict], grb_name: str):
        """Initialize generator with episode data.

        Parameters
        ----------
        episodes : List[Dict]
            List of parsed episode dictionaries.
        grb_name : str
            GRB identifier (e.g., 'GRB110721A').
        """
        self.episodes = episodes
        self.grb_name = grb_name

    def generate_table(self) -> str:
        """Generate complete LaTeX table.

        Returns
        -------
        str
            Complete LaTeX table as a string.
        """
        lines = []

        # Table header
        lines.append(f"\\subsection{{{self.grb_name}}}")
        lines.append("\\begin{table*}[!htpb]")
        lines.append(" \\centering")
        # lines.append(" \\renewcommand{\\arraystretch}{1.175}")
        lines.append(" \\caption{")
        lines.append(
            f"         Fitted parameters for time-integrated and time-resolved spectral analysis of {self.grb_name}."
        )
        lines.append("         The values in parenthesis are the uncertainty in the measured parameter.")
        lines.append("         The BEST models are highlighted with a light gray strip.")
        lines.append(
            "         The marked parameters in red indicate the values that are just beyond the error "
            + "criteria limit."
        )
        lines.append("         The percentage above threshold is indicated in superscript for reference.")
        lines.append(
            "         The models not included here either did not converge, or produced errors much higher"
            + " than the threshold criteria."
        )
        lines.append("     }")
        lines.append(f" \\label{{tab:{self.grb_name}-large}}")
        lines.append(" \\resizebox{\\textwidth}{!}{")
        lines.append("\\begin{tabular}{lcccccccccccc}")
        lines.append("    \\toprule")
        lines.append(f"     \\multicolumn{{13}}{{c}}{{\\textbf{{{self.grb_name}}}}} \\\\")
        lines.append("\\midrule")

        # Column headers
        lines.append("     \\multicolumn{1}{c}{\\multirow{2}{*}{}} &")
        lines.append("     \\multicolumn{4}{c}{\\sbpl/\\band/\\cpl} &")
        lines.append("     &")
        lines.append("     \\multicolumn{2}{c}{\\pl} &")
        lines.append("     &")
        lines.append("     \\multicolumn{2}{c}{\\bb} &")
        lines.append("     &")
        lines.append("     \\multirow{4}{*}{C-Stat/DOF} \\\\ \\cline{2-5} \\cline{7-8} \\cline{10-11}")
        lines.append("     \\multicolumn{1}{c}{} & \\twoRs{Amplitude [$\\times10^{-3}$]}{\\,[\\si{\\phcmskev}]} &")
        lines.append("     $\\alpha$ &")
        lines.append("     $\\beta$ &")
        lines.append("     \\twoRs{Break/Peak Energy}{\\,[keV]} &")
        lines.append("     &")
        lines.append("     \\twoRs{Amplitude [$\\times10^{-3}$]}{\\,[\\si{\\phcmskev}]} &")
        lines.append("     $\\alpha$ &")
        lines.append("     &")
        lines.append("     \\twoRs{Amplitude [$\\times10^{-6}$]}{\\,[\\si{\\phcmskev}]} &")
        lines.append("     \\twoRs{kT}{\\,[keV]} &")
        lines.append("     & \\\\")
        lines.append("    \\midrule")

        # Episode sections
        for episode in self.episodes:
            lines.extend(self._generate_episode_section(episode))

        # Table footer
        lines[-1] = "     \\bottomrule"
        lines.append(" \\end{tabular}%")
        lines.append("}")
        lines.append("\\end{table*}")

        return "\n".join(lines)

    def _generate_episode_section(self, episode: Dict) -> List[str]:
        """Generate LaTeX lines for a single episode section.

        Parameters
        ----------
        episode : Dict
            Episode data dictionary.

        Returns
        -------
        List[str]
            List of LaTeX lines for this episode.
        """
        lines = []

        # Episode header
        start, end = episode["time_range"]
        lines.append(
            f"     \\multicolumn{{13}}{{l}}{{\\textbf{{{episode['episode_name']}: \\sirangeDuration{{{start:.3f}}}{{{end:.3f}}}}}}}\\\\"
        )

        # Model rows in the specified order
        for model in MODEL_ORDER:
            if model in episode["model_parameters"]:
                params = episode["model_parameters"][model]
                row = self._generate_model_row(model, params)
                lines.append(row)

        lines.append("    \\midrule")

        return lines

    def _generate_model_row(self, model: str, params: Dict) -> str:
        """Generate a single model row for the table.

        Parameters
        ----------
        model : str
            Model name.
        params : Dict
            Parameter dictionary with (value, error) tuples.

        Returns
        -------
        str
            LaTeX table row string.
        """
        # Initialize all columns with tabledash
        cols = ["\\tabledash"] * 13

        # Column 0: Model name
        cols[0] = f"     {LATEX_MODEL_NAMES[model]}"

        # Determine which columns to fill based on the model type
        if model in ["PL", "PL_BB"]:
            # PL models use columns 7-8 (PL section)
            if "amplitude" in params:
                cols[6] = self._format_amplitude(params["amplitude"])
            if "index1" in params:
                cols[7] = self._format_value(params["index1"])
        else:
            # SBPL/BAND/CPL models use columns 2-5 (main section)
            if "amplitude" in params:
                cols[1] = self._format_amplitude(params["amplitude"])
            if "index1" in params:
                cols[2] = self._format_value(params["index1"])
            if "index2" in params:
                cols[3] = self._format_value(params["index2"])
            if "peak_energy" in params:
                cols[4] = self._format_value(params["peak_energy"])
            elif "break_energy" in params:
                cols[4] = self._format_value(params["break_energy"])

        if model.endswith("_PL_BB"):
            cols[6] = self._format_amplitude(params["amplitude_pl"])
            cols[7] = self._format_value(params["index2_pl"])

        # BB models (any model ending with _BB) use columns 10-11
        if model.endswith("_BB"):
            cols[9] = self._format_bb_amplitude(params["amplitude_bb"])
            cols[10] = self._format_value(params["kt_temperature"])

        # Column 13: C-Stat/DOF
        if "cstat" in params and "dof" in params:
            cols[12] = f"{params['cstat']:.4f}/{params['dof']:.0f}"

        # Columns 5, 8, 11 are always empty separators
        cols[5] = ""
        cols[8] = ""
        cols[11] = ""

        # Join with '&' and add a line ending
        return " & ".join(cols) + " \\\\"

    def _format_amplitude(self, value_error: Tuple[float, ...]) -> str:
        """Format amplitude value for main components (6 decimal places).

        Parameters
        ----------
        value_error : Tuple[float, ...]
            (value, error) or (value, error, error_percentage) tuple.

        Returns
        -------
        str
            Formatted LaTeX string.
        """
        value = value_error[0]
        error = value_error[1]
        error_pct = value_error[2] if len(value_error) >= 3 else None

        # Values are already in correct units from log file
        base_str = f"\\ampCOMP{{{value:.6f}({error:.6f})}}"

        # Add red color if error percentage > 40%
        if error_pct is not None and error_pct > 40.0:
            excess = error_pct - 40.0
            superscript = self._format_error_superscript(excess)
            return f"\\textcolor{{red}}{{{base_str}$^{{{superscript}}}$}}"

        return base_str

    def _format_bb_amplitude(self, value_error: Tuple[float, ...]) -> str:
        """Format BB amplitude value with adaptive precision.

        Parameters
        ----------
        value_error : Tuple[float, ...]
            (value, error) or (value, error, error_percentage) tuple.

        Returns
        -------
        str
            Formatted LaTeX string.
        """
        value = value_error[0]
        error = value_error[1]
        error_pct = value_error[2] if len(value_error) >= 3 else None

        # Values are already in correct units from the log file
        # Use adaptive precision: at least 9 decimals, but more if needed for significant figures
        # Find first significant digit position
        if value != 0:
            first_sig_pos = -int(math.floor(math.log10(abs(value))))
            # Use at least 9 decimals and round up to the nearest multiple of 3
            decimals = max(9, ((first_sig_pos + 3) // 3) * 3)
        else:
            decimals = 9

        base_str = f"\\ampBB[e6]{{{value:.{decimals}f}({error:.{decimals}f})}}"

        # Add red color if error percentage > 40%
        if error_pct is not None and error_pct > 40.0:
            excess = error_pct - 40.0
            superscript = self._format_error_superscript(excess)
            return f"\\textcolor{{red}}{{{base_str}$^{{{superscript}}}$}}"

        return base_str

    def _format_value(self, value_error: Tuple[float, ...]) -> str:
        """Format regular parameter value (3 decimal places).

        Parameters
        ----------
        value_error : Tuple[float, ...]
            (value, error) or (value, error, error_percentage) tuple.

        Returns
        -------
        str
            Formatted LaTeX string.
        """
        value = value_error[0]
        error = value_error[1]
        error_pct = value_error[2] if len(value_error) >= 3 else None

        base_str = f"\\valPars{{{value:.3f}({error:.3f})}}"

        # Add red color if error percentage > 40%
        if error_pct is not None and error_pct > 40.0:
            excess = error_pct - 40.0
            superscript = self._format_error_superscript(excess)
            return f"\\textcolor{{red}}{{{base_str}$^{{{superscript}}}$}}"

        return base_str

    def _format_error_superscript(self, excess_pct: float) -> str:
        """Format the error percentage superscript.

        Parameters
        ----------
        excess_pct : float
            Error percentage above 40% threshold.

        Returns
        -------
        str
            Formatted percentage string for superscript.
        """
        # Use 1 decimal place if < 10%, no decimal if >= 10%
        if excess_pct < 10.0:
            return f"{excess_pct:.1f}\\%"
        else:
            return f"{excess_pct:.0f}\\%"


def parse_log_and_generate_table(log_file_path: str, output_file_path: str = None, grb_name: str = None,
                                 multi_grb: bool = True) -> None:
    """Main function to parse log file and generate LaTeX table(s).

    Parameters
    ----------
    log_file_path : str
        Path to the input log file.
    output_file_path : str, optional
        Path to the output LaTeX file (only used if multi_grb=False).
    grb_name : str, optional
        GRB name for the table (only used if multi_grb=False). If None, will extract from first episode.
    multi_grb : bool, optional
        If True, generate separate tables for each GRB found (default: True).
        If False, generate a single table combining all episodes.
    """
    # Parse the log file
    parser = LogParser(log_file_path)
    episodes = parser.parse()

    if not episodes:
        print("No episodes found in log file.")
        return

    if multi_grb:
        # Generate separate tables for each GRB
        parser.generate_multiple_latex_tables()
    else:
        # Legacy mode: Generate a single table
        if output_file_path is None:
            print("Error: output_file_path required when multi_grb=False")
            return

        # Extract GRB name if not provided
        if grb_name is None:
            # Convert GRB110721200 to GRB110721A format
            raw_name = episodes[0]["grb_name"]
            # Extract just the date part and add 'A' suffix
            match = re.match(r"GRB(\d{6})", raw_name)
            if match:
                grb_name = f"GRB{match.group(1)}A"
            else:
                grb_name = raw_name

        # Generate the table
        generator = LaTeXTableGenerator(episodes, grb_name)
        table_content = generator.generate_table()

        # Write to a file
        with open(output_file_path, "w") as f:
            f.write(table_content)

        print(f"LaTeX table generated successfully: {output_file_path}")
        print(f"Processed {len(episodes)} episode(s)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python log_to_latex_parser.py <log_file> [output_file] [grb_name]")
        print("  - If only log_file is provided, generates separate tables for each GRB")
        print("  - If output_file is provided, generates a single combined table")
        sys.exit(1)

    log_file = sys.argv[1]

    if len(sys.argv) >= 3:
        # Legacy mode: single output file
        output_file = sys.argv[2]
        grb_name = sys.argv[3] if len(sys.argv) > 3 else None
        parse_log_and_generate_table(log_file, output_file, grb_name, multi_grb=False)
    else:
        # Multi-GRB mode: generate separate files
        parse_log_and_generate_table(log_file, multi_grb=True)
