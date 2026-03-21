import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="POSC 301 Deficits, Inflation, and Party",
    page_icon="📈",
    layout="wide"
)

# -----------------------------
# HELPERS
# -----------------------------
def build_party_series(years):
    party_map = {}
    for year in years:
        if year == 1980:
            party_map[year] = "Democrat"      # Carter
        elif 1981 <= year <= 1992:
            party_map[year] = "Republican"    # Reagan / Bush Sr.
        elif 1993 <= year <= 2000:
            party_map[year] = "Democrat"      # Clinton
        elif 2001 <= year <= 2008:
            party_map[year] = "Republican"    # Bush Jr.
        elif 2009 <= year <= 2016:
            party_map[year] = "Democrat"      # Obama
        elif 2017 <= year <= 2020:
            party_map[year] = "Republican"    # Trump
        elif 2021 <= year <= 2025:
            party_map[year] = "Democrat"      # Biden
    return np.array([party_map[y] for y in years])

def build_recession_series(years):
    recession_years = {1980, 1981, 1982, 1990, 1991, 2001, 2008, 2009, 2020}
    return np.array([1 if y in recession_years else 0 for y in years])

def simulate_data(
    start_year,
    end_year,
    seed,
    base_inflation,
    deficit_effect,
    republican_boost,
    oil_effect,
    recession_effect
):
    np.random.seed(seed)

    years = np.arange(start_year, end_year + 1)
    party = build_party_series(years)
    recession = build_recession_series(years)

    party_num = np.where(party == "Republican", 1, 0)

    # Deficit as % of GDP
    deficit = (
        3.0
        + 1.0 * recession
        + 0.7 * np.sin(np.linspace(0, 5 * np.pi, len(years)))
        + np.random.normal(0, 0.55, len(years))
    )

    for i, y in enumerate(years):
        if y in [1983, 1984, 1985, 2009, 2010, 2020, 2021]:
            deficit[i] += np.random.uniform(2.0, 3.8)

    deficit = np.clip(deficit, 0.4, None)

    # Oil shocks
    oil_shock = np.random.normal(0, 0.35, len(years))
    oil_spikes = {
        1980: 2.2,
        1981: 1.6,
        1990: 1.5,
        2008: 2.0,
        2011: 1.0,
        2022: 2.4
    }

    for i, y in enumerate(years):
        if y in oil_spikes:
            oil_shock[i] += oil_spikes[y]

    # Simulated next-year inflation
    noise = np.random.normal(0, 0.45, len(years))
    inflation_next_year = (
        base_inflation
        + deficit_effect * deficit
        + oil_effect * oil_shock
        + recession_effect * recession
        + republican_boost * deficit * party_num
        + noise
    )

    inflation_next_year = np.clip(inflation_next_year, -2.0, None)

    df = pd.DataFrame({
        "Year": years,
        "DeficitPctGDP": np.round(deficit, 2),
        "OilShock": np.round(oil_shock, 2),
        "Recession": recession,
        "Party": party,
        "InflationNextYear": np.round(inflation_next_year, 2)
    })

    df["RecessionLabel"] = np.where(df["Recession"] == 1, "Recession", "No Recession")
    return df

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("Simulation Controls")

start_year, end_year = st.sidebar.slider(
    "Year range",
    min_value=1980,
    max_value=2025,
    value=(1980, 2025)
)

seed = st.sidebar.number_input("Random seed", min_value=1, max_value=9999, value=42)

base_inflation = st.sidebar.slider("Base inflation", 0.0, 5.0, 2.1, 0.1)
deficit_effect = st.sidebar.slider("Deficit effect", 0.00, 1.00, 0.22, 0.01)
republican_boost = st.sidebar.slider("Republican deficit boost", 0.00, 0.50, 0.12, 0.01)
oil_effect = st.sidebar.slider("Oil shock effect", 0.00, 1.50, 0.55, 0.01)
recession_effect = st.sidebar.slider("Recession effect", -2.00, 1.00, -0.65, 0.01)

