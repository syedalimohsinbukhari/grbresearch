# Adding Figures to the Paper

This guide shows how to add figures from your GRB analysis to the reproducible paper.

## Quick Example

### 1. Create a Figure Script

Create a Python script in `src/scripts/` that generates your figure:

```python
# src/scripts/grb_epeak_evolution.py
"""
Generate E_peak evolution plot for GRB 080916C
"""
import sys
sys.path.insert(0, 'src')  # Add src to path to import grb_research

import matplotlib.pyplot as plt
import numpy as np
from paths import figures

# Import your existing GRB analysis modules
from grb_research import grb_core, grb_model

# Your analysis code here - use existing functions from grb_research
# For example:
# data = grb_core.load_grb_data('GRB080916C')
# epeak_values = grb_model.extract_epeak(data)

# For now, a simple example:
time = np.linspace(0, 10, 100)
epeak = 300 * np.exp(-time/5) + 100

# Create figure
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(time, epeak, 'b-', linewidth=2)
ax.set_xlabel('Time (s)')
ax.set_ylabel('$E_{\\rm peak}$ (keV)')
ax.set_title('GRB 080916C')
ax.grid(True, alpha=0.3)

# Save to figures directory
plt.tight_layout()
plt.savefig(figures / "grb080916c_epeak.pdf")
```

### 2. Add to LaTeX Manuscript

In `src/tex/ms.tex`, reference the figure:

```latex
\begin{figure}
    \script{grb_epeak_evolution.py}
    \includegraphics{figures/grb080916c_epeak.pdf}
    \caption{Temporal evolution of $E_{\rm peak}$ for GRB 080916C.}
    \label{fig:grb080916c_epeak}
\end{figure}
```

The `\script{grb_epeak_evolution.py}` directive tells showyourwork:
- Run this script before building the PDF
- Track dependencies automatically
- Include a link to the source code in the margin

### 3. Build the Paper

```bash
showyourwork build
```

Showyourwork will:
1. Run `src/scripts/grb_epeak_evolution.py`
2. Generate `src/tex/figures/grb080916c_epeak.pdf`
3. Compile the LaTeX manuscript with the figure

## Integrating Existing Analysis

### Using Existing Data

Your existing GRB data is in directories like `GRB080916009/`. Reference them:

```python
from pathlib import Path
from paths import root

grb_dir = root / "GRB080916009"
data_file = grb_dir / "your_data_file.dat"
```

### Using Existing Code

Import your analysis modules:

```python
import sys
sys.path.insert(0, 'src')  # Add to Python path

from grb_research.grb_core import *
from grb_research.grb_model import *
# etc.
```

### Using Existing Figures

If you already have figures in `codes-for-paper/`, you can:

**Option 1:** Adapt the existing scripts
- Copy to `src/scripts/`
- Modify to use `from paths import figures`
- Update to save to `figures / "filename.pdf"`

**Option 2:** Symlink existing data
```python
# In a script
import shutil
from paths import figures, root

existing_fig = root / "codes-for-paper" / "peak_energy__best__080916c_110721a.pdf"
shutil.copy(existing_fig, figures / "peak_energy_comparison.pdf")
```

## Advanced: Multiple Figures from One Script

```python
# src/scripts/all_grbs_epeak.py
from paths import figures

for grb in ['080916C', '110721A', '110731A', '150210A']:
    # Generate figure for this GRB
    # ...
    plt.savefig(figures / f"grb{grb}_epeak.pdf")
```

Then in LaTeX:

```latex
\begin{figure*}
    \script{all_grbs_epeak.py}
    \includegraphics[width=0.24\textwidth]{figures/grb080916C_epeak.pdf}
    \includegraphics[width=0.24\textwidth]{figures/grb110721A_epeak.pdf}
    \includegraphics[width=0.24\textwidth]{figures/grb110731A_epeak.pdf}
    \includegraphics[width=0.24\textwidth]{figures/grb150210A_epeak.pdf}
    \caption{$E_{\rm peak}$ evolution for all four GRBs.}
\end{figure*}
```

## Tips

1. **Keep scripts focused**: One script per figure or related set of figures
2. **Use relative paths**: Always use the `paths` module
3. **Add dependencies**: If your script needs external data, specify in `showyourwork.yml`
4. **Test locally**: Run scripts individually to debug before building the paper
5. **Reuse existing code**: Import from `grb_research` package to avoid duplication

## Troubleshooting

**Import errors**: Make sure to add `src` to the Python path:
```python
import sys
sys.path.insert(0, 'src')
```

**Missing data**: Specify external datasets in `showyourwork.yml` under `dependencies`

**Script doesn't run**: Test it standalone first:
```bash
cd src/scripts
python grb_epeak_evolution.py
```
