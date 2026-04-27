"""Convert amati_relationship.csv to LaTeX table format."""

import numpy as np
import pandas as pd


def format_value_with_errors(value, err_lower, err_upper, scientific=False, decimals=3):
    """
    Format a value with asymmetric errors for LaTeX.

    Parameters
    ----------
    value : float
        Central value
    err_lower : float
        Lower error (positive value)
    err_upper : float
        Upper error (positive value)
    scientific : bool
        Use scientific notation
    decimals : int
        Number of decimal places

    Returns
    -------
    str
        LaTeX formatted string like $value_{-lower}^{+upper}$
    """
    if scientific:
        # Format in scientific notation
        exp = int(np.floor(np.log10(abs(value))))
        val_mantissa = value / (10 ** exp)
        err_l_mantissa = err_lower / (10 ** exp)
        err_u_mantissa = err_upper / (10 ** exp)

        return f"${val_mantissa:.{decimals}f}_{{-{err_l_mantissa:.{decimals}f}}}^{{+{err_u_mantissa:.{decimals}f}}} \\times 10^{{{exp}}}$"
    else:
        return f"${value:.{decimals}f}_{{-{err_lower:.{decimals}f}}}^{{+{err_upper:.{decimals}f}}}$"


def format_grb_name(grb_name):
    """Format GRB name for LaTeX."""
    # Extract the numeric part after 'GRB'
    numeric = grb_name.replace('GRB', '')
    return f"GRB~{numeric}"


def format_model_name(model_name):
    """Format model name for LaTeX."""
    # Replace underscores with + signs
    return model_name.replace('_', '+')


def csv_to_latex_table(csv_path='amati_relationship.csv', output_path='amati_relationship_table.tex'):
    """
    Convert the Amati relationship CSV to a LaTeX table.

    Parameters
    ----------
    csv_path : str
        Path to input CSV file
    output_path : str
        Path to output LaTeX file
    """
    # Read CSV
    df = pd.read_csv(csv_path)

    # Start building LaTeX table
    latex_lines = []
    latex_lines.append("\\begin{table}[!ht]")
    latex_lines.append("    \\centering")
    latex_lines.append("    \\caption{}")
    latex_lines.append("    \\label{tab:eiso}")
    latex_lines.append("    \\renewcommand{\\arraystretch{1.25}}")
    latex_lines.append("    \\resizebox{\\columnwidth}{!}{")
    latex_lines.append("    \\begin{tabular}{llcc}")
    latex_lines.append("        \\toprule")
    latex_lines.append("        Model & Episode & "
                       "$E_{i,\\mathrm{peak}}$ [MeV] & $E^{52}_{\\mathrm{iso}}$ [erg] \\\\")
    latex_lines.append("        \\midrule")

    current_grb = None

    for idx, row in df.iterrows():
        grb_name = row['GRBName']
        model_name = format_model_name(row['Model'])
        episode_name = row['EpisodeName']

        # Add GRB header when we encounter a new GRB
        if grb_name != current_grb:
            # Add multicolumn row for GRB name
            grb_display = grb_name  # Keep the full GRB080916C format
            if idx != 0:
                latex_lines.append("        \\midrule")
            latex_lines.append(f"        \\multicolumn{{4}}{{l}}{{\\textbf{{{grb_display}}}}} \\\\")
            current_grb = grb_name

        # Format E_peak with errors
        ep_val = row['E_i_peak__keV']
        ep_err_l = row['E_i_peak_err_lower__keV']
        ep_err_u = row['E_i_peak_err_upper__keV']

        # Determine if we should use scientific notation for E_peak
        if ep_val >= 10000:
            ep_str = format_value_with_errors(ep_val, ep_err_l, ep_err_u, scientific=True, decimals=4)
        else:
            ep_str = format_value_with_errors(ep_val, ep_err_l, ep_err_u, scientific=False, decimals=4)

        # Format E_iso with errors
        ei_val = row['E_0_iso__1e52_erg']
        ei_err_l = row['E_0_iso_err_lower__1e52_erg']
        ei_err_u = row['E_0_iso_err_upper__1e52_erg']
        ei_str = format_value_with_errors(ei_val, ei_err_l, ei_err_u, scientific=False, decimals=4)

        # Build table row
        latex_lines.append(f"        {model_name} & {episode_name} & "
                           f"{ep_str} & {ei_str} \\\\")

    latex_lines.append("        \\bottomrule")
    latex_lines.append("    \\end{tabular}")
    latex_lines.append("    }")
    latex_lines.append("    \\label{tab:amati_relationship}")
    latex_lines.append("\\end{table}")

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(latex_lines))

    print(f"LaTeX table written to {output_path}")
    print(f"Total rows: {len(df)}")

    # Also print to console
    print("\n" + "=" * 80)
    print("LaTeX Table Preview:")
    print("=" * 80)
    for line in latex_lines:
        print(line)


if __name__ == "__main__":
    csv_to_latex_table()