df = simulate_data(
    start_year=start_year,
    end_year=end_year,
    seed=seed,
    base_inflation=base_inflation,
    deficit_effect=deficit_effect,
    republican_boost=republican_boost,
    oil_effect=oil_effect,
    recession_effect=recession_effect
)

# -----------------------------
# HEADER
# -----------------------------
st.title("Deficits, Inflation, and Party")
st.subheader("Interactive Simulation for POSC 301")
st.write(
    "This dashboard simulates whether larger federal deficits are associated with "
    "higher next-year inflation, and whether that effect is stronger under Republican presidents."
)

# -----------------------------
# METRICS
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Years Shown", len(df))
col2.metric("Avg Deficit % GDP", f"{df['DeficitPctGDP'].mean():.2f}")
col3.metric("Avg Next-Year Inflation", f"{df['InflationNextYear'].mean():.2f}%")
col4.metric("Recession Years", int(df["Recession"].sum()))

st.divider()

# -----------------------------
# MAIN CHART: TIME SERIES
# -----------------------------
fig_time = go.Figure()

fig_time.add_trace(go.Scatter(
    x=df["Year"],
    y=df["InflationNextYear"],
    mode="lines+markers",
    name="Next-Year Inflation"
))

fig_time.add_trace(go.Scatter(
    x=df["Year"],
    y=df["DeficitPctGDP"],
    mode="lines+markers",
    name="Deficit % GDP",
    yaxis="y2"
))

for _, row in df[df["Recession"] == 1].iterrows():
    fig_time.add_vrect(
        x0=row["Year"] - 0.5,
        x1=row["Year"] + 0.5,
        opacity=0.12,
        line_width=0
    )

fig_time.update_layout(
    title="Simulated Deficits and Next-Year Inflation Over Time",
    xaxis_title="Year",
    yaxis=dict(title="Inflation (%)"),
    yaxis2=dict(
        title="Deficit (% GDP)",
        overlaying="y",
        side="right"
    ),
    height=550,
    hovermode="x unified"
)

st.plotly_chart(fig_time, use_container_width=True)

# -----------------------------
# SCATTER CHART
# -----------------------------
fig_scatter = px.scatter(
    df,
    x="DeficitPctGDP",
    y="InflationNextYear",
    color="Party",
    symbol="RecessionLabel",
    hover_data=["Year", "OilShock"],
    title="Deficit % GDP vs. Next-Year Inflation"
)

z = np.polyfit(df["DeficitPctGDP"], df["InflationNextYear"], 1)
p = np.poly1d(z)
x_line = np.linspace(df["DeficitPctGDP"].min(), df["DeficitPctGDP"].max(), 200)

fig_scatter.add_trace(go.Scatter(
    x=x_line,
    y=p(x_line),
    mode="lines",
    name="Trend Line"
))

fig_scatter.update_layout(height=500)

st.plotly_chart(fig_scatter, use_container_width=True)

# -----------------------------
# PARTY COMPARISON
# -----------------------------
party_summary = (
    df.groupby("Party")[["DeficitPctGDP", "InflationNextYear", "OilShock"]]
    .mean()
    .round(2)
    .reset_index()
)

fig_party = px.bar(
    party_summary,
    x="Party",
    y=["DeficitPctGDP", "InflationNextYear", "OilShock"],
    barmode="group",
    title="Average Simulated Values by Presidential Party"
)

fig_party.update_layout(height=500)
st.plotly_chart(fig_party, use_container_width=True)

# -----------------------------
# DATA TABLE
# -----------------------------
st.subheader("Full Simulated Dataset")
st.dataframe(df, use_container_width=True, height=500)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv,
    file_name="posc301_simulated_deficits_inflation.csv",
    mime="text/csv"
)

# -----------------------------
# METHODS BOX
# -----------------------------
st.subheader("How to Talk About This in Your Paper")
st.info(
    "This is a simulation, not the final real-data analysis. "
    "Each year is one observation. The model assumes that next-year inflation is affected by "
    "the federal deficit, oil shocks, recession conditions, and presidential party, with a stronger "
    "deficit effect under Republican presidents."
)