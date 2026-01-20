"""
Compute TIPS-Treasury basis (arbitrage spread).

The TIPS-implied risk-free rate is:
    tips_treas_{t}_rf = 1e4 * (exp(real_cc{t} + log(1 + inf_swap_{t}y)) - 1)

The arbitrage spread is:
    arb_{t} = tips_treas_{t}_rf - nom_zc{t}
"""

import sys
from pathlib import Path

sys.path.insert(0, "./src")

import os
import numpy as np
import pandas as pd
import polars as pl

import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"


def import_inflation_swap_data(data_dir=DATA_DIR):
    """Load Bloomberg inflation swap data."""
    swaps_path = os.path.join(data_dir, "treasury_inflation_swaps.parquet")

    swaps = pd.read_parquet(swaps_path)
    if "Dates" in swaps.columns and not pd.api.types.is_datetime64_any_dtype(swaps["Dates"]):
        swaps["Dates"] = pd.to_datetime(swaps["Dates"])

    column_map = {
        "Dates": "date",
        "USSWITA BGN Curncy": "inf_swap_1m",
        "USSWITC BGN Curncy": "inf_swap_3m",
        "USSWITF BGN Curncy": "inf_swap_6m",
        "USSWIT1 BGN Curncy": "inf_swap_1y",
        "USSWIT2 BGN Curncy": "inf_swap_2y",
        "USSWIT3 BGN Curncy": "inf_swap_3y",
        "USSWIT4 BGN Curncy": "inf_swap_4y",
        "USSWIT5 BGN Curncy": "inf_swap_5y",
        "USSWIT10 BGN Curncy": "inf_swap_10y",
        "USSWIT20 BGN Curncy": "inf_swap_20y",
        "USSWIT30 BGN Curncy": "inf_swap_30y",
    }

    swaps = swaps.rename(columns=column_map)

    inf_cols = [
        "inf_swap_1y", "inf_swap_2y", "inf_swap_3y", "inf_swap_4y",
        "inf_swap_5y", "inf_swap_10y", "inf_swap_20y", "inf_swap_30y",
    ]
    for col in inf_cols:
        if col in swaps.columns:
            swaps[col] = pd.to_numeric(swaps[col], errors="coerce") / 100.0

    available_cols = ["date"] + [c for c in inf_cols if c in swaps.columns]
    swaps = swaps[available_cols]

    return swaps


def import_treasury_yields(data_dir=DATA_DIR):
    """Load Fed zero-coupon Treasury yields."""
    nom_path = os.path.join(data_dir, "fed_yield_curve.parquet")

    nom = pd.read_parquet(nom_path)

    if not pd.api.types.is_datetime64_any_dtype(nom.index):
        nom.index = pd.to_datetime(nom.index, format="%m/%d/%Y")

    if nom.index.name is None or nom.index.name == "Date":
        nom.index.name = "date"

    # Compute nominal zero-coupon yield in basis points for each tenor
    for t in [2, 5, 10, 20]:
        col = f"SVENY{'0' + str(t) if t < 10 else str(t)}"
        nom[f"nom_zc{t}"] = 1e4 * (np.exp(nom[col] / 100) - 1)

    nom = nom.reset_index()
    nom = nom.rename(columns={"Date": "date"})
    nom = nom[["date"] + [col for col in nom.columns if col.startswith("nom")]]

    return nom


def import_tips_yields(data_dir=DATA_DIR):
    """Load Fed zero-coupon TIPS yields."""
    real_path = os.path.join(data_dir, "fed_tips_yield_curve.parquet")
    real = pd.read_parquet(real_path)

    if "Date" in real.columns:
        real.rename(columns={"Date": "date"}, inplace=True)
        if not pd.api.types.is_datetime64_any_dtype(real["date"]):
            real["date"] = pd.to_datetime(real["date"], format="%Y-%m-%d")

    for t in [2, 5, 10, 20]:
        col = f"TIPSY{'0' + str(t) if t < 10 else str(t)}"
        if col in real.columns:
            real[f"real_cc{t}"] = real[col] / 100

    real = real[["date"] + [col for col in real.columns if col.startswith("real")]]

    return real


def compute_tips_treasury(data_dir=DATA_DIR):
    """
    Compute TIPS-Treasury arbitrage spread.

    Returns DataFrame with:
    - date: Observation date
    - real_*: TIPS real yields (decimal)
    - nom_*: Nominal zero-coupon yields (basis points)
    - tips_*: TIPS-implied risk-free rates (basis points)
    - arb_*: Arbitrage spreads (basis points)
    """
    print(">> Computing TIPS-Treasury basis...")

    real = import_tips_yields(data_dir=data_dir)
    nom = import_treasury_yields(data_dir=data_dir)
    swaps = import_inflation_swap_data(data_dir=data_dir)

    merged = pd.merge(real, nom, on="date", how="inner")
    merged = pd.merge(merged, swaps, on="date", how="inner")

    # Compute implied riskless rates and arbitrage measures
    missing_indicators = []
    for t in [2, 5, 10, 20]:
        merged[f"tips_treas_{t}_rf"] = 1e4 * (
            np.exp(merged[f"real_cc{t}"] + np.log(1 + merged[f"inf_swap_{t}y"])) - 1
        )
        merged[f"mi_{t}"] = merged[f"tips_treas_{t}_rf"].isna().astype(int)
        missing_indicators.append(f"mi_{t}")

        # Arbitrage spread
        merged[f"arb_{t}"] = merged[f"tips_treas_{t}_rf"] - merged[f"nom_zc{t}"]

    merged["miss_count"] = merged[missing_indicators].sum(axis=1)
    merged = merged[merged["miss_count"] < 4]
    merged = merged.drop(missing_indicators + ["miss_count"], axis=1)

    cols_to_keep = (
        ["date"]
        + [col for col in merged.columns if col.startswith("real_")]
        + [col for col in merged.columns if col.startswith("nom_")]
        + [col for col in merged.columns if col.startswith("tips_")]
        + [col for col in merged.columns if col.startswith("arb_")]
    )
    merged = merged[cols_to_keep]

    print(f">> Records: {len(merged):,}")
    return merged


def load_tips_treasury(data_dir=DATA_DIR):
    """Load computed TIPS-Treasury data."""
    df = pl.read_parquet(os.path.join(data_dir, "tips_treasury_implied_rf.parquet"))
    if "__index_level_0__" in df.columns:
        df = df.drop("__index_level_0__")
    return df


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    merged = compute_tips_treasury(data_dir=DATA_DIR)
    output_path = DATA_DIR / "tips_treasury_implied_rf.parquet"
    merged.to_parquet(output_path, compression="snappy")
    print(f">> Saved {output_path}")


if __name__ == "__main__":
    main()
