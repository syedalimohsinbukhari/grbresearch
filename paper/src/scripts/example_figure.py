"""
Example figure script demonstrating integration with existing GRB analysis code.

This script creates a simple demonstration figure. In a real analysis, this would
import the GRB analysis modules and generate publication-quality figures.
"""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Import the paths module for consistent file locations
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from paper.src.scripts.paths import figures

# Simple example: Create a demonstration plot
# In practice, this would use the actual GRB data and analysis from src/grb_research/

fig, ax = plt.subplots(1, 1, figsize=(6, 4))

# Example data (replace with actual analysis)
time = np.linspace(0, 10, 100)
epeak = 300 * np.exp(-time/5) + 100  # Example Epeak evolution

ax.plot(time, epeak, 'b-', linewidth=2, label='$E_{\\rm peak}$')
ax.set_xlabel('Time (s)', fontsize=12)
ax.set_ylabel('$E_{\\rm peak}$ (keV)', fontsize=12)
ax.set_title('Example: Temporal Evolution of $E_{\\rm peak}$', fontsize=14)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Save the figure
plt.tight_layout()
plt.savefig(figures / "example_epeak_evolution.pdf", dpi=300, bbox_inches='tight')
plt.close()

print("Example figure generated successfully!")
