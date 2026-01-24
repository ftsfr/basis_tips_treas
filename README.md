# TIPS-Treasury Basis

TIPS-Treasury arbitrage spread measuring relative value between TIPS and nominal Treasuries.

## Overview

The TIPS-implied risk-free rate is:

```
TIPS-implied RF = 10000 × (exp(r_real + ln(1 + π)) - 1)
```

Where:
- r_real: TIPS real yield (continuously compounded)
- π: Inflation swap rate

The arbitrage spread is:
```
Arb = TIPS-implied RF - Nominal Treasury
```

## Interpretation

- **Positive spread**: TIPS appear cheap relative to nominal Treasuries
- **Negative spread**: TIPS appear expensive

## Tenors

- 2-year (arb_2)
- 5-year (arb_5)
- 10-year (arb_10)
- 20-year (arb_20)

## Data Sources

- **Federal Reserve**: Zero-coupon Treasury yields (GSW model)
- **Federal Reserve**: Zero-coupon TIPS yields
- **Bloomberg**: Treasury inflation swaps

## Outputs

- `ftsfr_tips_treasury_basis.parquet`: Daily arbitrage spreads for all tenors

## Requirements

- Bloomberg Terminal (for inflation swaps)
- Python 3.10+
- xbbg package

## Setup

1. Ensure Bloomberg Terminal is running
2. Install dependencies: `pip install -r requirements.txt`
3. Run pipeline: `doit`

## Academic References

### Primary Papers

- **Fleckenstein, Longstaff, and Lustig (2014)** - "The TIPS-Treasury Bond Puzzle"
  - Journal of Finance
  - Documents persistent mispricing between TIPS and nominal Treasuries

- **Siriwardane, Sunderam, and Wallen** - "Segmented Arbitrage"
  - Links TIPS-Treasury basis to financial constraints

### Key Findings

- Mispricing can exceed $20 per $100 notional
- Average mispricing is 54.5 basis points, can exceed 200 bps
- Slow-moving capital explains persistence of arbitrage
