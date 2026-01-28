# GRB Research Paper

This directory contains a research paper setup using [showyourwork](https://show-your.work/), a workflow for creating reproducible scientific articles.

## Overview

This paper presents a time-resolved spectral analysis of four Gamma-Ray Bursts (GRBs) observed by Fermi-GBM:
- GRB 080916C
- GRB 110721A
- GRB 110731A
- GRB 150210A

The analysis focuses on characterizing blackbody components in their spectra and understanding the temporal evolution of spectral parameters.

## Structure

```
paper/
├── src/
│   ├── tex/           # LaTeX manuscript files
│   │   ├── ms.tex     # Main manuscript
│   │   ├── bib.bib    # Bibliography
│   │   └── figures/   # Generated figures (auto-populated)
│   ├── scripts/       # Python scripts for figures and analysis
│   ├── data/          # Input data files
│   └── static/        # Static images/figures
├── showyourwork.yml   # Configuration file
├── environment.yml    # Conda environment specification
└── Snakefile          # Snakemake workflow (usually empty for showyourwork)
```

## Building the Paper

### Prerequisites

1. Install showyourwork:
   ```bash
   pip install showyourwork
   ```

2. Install conda/mamba for environment management

### Build Commands

To build the paper:
```bash
cd paper
showyourwork build
```

To clean the build:
```bash
cd paper
showyourwork clean
```

To generate a tarball for arXiv submission:
```bash
cd paper
showyourwork tarball
```

## Workflow

Showyourwork automates the following:
1. Sets up a reproducible conda environment
2. Runs analysis scripts to generate figures
3. Compiles the LaTeX manuscript
4. Ensures all figures can be traced back to their source code
5. Creates a dependency graph of the entire workflow

## Integration with Existing Code

The paper integrates with the existing GRB analysis code in the repository:
- Python modules in `src/grb_research/` can be imported in analysis scripts
- Data files from the main repository can be referenced
- Analysis results from `codes-for-paper/` can be incorporated

## Adding Figures

To add a figure to the paper:

1. Create a Python script in `src/scripts/` that generates the figure:
   ```python
   # src/scripts/my_figure.py
   import matplotlib.pyplot as plt
   from paths import figures
   
   # Your analysis code here
   plt.figure()
   # ... plotting code ...
   plt.savefig(figures / "my_figure.pdf")
   ```

2. Reference it in the manuscript:
   ```latex
   \begin{figure}
       \script{my_figure.py}
       \includegraphics{figures/my_figure.pdf}
       \caption{My figure caption}
   \end{figure}
   ```

Showyourwork will automatically run the script when building the paper and track the dependency.

## Configuration

Edit `showyourwork.yml` to configure:
- Caching behavior
- External datasets
- Custom dependencies
- Build options

## Resources

- [Showyourwork documentation](https://show-your.work/)
- [Example repositories](https://github.com/showyourwork/showyourwork/tree/main/examples)
- [Tutorial](https://show-your.work/en/latest/tutorials/)
