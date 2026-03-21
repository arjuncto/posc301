import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


#1983 has a deficit of 8.26% of GDP
#it is a Republican year
#no recession
#predicted next-year inflation = 4.93






# -----------------------------
# 1. SETUP
# -----------------------------
np.random.seed(42)

years = np.arange(1980, 2026)

# Presidential party by year
# 0 = Democrat, 1 = Republican
party_map = {}
for year in years:
    if 1980 <= year <= 1980:
        party_map[year] = 0   # Carter
    elif 1981 <= year <= 1992:
        party_map[year] = 1   # Reagan/Bush Sr.
    elif 1993 <= year <= 2000:
        party_map[year] = 0   # Clinton
    elif 2001 <= year <= 2008:
        party_map[year] = 1   # Bush Jr.
    elif 2009 <= year <= 2016:
        party_map[year] = 0   # Obama
    elif 2017 <= year <= 2020:
        party_map[year] = 1   # Trump
    elif 2021 <= year <= 2025:
        party_map[year] = 0   # Biden
party = np.array([party_map[y] for y in years])

# Recession indicator by year
# 1 = recession year, 0 = not recession year
recession_years = {1980, 1981, 1982, 1990, 1991, 2001, 2008, 2009, 2020}
recession = np.array([1 if y in recession_years else 0 for y in years])

# -----------------------------
# 2. SIMULATE VARIABLES
# -----------------------------

# Deficit as % of GDP
# Base pattern + recession spikes + random noise
deficit = (
    3.0
    + 1.2 * recession
    + 0.8 * np.sin(np.linspace(0, 5 * np.pi, len(years)))
    + np.random.normal(0, 0.6, len(years))
)

# Make a few known high-deficit periods stand out more
for i, y in enumerate(years):
    if y in [1983, 1984, 1985, 2009, 2010, 2020, 2021]:
        deficit[i] += np.random.uniform(2.0, 4.0)

deficit = np.clip(deficit, 0.5, None)

# Oil shock variable (annual shock intensity)
oil_shock = np.random.normal(0, 0.4, len(years))

# Add major oil shock years
oil_shock_spikes = {
    1980: 2.2,
    1981: 1.5,
    1990: 1.4,
    2008: 2.0,
    2011: 1.0,
    2022: 2.3
}
for i, y in enumerate(years):
    if y in oil_shock_spikes:
        oil_shock[i] += oil_shock_spikes[y]

# -----------------------------
# 3. GENERATE NEXT-YEAR INFLATION
# -----------------------------
# Your theory:
# - higher deficits -> higher next-year inflation
# - stronger deficit effect under Republican presidents
# - oil shocks raise inflation
# - recessions reduce inflation pressure

base_inflation = 2.1
noise = np.random.normal(0, 0.5, len(years))

inflation_next_year = (
    base_inflation
    + 0.22 * deficit
    + 0.55 * oil_shock
    - 0.65 * recession
    + 0.12 * deficit * party   # stronger deficit effect under Republicans
    + noise
)

inflation_next_year = np.clip(inflation_next_year, -1.5, None)

# -----------------------------
# 4. BUILD DATAFRAME
# -----------------------------
df = pd.DataFrame({
    "Year": years,
    "DeficitPctGDP": np.round(deficit, 2),
    "OilShock": np.round(oil_shock, 2),
    "Recession": recession,
    "Party": np.where(party == 1, "Republican", "Democrat"),
    "InflationNextYear": np.round(inflation_next_year, 2)
})

print(df.head(10))
print("\nSummary:")
print(df.describe(numeric_only=True))

# -----------------------------
# 5. PRETTY GRAPH
# -----------------------------
fig, ax = plt.subplots(figsize=(13, 7))

ax.plot(
    df["Year"],
    df["InflationNextYear"],
    linewidth=2.5,
    label="Predicted Next-Year Inflation"
)

# Shade recession years
for i in range(len(df)):
    if df.loc[i, "Recession"] == 1:
        ax.axvspan(df.loc[i, "Year"] - 0.5, df.loc[i, "Year"] + 0.5, alpha=0.12)

# Mark party changes in background labels
for i in range(len(df)):
    if df.loc[i, "Party"] == "Republican":
        ax.text(
            df.loc[i, "Year"],
            ax.get_ylim()[1] - 0.2,
            "R",
            fontsize=8,
            ha="center",
            va="top",
            alpha=0.45
        )
    else:
        ax.text(
            df.loc[i, "Year"],
            ax.get_ylim()[1] - 0.2,
            "D",
            fontsize=8,
            ha="center",
            va="top",
            alpha=0.45
        )

ax.set_title("Simulated Next-Year Inflation in the United States, 1980–2025", fontsize=16, pad=15)
ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("Predicted Inflation (%)", fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend(frameon=False)
plt.tight_layout()
plt.show()

# -----------------------------
# 6. OPTIONAL SECOND GRAPH
# -----------------------------
fig, ax = plt.subplots(figsize=(13, 7))

ax.scatter(
    df["DeficitPctGDP"],
    df["InflationNextYear"],
    alpha=0.8
)

# Add simple trend line
z = np.polyfit(df["DeficitPctGDP"], df["InflationNextYear"], 1)
p = np.poly1d(z)
x_line = np.linspace(df["DeficitPctGDP"].min(), df["DeficitPctGDP"].max(), 100)

ax.plot(x_line, p(x_line), linewidth=2)

ax.set_title("Simulated Relationship Between Deficits and Next-Year Inflation", fontsize=16, pad=15)
ax.set_xlabel("Federal Deficit (% of GDP)", fontsize=12)
ax.set_ylabel("Predicted Next-Year Inflation (%)", fontsize=12)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()