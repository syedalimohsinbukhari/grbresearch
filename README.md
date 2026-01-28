# GRBResearch

Research repository for time-resolved spectral analysis of Gamma-Ray Bursts (GRBs) with blackbody components.

## Overview

This repository contains analysis code and a reproducible research paper for studying four GRBs observed by Fermi-GBM:
- GRB 080916C
- GRB 110721A  
- GRB 110731A
- GRB 150210A

The analysis focuses on characterizing thermal (blackbody) components in GRB spectra to understand photospheric emission mechanisms.

## Repository Structure

```
GRBResearch/
├── src/                          # Source code and paper
│   ├── grb_research/             # Python package for GRB analysis
│   ├── tex/                      # LaTeX manuscript files
│   ├── scripts/                  # Figure-generating scripts for paper
│   ├── data/                     # Input data files
│   └── static/                   # Static images
├── codes-for-paper/              # Analysis scripts for figures
├── light_curves/                 # Light curve analysis
├── GRB*/                         # Individual GRB data directories
├── Literature Review/            # Reference papers
├── showyourwork.yml              # Paper build configuration
├── environment.yml               # Conda environment for paper
└── requirements.txt              # Python dependencies for analysis code
```

## Research Paper

This repository uses [showyourwork](https://show-your.work/) to create a fully reproducible research article. The manuscript source is in `src/tex/ms.tex`, and all figures are generated from scripts in `src/scripts/`.

### Building the Paper

**Note:** Building locally requires Python 3.11 or earlier due to dependency compatibility. See [BUILD.md](BUILD.md) for detailed instructions.

Quick start with conda:
```bash
conda create -n grb-paper python=3.11
conda activate grb-paper
pip install showyourwork
showyourwork build
```

The paper is also automatically built on GitHub Actions.

### Paper Features

- Fully reproducible: All figures generated from code
- Automatic dependency tracking
- Integration with existing analysis code
- GitHub Actions for automated builds

See the [showyourwork documentation](https://show-your.work/) for more details.

## Analysis Code

The Python package `grb_research` contains modules for:
- Spectral analysis
- Time-resolved fitting
- Model comparisons
- Parameter extraction

### Installation

```bash
pip install -r requirements.txt
```

### Usage

```python
from src.grb_research import grb_core, grb_model
# Your analysis code here
```

## Data

GRB data is organized in individual directories (GRB080916009, etc.) containing:
- Light curves
- Spectral data
- Fitting results

## License

See LICENSE file for details.

## Contact

For questions about this research, please open an issue on this repository.