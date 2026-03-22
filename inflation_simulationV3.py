import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Deficits, Inflation, and Party",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DEFAULT_THEME = "Dark"

ADMINS = [
    {"name": "Carter", "start": 1980, "end": 1980, "party": "Democrat", "color": "#0D47A1", "fill": "rgba(13,71,161,0.18)"},
    {"name": "Reagan", "start": 1981, "end": 1988, "party": "Republican", "color": "#B71C1C", "fill": "rgba(183,28,28,0.16)"},
    {"name": "Bush 41", "start": 1989, "end": 1992, "party": "Republican", "color": "#EF9A9A", "fill": "rgba(239,154,154,0.18)"},
    {"name": "Clinton", "start": 1993, "end": 2000, "party": "Democrat", "color": "#90CAF9", "fill": "rgba(144,202,249,0.16)"},
    {"name": "Bush 43", "start": 2001, "end": 2008, "party": "Republican", "color": "#EF9A9A", "fill": "rgba(239,154,154,0.18)"},
    {"name": "Obama", "start": 2009, "end": 2016, "party": "Democrat", "color": "#0D47A1", "fill": "rgba(13,71,161,0.16)"},
    {"name": "Trump", "start": 2017, "end": 2020, "party": "Republican", "color": "#B71C1C", "fill": "rgba(183,28,28,0.16)"},
    {"name": "Biden", "start": 2021, "end": 2025, "party": "Democrat", "color": "#90CAF9", "fill": "rgba(144,202,249,0.18)"},
]

RECESSION_YEARS = {1980, 1981, 1982, 1990, 1991, 2001, 2008, 2009, 2020}

OIL_SPIKES = {
    1980: 2.2,
    1981: 1.4,
    1990: 1.5,
    2008: 2.1,
    2011: 0.9,
    2022: 2.4,
}

REFERENCES = [
    {
        "citation": "Federal Reserve Bank of St. Louis. (n.d.). Federal Surplus or Deficit [-] as Percent of Gross Domestic Product (FYFSGDA188S). FRED.",
        "url": "https://fred.stlouisfed.org/series/FYFSGDA188S",
    },
    {
        "citation": "U.S. Bureau of Labor Statistics. (n.d.). Consumer Price Index historical tables for U.S. city average.",
        "url": "https://www.bls.gov/regions/mid-atlantic/data/consumerpriceindexhistorical_us_table.htm",
    },
    {
        "citation": "Miller Center. (n.d.). U.S. Presidents. University of Virginia.",
        "url": "https://millercenter.org/president",
    },
    {
        "citation": "National Bureau of Economic Research. (n.d.). U.S. business cycle expansions and contractions.",
        "url": "https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions",
    },
    {
        "citation": "Federal Reserve Bank of St. Louis. (n.d.). Crude Oil Prices: West Texas Intermediate (WTI) - Cushing, Oklahoma (MCOILWTICO). FRED.",
        "url": "https://fred.stlouisfed.org/series/MCOILWTICO",
    },
    {
        "citation": "Krause, G. A. (2000). Partisan and ideological sources of fiscal deficits in the United States. American Journal of Political Science, 44(3), 541–559.",
        "url": "https://www.jstor.org/stable/2669263",
    },
]


def administration_for_year(year: int) -> dict:
    for admin in ADMINS:
        if admin["start"] <= year <= admin["end"]:
            return admin
    return ADMINS[-1]


def build_dataframe(
    start_year: int,
    end_year: int,
    seed: int,
    base_inflation: float,
    deficit_effect: float,
    republican_boost: float,
    oil_effect: float,
    recession_effect: float,
    noise_scale: float,
):
    np.random.seed(seed)
    years = np.arange(start_year, end_year + 1)

    administrations = [administration_for_year(year) for year in years]
    admin_names = np.array([item["name"] for item in administrations])
    parties = np.array([item["party"] for item in administrations])
    party_num = np.where(parties == "Republican", 1, 0)

    recession = np.array([1 if year in RECESSION_YEARS else 0 for year in years])

    deficit = (
        3.0
        + 1.0 * recession
        + 0.65 * np.sin(np.linspace(0, 5 * np.pi, len(years)))
        + np.random.normal(0, 0.50, len(years))
    )

    for i, year in enumerate(years):
        if year in {1983, 1984, 1985, 2009, 2010, 2020, 2021}:
            deficit[i] += np.random.uniform(2.0, 3.7)

    deficit = np.clip(deficit, 0.3, None)

    oil_shock = np.random.normal(0, 0.32, len(years))
    for i, year in enumerate(years):
        if year in OIL_SPIKES:
            oil_shock[i] += OIL_SPIKES[year]

    noise = np.random.normal(0, noise_scale, len(years))
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
        "Administration": admin_names,
        "Party": parties,
        "DeficitPctGDP": np.round(deficit, 2),
        "OilShock": np.round(oil_shock, 2),
        "Recession": recession,
        "InflationNextYear": np.round(inflation_next_year, 2),
    })
    df["RecessionLabel"] = np.where(df["Recession"] == 1, "Recession Year", "No Recession")
    df["AdminColor"] = df["Administration"].map({item["name"]: item["color"] for item in ADMINS})
    df["AdminFill"] = df["Administration"].map({item["name"]: item["fill"] for item in ADMINS})
    return df


