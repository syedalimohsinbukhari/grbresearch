# Building the Paper Locally

## Requirements

Due to dependency compatibility issues between snakemake 7.15.2 and Python 3.12, building the paper locally requires Python 3.11 or earlier.

## Recommended Setup

### Option 1: Using Conda (Recommended)

Create a dedicated environment for building the paper:

```bash
conda create -n grb-paper python=3.11
conda activate grb-paper
pip install showyourwork
showyourwork build
```

### Option 2: Using Docker

You can also use the showyourwork Docker image:

```bash
docker run -it -v $(pwd):/work ghcr.io/showyourwork/showyourwork:latest build
```

### Option 3: GitHub Actions

The paper is automatically built on GitHub Actions when changes are pushed. The built PDF is available as an artifact in the Actions tab.

## Build Process

Once you have a compatible environment:

1. Navigate to the repository root
2. Run `showyourwork build`
3. The compiled PDF will be `ms.pdf`

## Troubleshooting

If you encounter issues with Python 3.12:
- Use Python 3.11 or earlier
- The error is typically `AttributeError: module 'asyncio' has no attribute 'coroutine'`
- This is a known issue with snakemake 7.15.2 and Python 3.12

If you encounter issues with pulp:
- The environment.yml constrains pulp to versions <2.8.0 for compatibility with snakemake 7.15.2
- If you installed showyourwork separately, you may need to downgrade: `pip install 'pulp<2.8.0'`

The BUILD.md documentation states that the GitHub Actions workflow uses Python 3.12, but the actual workflow file (.github/workflows/build-paper.yml) specifies Python 3.11. This is correct - the workflow uses Python 3.11 to ensure compatibility.
