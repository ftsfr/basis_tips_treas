"""
Create FTSFR standardized datasets for TIPS-Treasury basis.

Outputs:
- ftsfr_tips_treasury_basis.parquet: Daily TIPS-Treasury arbitrage spreads
"""

import sys
from pathlib import Path

sys.path.insert(0, "./src")

import polars as pl

import chartbook
import compute_tips_treasury

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(">> Creating ftsfr_tips_treasury_basis...")
    df = compute_tips_treasury.load_tips_treasury(data_dir=DATA_DIR)

    df_long = (
        df.select(["date", "arb_2", "arb_5", "arb_10", "arb_20"])
        .with_columns(pl.col("date").cast(pl.Datetime))
        .unpivot(index=["date"], variable_name="unique_id", value_name="y")
        .rename({"date": "ds"})
        .select(["unique_id", "ds", "y"])
    )

    df_long = df_long.drop_nulls()
    df_long = df_long.sort(["unique_id", "ds"])

    output_path = DATA_DIR / "ftsfr_tips_treasury_basis.parquet"
    df_long.write_parquet(output_path)
    print(f"   Saved: {output_path.name}")
    print(f"   Records: {len(df_long):,}")
    print(f"   Tenors: {df_long['unique_id'].n_unique()}")


if __name__ == "__main__":
    main()
