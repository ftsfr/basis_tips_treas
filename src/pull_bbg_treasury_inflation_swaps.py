"""
Pull Treasury Inflation Swaps from Bloomberg.
"""

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, "./src")

import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"

START_DATE = "2000-01-01"
END_DATE = str(date.today())


def pull_treasury_inflation_swaps(start_date=START_DATE, end_date=END_DATE):
    """
    Connects to Bloomberg via xbbg, pulls historical daily prices for USD
    Treasury Inflation Swaps.
    """
    from xbbg import blp

    print(">> Pulling Treasury Inflation Swaps from Bloomberg...")

    tickers = [
        "USSWIT1 BGN Curncy",   # 1Y
        "USSWIT2 BGN Curncy",   # 2Y
        "USSWIT3 BGN Curncy",   # 3Y
        "USSWIT4 BGN Curncy",   # 4Y
        "USSWIT5 BGN Curncy",   # 5Y
        "USSWIT10 BGN Curncy",  # 10Y
        "USSWIT20 BGN Curncy",  # 20Y
        "USSWIT30 BGN Curncy",  # 30Y
    ]

    fields = ["PX_LAST"]

    df = blp.bdh(tickers=tickers, flds=fields, start_date=start_date, end_date=end_date)
    df.columns = df.columns.droplevel(level=1)
    df = df.reset_index()
    df = df.rename(columns={"index": "Dates", "date": "Dates"})

    col_order = ["Dates"] + tickers
    df = df[col_order]

    print(f">> Records: {len(df):,}")
    return df


def load_treasury_inflation_swaps(data_dir=DATA_DIR):
    """Load Treasury Inflation Swaps from parquet file."""
    return pd.read_parquet(data_dir / "treasury_inflation_swaps.parquet")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pull_treasury_inflation_swaps()
    output_path = DATA_DIR / "treasury_inflation_swaps.parquet"
    df.to_parquet(output_path, index=False)
    print(f">> Saved {output_path}")


if __name__ == "__main__":
    import pandas as pd
    main()
