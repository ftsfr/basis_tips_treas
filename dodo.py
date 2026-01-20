"""
Doit build file for TIPS-Treasury Basis pipeline.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

import chartbook

sys.path.insert(1, "./src/")


# Bloomberg Terminal check - runs at module load time
def _check_bloomberg_terminal():
    """Check Bloomberg Terminal availability with env var override."""
    # Skip prompt if environment variable is set
    if os.environ.get("BLOOMBERG_TERMINAL_OPEN", "").lower() in ("true", "1", "yes"):
        print("BLOOMBERG_TERMINAL_OPEN=True detected, skipping prompt...")
        return True

    # Interactive prompt
    response = input("Do you have the Bloomberg terminal open in the background? [Y/n]: ")
    if response.lower() in ('n', 'no'):
        raise SystemExit(
            "\nBloomberg Terminal not available. Exiting.\n"
            "Tip: Set BLOOMBERG_TERMINAL_OPEN=True to skip this prompt."
        )
    return True


_check_bloomberg_terminal()

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"
OUTPUT_DIR = BASE_DIR / "_output"
NOTEBOOK_BUILD_DIR = OUTPUT_DIR / "_notebook_build"


def jupyter_execute_notebook(notebook):
    """Execute a notebook and convert to HTML."""
    subprocess.run(
        [
            "jupyter", "nbconvert", "--execute", "--to", "html",
            "--output-dir", str(OUTPUT_DIR), str(notebook),
        ],
        check=True,
    )


def task_config():
    """Create directories for data and output."""

    def create_dirs():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        NOTEBOOK_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "actions": [create_dirs],
        "targets": [DATA_DIR, OUTPUT_DIR, NOTEBOOK_BUILD_DIR],
        "verbosity": 2,
    }


def task_pull_fed_yield_curve():
    """Pull Fed zero-coupon Treasury yields."""
    return {
        "actions": ["python src/pull_fed_yield_curve.py"],
        "file_dep": ["src/pull_fed_yield_curve.py"],
        "targets": [DATA_DIR / "fed_yield_curve.parquet"],
        "verbosity": 2,
        "task_dep": ["config"],
    }


def task_pull_fed_tips_yield_curve():
    """Pull Fed zero-coupon TIPS yields."""
    return {
        "actions": ["python src/pull_fed_tips_yield_curve.py"],
        "file_dep": ["src/pull_fed_tips_yield_curve.py"],
        "targets": [DATA_DIR / "fed_tips_yield_curve.parquet"],
        "verbosity": 2,
        "task_dep": ["config"],
    }


def task_pull_inflation_swaps():
    """Pull Treasury inflation swaps from Bloomberg."""
    return {
        "actions": ["python src/pull_bbg_treasury_inflation_swaps.py"],
        "file_dep": ["src/pull_bbg_treasury_inflation_swaps.py"],
        "targets": [DATA_DIR / "treasury_inflation_swaps.parquet"],
        "verbosity": 2,
        "task_dep": ["config"],
    }


def task_calc():
    """Compute TIPS-Treasury basis."""
    return {
        "actions": ["python src/compute_tips_treasury.py"],
        "file_dep": [
            "src/compute_tips_treasury.py",
            DATA_DIR / "fed_yield_curve.parquet",
            DATA_DIR / "fed_tips_yield_curve.parquet",
            DATA_DIR / "treasury_inflation_swaps.parquet",
        ],
        "targets": [DATA_DIR / "tips_treasury_implied_rf.parquet"],
        "verbosity": 2,
        "task_dep": ["pull_fed_yield_curve", "pull_fed_tips_yield_curve", "pull_inflation_swaps"],
    }


def task_format():
    """Create FTSFR standardized datasets."""
    return {
        "actions": ["python src/create_ftsfr_datasets.py"],
        "file_dep": [
            "src/create_ftsfr_datasets.py",
            DATA_DIR / "tips_treasury_implied_rf.parquet",
        ],
        "targets": [DATA_DIR / "ftsfr_tips_treasury_basis.parquet"],
        "verbosity": 2,
        "task_dep": ["calc"],
    }


def task_run_notebooks():
    """Execute summary notebook and convert to HTML."""
    notebook_py = BASE_DIR / "src" / "summary_basis_tips_treas_ipynb.py"
    notebook_ipynb = NOTEBOOK_BUILD_DIR / "summary_basis_tips_treas.ipynb"

    def run_notebook():
        subprocess.run(
            ["ipynb-py-convert", str(notebook_py), str(notebook_ipynb)],
            check=True,
        )
        jupyter_execute_notebook(notebook_ipynb)

    return {
        "actions": [run_notebook],
        "file_dep": [
            notebook_py,
            DATA_DIR / "ftsfr_tips_treasury_basis.parquet",
        ],
        "targets": [
            notebook_ipynb,
            OUTPUT_DIR / "summary_basis_tips_treas.html",
        ],
        "verbosity": 2,
        "task_dep": ["format"],
    }


def task_generate_pipeline_site():
    """Generate chartbook documentation site."""
    return {
        "actions": ["chartbook build -f"],
        "file_dep": [
            "chartbook.toml",
            NOTEBOOK_BUILD_DIR / "summary_basis_tips_treas.ipynb",
        ],
        "targets": [BASE_DIR / "docs" / "index.html"],
        "verbosity": 2,
        "task_dep": ["run_notebooks"],
    }
