# POSC301
# Deficits, Inflation, and Party 🏛️

An interactive Streamlit dashboard that simulates whether larger U.S. federal deficits are associated with higher next-year inflation, and whether that effect is stronger under Republican presidents.

## Research Question
Since 1980, are larger U.S. federal deficits associated with higher inflation in the following year, and why does this relationship differ under Democratic versus Republican presidents?

## Hypothesis
Since 1980, larger U.S. federal deficits are associated with higher next-year inflation, and this effect is stronger under Republican presidents.

## What This Dashboard Does
- Simulates yearly U.S. data from 1980–2025
- Lets the user adjust:
  - year range
  - base inflation
  - deficit effect
  - Republican deficit boost
  - oil shock effect
  - recession effect
  - random variation
- Visualizes:
  - deficits and next-year inflation over time
  - the relationship between deficits and next-year inflation
  - average simulated values by administration
- Displays a simulated dataset and allows CSV download

## Built With
- Python
- Streamlit
- Plotly
- Pandas
- NumPy

## Run Locally
```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run inflation_simulationV8.py
