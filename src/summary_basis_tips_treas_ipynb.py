# %%
"""
# TIPS-Treasury Basis Summary

The TIPS-Treasury basis measures the arbitrage spread between TIPS-implied
risk-free rates and nominal Treasury yields.
"""

# %%
import sys
sys.path.insert(0, "./src")

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl

import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"

# %%
"""
## Methodology

The TIPS-implied risk-free rate is:

$$
\\text{TIPS-implied RF}_t = 10000 \\times \\left( e^{r_{\\text{real},t} + \\ln(1 + \\pi_t)} - 1 \\right)
$$

Where:
- $r_{\\text{real}}$: TIPS real yield (continuously compounded)
- $\\pi$: Inflation swap rate

The arbitrage spread is:
$$
\\text{Arbitrage}_t = \\text{TIPS-implied RF}_t - \\text{Nominal Treasury}_t
$$

### Interpretation

- Positive spread: TIPS appear cheap relative to nominal Treasuries
- Negative spread: TIPS appear expensive

### Data Sources

- Federal Reserve: Zero-coupon Treasury yields (GSW model)
- Federal Reserve: Zero-coupon TIPS yields
- Bloomberg: Treasury inflation swaps
"""

# %%
"""
## Data Overview
"""

# %%
df = pl.read_parquet(DATA_DIR / "ftsfr_tips_treasury_basis.parquet")
df_pd = df.to_pandas()
print(f"Shape: {df_pd.shape}")
print(f"Columns: {df_pd.columns.tolist()}")
print(f"\nDate range: {df_pd['ds'].min()} to {df_pd['ds'].max()}")
print(f"Number of tenors: {df_pd['unique_id'].nunique()}")

# %%
print("\nTenors:")
for tenor in sorted(df_pd['unique_id'].unique()):
    print(f"  {tenor}")

# %%
"""
### Summary Statistics
"""

# %%
basis_wide = df_pd.pivot(index='ds', columns='unique_id', values='y')
basis_stats = basis_wide.describe().T
basis_stats['skewness'] = basis_wide.skew()
basis_stats['kurtosis'] = basis_wide.kurtosis()
print(basis_stats[['mean', 'std', 'min', 'max', 'skewness', 'kurtosis']].round(2).to_string())

# %%
"""
### TIPS-Treasury Basis Time Series
"""

# %%
fig, ax = plt.subplots(figsize=(14, 8))

for tenor in ['arb_2', 'arb_5', 'arb_10', 'arb_20']:
    if tenor in basis_wide.columns:
        ax.plot(basis_wide.index, basis_wide[tenor], label=tenor.replace('arb_', '') + 'Y', alpha=0.8)

ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax.set_xlabel('Date')
ax.set_ylabel('Arbitrage Spread (bps)')
ax.set_title('TIPS-Treasury Arbitrage Basis')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(DATA_DIR.parent / "_output" / "tips_treasury_basis.png", dpi=150, bbox_inches='tight')
plt.show()

# %%
"""
### Correlation Matrix
"""

# %%
fig, ax = plt.subplots(figsize=(8, 6))
corr = basis_wide.corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax)
ax.set_title('TIPS-Treasury Basis Correlations')
plt.tight_layout()
plt.savefig(DATA_DIR.parent / "_output" / "tips_treasury_correlation.png", dpi=150, bbox_inches='tight')
plt.show()

# %%
"""
## Data Definitions

### TIPS-Treasury Basis (ftsfr_tips_treasury_basis)

| Variable | Description |
|----------|-------------|
| unique_id | Tenor identifier (arb_2, arb_5, arb_10, arb_20) |
| ds | Date |
| y | Arbitrage spread in basis points |

### Tenors

| ID | Maturity |
|----|----------|
| arb_2 | 2-year |
| arb_5 | 5-year |
| arb_10 | 10-year |
| arb_20 | 20-year |
"""
