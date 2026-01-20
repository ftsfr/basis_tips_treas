"""
Pull zero coupon TIPS yield curve from the Federal Reserve.
"""

import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, "./src")

import pandas as pd
import requests

import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"

# URL for the TIPS yield data
TIPS_URL = "https://www.federalreserve.gov/data/yield-curve-tables/feds200805.csv"


def pull_fed_tips_yield_curve():
    """
    Download and process the latest zero-coupon TIPS yield curve from the Federal Reserve.
    """
    print(">> Pulling Fed TIPS yield curve...")
    response = requests.get(TIPS_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch TIPS data: HTTP {response.status_code}")

    df = pd.read_csv(BytesIO(response.content), skiprows=18)
    print(f">> Records: {len(df):,}")
    return df


def load_fed_tips_yield_curve(data_dir=DATA_DIR):
    path = data_dir / "fed_tips_yield_curve.parquet"
    return pd.read_parquet(path)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pull_fed_tips_yield_curve()
    path = DATA_DIR / "fed_tips_yield_curve.parquet"
    df.to_parquet(path)
    print(f">> Saved {path}")


if __name__ == "__main__":
    main()
