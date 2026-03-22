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
## Simulation Equations

This dashboard uses a simple simulation model to represent the relationship between federal deficits, inflation, presidential party, recessions, and oil shocks over time.

### 1. Presidential Party
Party_t = 1 if the president in year t is Republican  
Party_t = 0 if the president in year t is Democratic

### 2. Recession Indicator
Recession_t = 1 if year t is a recession year  
Recession_t = 0 otherwise

### 3. Simulated Federal Deficit
Deficit_t = 3.0 + 1.0(Recession_t) + 0.65(sine time pattern) + random noise

In selected years, an extra deficit spike is added.

### 4. Simulated Oil Shock
OilShock_t = random noise + selected spike years

### 5. Simulated Next-Year Inflation
Inflation_(t+1) = base inflation  
+ deficit effect × Deficit_t  
+ oil effect × OilShock_t  
+ recession effect × Recession_t  
+ Republican boost × (Deficit_t × Party_t)  
+ random noise

With the default settings in the dashboard:

Inflation_(t+1) = 2.1  
+ 0.22 × Deficit_t  
+ 0.55 × OilShock_t  
- 0.65 × Recession_t  
+ 0.12 × (Deficit_t × Party_t)  
+ random noise

### Interpretation
The simulation assumes that larger deficits are associated with higher next-year inflation, oil shocks raise inflation, recessions reduce inflationary pressure, and the deficit effect is stronger under Republican presidents.

### Purpose
These equations are used to visualize the logic of the research design. The dashboard is a simulation tool, not a final real-world statistical test.

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
