# Deficits, Inflation, and Presidential Party

A Streamlit dashboard that uses real U.S. government data to explore whether larger federal deficits are associated with higher inflation, and whether that relationship looks different under Democratic and Republican presidencies.

## Main app

`inflation_simulationV10.py`

## Run locally

```bash
python3 -m pip install -r requirements.txt
streamlit run inflation_simulationV10.py
```

## Data used

This version does not use simulated values.

It uses a cleaned local panel in `data/official_fiscal_inflation_panel.csv`, built from:

- OMB Historical Table 1.2 for federal surplus or deficit as a percent of GDP
- BLS CPI-U historical tables for annual average CPI-U values

## Important design choice

OMB publishes surpluses as positive and deficits as negative. In the dashboard, that sign is flipped so higher plotted values always mean larger deficits. The original OMB sign is still preserved in the downloadable panel.

## Source links

- GovInfo / OMB Table 1.2: https://www.govinfo.gov/app/details/BUDGET-2025-TAB/BUDGET-2025-TAB-2-2
- BLS historical CPI-U archive: https://www.bls.gov/cpi/tables/supplemental-files/historical-cpi-u-201901.pdf
- BLS U.S. city average CPI table: https://www.bls.gov/regions/northeast/data/consumerpriceindex_us_table.htm

## Notes

- The OMB FY2025 historical table includes estimate rows for 2024-2029. Those estimated rows are excluded.
- The main dashboard default aligns fiscal year deficit in year `t` with CPI-U inflation in year `t+1`.
- The app is descriptive and presentation-ready, but it is not a causal identification strategy on its own.