def inject_css(theme_mode: str):
    dark = theme_mode == "Dark"
    if dark:
        bg = "#0b1220"
        panel = "#121a2b"
        panel2 = "#0f172a"
        text = "#e5eefb"
        muted = "#9bb0d1"
        border = "rgba(148,163,184,0.20)"
        accent = "#60a5fa"
        shadow = "0 18px 50px rgba(0,0,0,0.35)"
        metric_bg = "linear-gradient(135deg, rgba(30,41,59,0.95), rgba(15,23,42,0.95))"
        sticky_bg = "rgba(15,23,42,0.78)"
    else:
        bg = "#f3f7fc"
        panel = "#ffffff"
        panel2 = "#eef4ff"
        text = "#0f172a"
        muted = "#51607a"
        border = "rgba(15,23,42,0.08)"
        accent = "#1d4ed8"
        shadow = "0 18px 40px rgba(15,23,42,0.08)"
        metric_bg = "linear-gradient(135deg, rgba(255,255,255,0.98), rgba(239,246,255,0.98))"
        sticky_bg = "rgba(255,255,255,0.78)"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(59,130,246,0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(239,68,68,0.10), transparent 22%),
                {bg};
            color: {text};
        }}

        .block-container {{
            padding-top: 1.1rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }}

        div[data-testid="stHorizontalBlock"]:first-of-type {{
            position: sticky;
            top: 0.6rem;
            z-index: 1000;
            padding: 0.45rem 0.5rem;
            margin-bottom: 0.8rem;
            background: {sticky_bg};
            backdrop-filter: blur(12px);
            border: 1px solid {border};
            border-radius: 18px;
            box-shadow: {shadow};
        }}

        .hero-card {{
            padding: 1rem 1.15rem 0.2rem 1.15rem;
            border-radius: 24px;
            background: linear-gradient(145deg, {panel}, {panel2});
            border: 1px solid {border};
            box-shadow: {shadow};
            margin-bottom: 0.8rem;
        }}

        .hero-title {{
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1.05;
            margin-bottom: 0.35rem;
            color: {text};
            letter-spacing: -0.02em;
        }}

        .hero-sub {{
            font-size: 1.02rem;
            line-height: 1.65;
            color: {muted};
            margin-bottom: 0.5rem;
            max-width: 980px;
        }}

        div[data-testid="stMetric"] {{
            background: {metric_bg};
            border: 1px solid {border};
            border-radius: 22px;
            padding: 0.5rem 0.85rem;
            box-shadow: {shadow};
        }}

        div[data-testid="stMetricLabel"] {{
            color: {muted};
            font-weight: 700;
        }}

        div[data-testid="stMetricValue"] {{
            color: {text};
            font-weight: 800;
        }}

        .stDataFrame, .stPlotlyChart {{
            border-radius: 24px;
            overflow: hidden;
            border: 1px solid {border};
            box-shadow: {shadow};
            background: {panel};
        }}

        .section-title {{
            font-size: 1.25rem;
            font-weight: 800;
            margin: 1rem 0 0.6rem 0;
            color: {text};
            letter-spacing: -0.01em;
        }}

        .tiny-note {{
            color: {muted};
            font-size: 0.92rem;
            margin-top: 0.2rem;
        }}

        .reference-card {{
            background: linear-gradient(145deg, {panel}, {panel2});
            border: 1px solid {border};
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.7rem;
            box-shadow: {shadow};
        }}

        .reference-card a {{
            color: {accent} !important;
            font-weight: 700;
            text-decoration: none;
        }}

        .reference-card a:hover {{
            text-decoration: underline;
        }}

        .stButton > button, div[data-testid="stPopover"] button {{
            border-radius: 999px !important;
            border: 1px solid {border} !important;
            background: linear-gradient(135deg, rgba(29,78,216,0.95), rgba(59,130,246,0.88)) !important;
            color: white !important;
            font-weight: 800 !important;
            box-shadow: {shadow} !important;
            padding: 0.7rem 1.15rem !important;
        }}

        div[data-testid="stPopover"] {{
            width: 100%;
        }}

        div[data-testid="stPopover"] button {{
            width: 100% !important;
            min-height: 3rem !important;
            font-size: 1rem !important;
        }}

        .stSelectbox > div > div, .stNumberInput > div > div > input {{
            border-radius: 14px !important;
        }}

        .stSlider {{
            padding-top: 0.2rem;
            padding-bottom: 0.35rem;
        }}

        hr {{
            border-color: {border};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def admin_color_map():
    return {item["name"]: item["color"] for item in ADMINS}


if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = DEFAULT_THEME

toolbar_left, toolbar_mid, toolbar_right = st.columns([2.3, 6.2, 1.8])

with toolbar_left:
    control_host = st.popover("⚙️ Simulation Controls", use_container_width=True) if hasattr(st, "popover") else st.expander("⚙️ Simulation Controls", expanded=False)

with toolbar_right:
    selected_theme = st.selectbox(
        "Theme",
        options=["Dark", "Light"],
        index=0 if st.session_state.theme_mode == "Dark" else 1,
        label_visibility="collapsed",
        key="theme_picker",
    )
    st.session_state.theme_mode = selected_theme

inject_css(st.session_state.theme_mode)

plotly_template = "plotly_dark" if st.session_state.theme_mode == "Dark" else "plotly_white"

with control_host:
    st.markdown("#### Window")
    year_range = st.slider("Year range", 1980, 2025, (1980, 2025))
    seed = st.number_input("Random seed", min_value=1, max_value=9999, value=42, step=1)

    model_tab, shock_tab, structure_tab = st.tabs(["Model", "Shocks", "Structure"])

    with model_tab:
        base_inflation = st.slider("Base inflation", 0.0, 5.0, 2.1, 0.1)
        deficit_effect = st.slider("Deficit effect", 0.00, 1.00, 0.22, 0.01)
        republican_boost = st.slider("Republican deficit boost", 0.00, 0.50, 0.12, 0.01)

    with shock_tab:
        oil_effect = st.slider("Oil shock effect", 0.00, 1.50, 0.55, 0.01)
        recession_effect = st.slider("Recession effect", -2.00, 1.00, -0.65, 0.01)
        noise_scale = st.slider("Random variation", 0.00, 1.20, 0.45, 0.01)

    with structure_tab:
        st.markdown(
            """
            - **Years** = one observation per year  
            - **DeficitPctGDP** = simulated federal deficit as a share of GDP  
            - **InflationNextYear** = simulated following-year inflation  
            - **Party** = administration in office that year  
            - **Recession** and **OilShock** = control factors
            """
        )

df = build_dataframe(
    start_year=year_range[0],
    end_year=year_range[1],
    seed=seed,
    base_inflation=base_inflation,
    deficit_effect=deficit_effect,
    republican_boost=republican_boost,
    oil_effect=oil_effect,
    recession_effect=recession_effect,
    noise_scale=noise_scale,
)

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">Deficits, Inflation, and Party</div>
        <div class="hero-sub">
            This dashboard simulates whether larger federal deficits are associated with higher next-year inflation,
            and whether that effect is stronger under Republican presidents.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("Years Shown", f"{len(df)}")
metric2.metric("Avg Deficit % GDP", f"{df['DeficitPctGDP'].mean():.2f}")
metric3.metric("Avg Next-Year Inflation", f"{df['InflationNextYear'].mean():.2f}%")
metric4.metric("Recession Years", f"{int(df['Recession'].sum())}")

fig_time = go.Figure()
for admin in ADMINS:
    if admin["end"] < year_range[0] or admin["start"] > year_range[1]:
        continue
    x0 = max(admin["start"], year_range[0]) - 0.5
    x1 = min(admin["end"], year_range[1]) + 0.5
    fig_time.add_vrect(
        x0=x0,
        x1=x1,
        fillcolor=admin["fill"],
        opacity=1.0,
        line_width=0,
        layer="below",
        annotation_text=admin["name"],
        annotation_position="top left",
    )

fig_time.add_trace(
    go.Scatter(
        x=df["Year"],
        y=df["InflationNextYear"],
        mode="lines+markers",
        name="Next-Year Inflation",
        line=dict(color="#f59e0b", width=3),
        marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>Inflation (next year): %{y:.2f}%<extra></extra>",
    )
)

fig_time.add_trace(
    go.Scatter(
        x=df["Year"],
        y=df["DeficitPctGDP"],
        mode="lines+markers",
        name="Deficit % GDP",
        yaxis="y2",
        line=dict(color="#34d399", width=3),
        marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>Deficit: %{y:.2f}% of GDP<extra></extra>",
    )
)

for _, row in df[df["Recession"] == 1].iterrows():
    fig_time.add_vline(x=row["Year"], line_width=1, line_dash="dot", line_color="rgba(148,163,184,0.7)")

fig_time.update_layout(
    template=plotly_template,
    title="Simulated Deficits and Next-Year Inflation Over Time",
    height=560,
    hovermode="x unified",
    margin=dict(l=20, r=20, t=70, b=20),
    xaxis_title="Year",
    yaxis=dict(title="Inflation (%)"),
    yaxis2=dict(title="Deficit (% GDP)", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

st.plotly_chart(fig_time, use_container_width=True)

fig_scatter = px.scatter(
    df,
    x="DeficitPctGDP",
    y="InflationNextYear",
    color="Administration",
    color_discrete_map=admin_color_map(),
    symbol="RecessionLabel",
    hover_data=["Year", "Party", "OilShock"],
    title="Deficit % GDP vs. Next-Year Inflation",
    template=plotly_template,
)

z = np.polyfit(df["DeficitPctGDP"], df["InflationNextYear"], 1)
p = np.poly1d(z)
x_line = np.linspace(df["DeficitPctGDP"].min(), df["DeficitPctGDP"].max(), 200)
fig_scatter.add_trace(
    go.Scatter(
        x=x_line,
        y=p(x_line),
        mode="lines",
        name="Trend Line",
        line=dict(color="#f59e0b", width=3, dash="dash"),
    )
)
fig_scatter.update_layout(height=520, margin=dict(l=20, r=20, t=70, b=20))
st.plotly_chart(fig_scatter, use_container_width=True)

admin_summary = (
    df.groupby(["Administration", "Party"], as_index=False)[["DeficitPctGDP", "InflationNextYear"]]
    .mean()
    .round(2)
)

fig_admin = go.Figure()
fig_admin.add_trace(
    go.Bar(
        x=admin_summary["Administration"],
        y=admin_summary["DeficitPctGDP"],
        name="Avg Deficit % GDP",
        marker_color=[admin_color_map()[admin] for admin in admin_summary["Administration"]],
        opacity=0.95,
    )
)
fig_admin.add_trace(
    go.Bar(
        x=admin_summary["Administration"],
        y=admin_summary["InflationNextYear"],
        name="Avg Next-Year Inflation",
        marker_color="#f59e0b",
        opacity=0.85,
    )
)
fig_admin.update_layout(
    template=plotly_template,
    title="Average Simulated Values by Administration",
    barmode="group",
    height=500,
    margin=dict(l=20, r=20, t=70, b=20),
    xaxis_title="Administration",
    yaxis_title="Value",
)

st.plotly_chart(fig_admin, use_container_width=True)

st.markdown('<div class="section-title">Simulated Dataset</div>', unsafe_allow_html=True)
st.dataframe(df, use_container_width=True, height=560)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv,
    file_name="inflation_simulation_v3.csv",
    mime="text/csv",
    use_container_width=False,
)

st.markdown('<div class="section-title">References</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="tiny-note">Historical data pages and political science literature used to inform the variables, coding, and framing of the simulation.</div>',
    unsafe_allow_html=True,
)
for ref in REFERENCES:
    st.markdown(
        f"""
        <div class="reference-card">
            <div>{ref["citation"]}</div>
            <div style="margin-top:0.45rem;"><a href="{ref["url"]}" target="_blank">Open source</a></div>
        </div>
        """,
        unsafe_allow_html=True,
    )