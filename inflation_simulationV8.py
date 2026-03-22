import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Deficits, Inflation, and Party",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULTS = {
    "year_range": (1980, 2025),
    "seed": 42,
    "base_inflation": 2.1,
    "deficit_effect": 0.22,
    "republican_boost": 0.12,
    "oil_effect": 0.55,
    "recession_effect": -0.65,
    "noise_scale": 0.45,
}

ADMINS = [
    {"name": "Carter",  "start": 1980, "end": 1980, "party": "Democrat",   "line": "#2563EB", "fill": "rgba(37,99,235,0.09)"},
    {"name": "Reagan",  "start": 1981, "end": 1988, "party": "Republican", "line": "#DC2626", "fill": "rgba(220,38,38,0.09)"},
    {"name": "Bush 41", "start": 1989, "end": 1992, "party": "Republican", "line": "#FCA5A5", "fill": "rgba(252,165,165,0.07)"},
    {"name": "Clinton", "start": 1993, "end": 2000, "party": "Democrat",   "line": "#93C5FD", "fill": "rgba(147,197,253,0.07)"},
    {"name": "Bush 43", "start": 2001, "end": 2008, "party": "Republican", "line": "#FCA5A5", "fill": "rgba(252,165,165,0.07)"},
    {"name": "Obama",   "start": 2009, "end": 2016, "party": "Democrat",   "line": "#2563EB", "fill": "rgba(37,99,235,0.09)"},
    {"name": "Trump",   "start": 2017, "end": 2020, "party": "Republican", "line": "#DC2626", "fill": "rgba(220,38,38,0.09)"},
    {"name": "Biden",   "start": 2021, "end": 2025, "party": "Democrat",   "line": "#93C5FD", "fill": "rgba(147,197,253,0.07)"},
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
        "citation": "Miller Center. (n.d.). Presidents. University of Virginia.",
        "url": "https://millercenter.org/president",
    },
    {
        "citation": "National Bureau of Economic Research. (n.d.). U.S. business cycle expansions and contractions.",
        "url": "https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions",
    },
    {
        "citation": "Federal Reserve Bank of St. Louis. (n.d.). Crude Oil Prices: West Texas Intermediate (WTI) – Cushing, Oklahoma (MCOILWTICO). FRED.",
        "url": "https://fred.stlouisfed.org/series/MCOILWTICO",
    },
    {
        "citation": "Krause, G. A. (2000). Partisan and ideological sources of fiscal deficits in the United States. American Journal of Political Science, 44(3), 541–559.",
        "url": "https://www.jstor.org/stable/2669263",
    },
]


def inject_css():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37,99,235,0.04), transparent 18%),
                radial-gradient(circle at top right, rgba(96,165,250,0.03), transparent 14%),
                linear-gradient(180deg, #01040A 0%, #020712 100%);
            color: #E8EEF9;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 1.35rem !important;
            padding-bottom: 2rem !important;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #040914 0%, #07101F 100%);
            border-right: 1px solid rgba(115,145,190,0.14);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1rem;
        }

        .sidebar-shell {
            padding: 0.15rem 0 0.5rem 0;
        }

        .sidebar-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 0.9rem 1rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #123A91 0%, #1D4ED8 55%, #60A5FA 100%);
            color: white;
            font-weight: 900;
            font-size: 1.05rem;
            letter-spacing: -0.01em;
            box-shadow: 0 14px 30px rgba(29,78,216,0.22);
            margin-bottom: 0.8rem;
        }

        .sidebar-sub {
            color: #A7B7D4;
            font-size: 0.93rem;
            line-height: 1.45;
            margin-bottom: 1rem;
        }

        .sidebar-section {
            margin-top: 0.9rem;
            margin-bottom: 0.5rem;
        }

        .sidebar-section-title {
            color: #E8EEF9;
            font-size: 0.92rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .sidebar-section-note {
            color: #8EA2C7;
            font-size: 0.84rem;
            margin-bottom: 0.45rem;
        }

        .sidebar-divider {
            height: 1px;
            background: rgba(115,145,190,0.12);
            margin: 0.95rem 0 0.2rem 0;
            border-radius: 999px;
        }

        .hero-card {
            padding: 1.2rem 1.25rem 0.7rem 1.25rem;
            border-radius: 26px;
            background: linear-gradient(145deg, #050B16, #081121);
            border: 1px solid rgba(115,145,190,0.14);
            box-shadow: 0 18px 44px rgba(0,0,0,0.30);
            margin-bottom: 0.9rem;
        }

        .hero-title {
            font-size: 2.3rem;
            font-weight: 900;
            letter-spacing: -0.03em;
            line-height: 1.02;
            color: #E8EEF9;
            margin-bottom: 0.45rem;
        }

        .hero-sub {
            font-size: 1.03rem;
            line-height: 1.62;
            color: #9CB0D1;
            max-width: 1020px;
            margin-bottom: 0.1rem;
        }

        .mini-legend {
            display: flex;
            gap: 0.85rem;
            flex-wrap: wrap;
            align-items: center;
            margin-top: 0.55rem;
        }

        .mini-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            color: #B8C6DF;
            font-size: 0.88rem;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(115,145,190,0.10);
        }

        .mini-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #050B16, #081121);
            border: 1px solid rgba(115,145,190,0.14);
            border-radius: 22px;
            padding: 0.55rem 0.95rem;
            box-shadow: 0 18px 44px rgba(0,0,0,0.30);
        }

        div[data-testid="stMetricLabel"] {
            color: #9CB0D1;
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: #E8EEF9;
            font-weight: 900;
        }

        .stPlotlyChart, .stDataFrame {
            border-radius: 24px;
            overflow: hidden;
            border: 1px solid rgba(115,145,190,0.14);
            box-shadow: 0 18px 44px rgba(0,0,0,0.30);
            background: #050B16;
        }

        .section-title {
            font-size: 1.18rem;
            font-weight: 850;
            color: #E8EEF9;
            margin: 1rem 0 0.6rem 0;
        }

        .section-note {
            color: #9CB0D1;
            font-size: 0.92rem;
            margin-bottom: 0.7rem;
        }

        .reference-card {
            padding: 1rem 1rem;
            border-radius: 18px;
            background: linear-gradient(145deg, #050B16, #081121);
            border: 1px solid rgba(115,145,190,0.14);
            box-shadow: 0 18px 44px rgba(0,0,0,0.30);
            margin-bottom: 0.7rem;
        }

        .reference-card a {
            color: #60A5FA !important;
            font-weight: 800;
            text-decoration: none;
        }

        .reference-card a:hover {
            text-decoration: underline;
        }

        .stDownloadButton button {
            border-radius: 999px !important;
            padding: 0.72rem 1.05rem !important;
            border: 1px solid rgba(115,145,190,0.14) !important;
            background: linear-gradient(135deg, #081121, #050B16) !important;
            color: #E8EEF9 !important;
            font-weight: 800 !important;
        }

        .stSlider label, .stNumberInput label {
            color: #E8EEF9 !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def administration_for_year(year):
    for admin in ADMINS:
        if admin["start"] <= year <= admin["end"]:
            return admin
    return ADMINS[-1]


def build_dataframe(
    start_year,
    end_year,
    seed,
    base_inflation,
    deficit_effect,
    republican_boost,
    oil_effect,
    recession_effect,
    noise_scale,
):
    np.random.seed(seed)
    years = np.arange(start_year, end_year + 1)

    admins = [administration_for_year(y) for y in years]
    administrations = np.array([a["name"] for a in admins])
    parties = np.array([a["party"] for a in admins])
    party_num = np.where(parties == "Republican", 1, 0)

    recession = np.array([1 if y in RECESSION_YEARS else 0 for y in years])

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

    return pd.DataFrame({
        "Year": years,
        "Administration": administrations,
        "Party": parties,
        "DeficitPctGDP": np.round(deficit, 2),
        "OilShock": np.round(oil_shock, 2),
        "Recession": recession,
        "InflationNextYear": np.round(inflation_next_year, 2),
    })


def base_layout(title):
    return dict(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#040A14",
        font=dict(color="#E8EEF9"),
        margin=dict(l=20, r=20, t=78, b=20),
        xaxis=dict(showgrid=True, gridcolor="rgba(115,145,190,0.10)", zeroline=False, color="#E8EEF9"),
        yaxis=dict(showgrid=True, gridcolor="rgba(115,145,190,0.10)", zeroline=False, color="#E8EEF9"),
        hovermode="closest",
    )


inject_css()

with st.sidebar:
    st.markdown('<div class="sidebar-shell">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-badge">Simulation Controls</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-sub">Adjust the assumptions and watch the charts and dataset update instantly.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section"><div class="sidebar-section-title">Years</div><div class="sidebar-section-note">Choose the time window and random seed.</div></div>', unsafe_allow_html=True)
    year_range = st.slider("Year range", 1980, 2025, DEFAULTS["year_range"])
    seed = st.number_input("Random seed", min_value=1, max_value=9999, value=DEFAULTS["seed"], step=1)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section"><div class="sidebar-section-title">Model</div><div class="sidebar-section-note">Main relationship between deficits and inflation.</div></div>', unsafe_allow_html=True)
    base_inflation = st.slider("Base inflation", 0.0, 5.0, DEFAULTS["base_inflation"], 0.1)
    deficit_effect = st.slider("Deficit effect", 0.00, 1.00, DEFAULTS["deficit_effect"], 0.01)
    republican_boost = st.slider("Republican deficit boost", 0.00, 0.50, DEFAULTS["republican_boost"], 0.01)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section"><div class="sidebar-section-title">Shocks</div><div class="sidebar-section-note">Outside pressures that can move inflation.</div></div>', unsafe_allow_html=True)
    oil_effect = st.slider("Oil shock effect", 0.00, 1.50, DEFAULTS["oil_effect"], 0.01)
    recession_effect = st.slider("Recession effect", -2.00, 1.00, DEFAULTS["recession_effect"], 0.01)
    noise_scale = st.slider("Random variation", 0.00, 1.20, DEFAULTS["noise_scale"], 0.01)
    st.markdown("</div>", unsafe_allow_html=True)

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
        <div class="mini-legend">
            <div class="mini-pill"><span class="mini-dot" style="background:#2563EB;"></span> Democratic periods</div>
            <div class="mini-pill"><span class="mini-dot" style="background:#DC2626;"></span> Republican periods</div>
            <div class="mini-pill"><span class="mini-dot" style="background:#F59E0B;"></span> Inflation line / trend</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Years Shown", f"{len(df)}")
m2.metric("Avg Deficit % GDP", f"{df['DeficitPctGDP'].mean():.2f}")
m3.metric("Avg Next-Year Inflation", f"{df['InflationNextYear'].mean():.2f}%")
m4.metric("Recession Years", f"{int(df['Recession'].sum())}")

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
    )

fig_time.add_trace(
    go.Scatter(
        x=df["Year"],
        y=df["InflationNextYear"],
        mode="lines+markers",
        name="Next-Year Inflation",
        line=dict(color="#F59E0B", width=3),
        marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>Next-Year Inflation: %{y:.2f}%<extra></extra>",
    )
)

fig_time.add_trace(
    go.Scatter(
        x=df["Year"],
        y=df["DeficitPctGDP"],
        mode="lines+markers",
        name="Deficit % GDP",
        yaxis="y2",
        line=dict(color="#2DD4BF", width=3),
        marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>Deficit: %{y:.2f}% of GDP<extra></extra>",
    )
)

for _, row in df[df["Recession"] == 1].iterrows():
    fig_time.add_vline(
        x=row["Year"],
        line_width=1,
        line_dash="dot",
        line_color="rgba(148,163,184,0.65)"
    )

layout1 = base_layout("Simulated Deficits and Next-Year Inflation Over Time")
layout1["height"] = 560
layout1["yaxis"]["title"] = "Inflation (%)"
layout1["yaxis2"] = dict(
    title="Deficit (% GDP)",
    overlaying="y",
    side="right",
    showgrid=False,
    color="#E8EEF9",
)
layout1["legend"] = dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1,
    bgcolor="rgba(0,0,0,0)",
)
fig_time.update_layout(**layout1)
st.plotly_chart(fig_time, use_container_width=True)

fig_scatter = go.Figure()

dem = df[df["Party"] == "Democrat"]
rep = df[df["Party"] == "Republican"]

fig_scatter.add_trace(
    go.Scatter(
        x=dem["DeficitPctGDP"],
        y=dem["InflationNextYear"],
        mode="markers",
        name="Democrat",
        marker=dict(size=11, color="#2563EB"),
        text=dem["Year"].astype(str),
        customdata=dem[["Administration"]],
        hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>Federal Deficit: %{x:.2f}% of GDP<br>Next-Year Inflation: %{y:.2f}%<extra></extra>",
    )
)

fig_scatter.add_trace(
    go.Scatter(
        x=rep["DeficitPctGDP"],
        y=rep["InflationNextYear"],
        mode="markers",
        name="Republican",
        marker=dict(size=11, color="#DC2626"),
        text=rep["Year"].astype(str),
        customdata=rep[["Administration"]],
        hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>Federal Deficit: %{x:.2f}% of GDP<br>Next-Year Inflation: %{y:.2f}%<extra></extra>",
    )
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
        line=dict(color="#F59E0B", width=3, dash="dash"),
        hoverinfo="skip",
    )
)

layout2 = base_layout("Deficit % GDP vs. Next-Year Inflation")
layout2["height"] = 540
layout2["xaxis"]["title"] = "Federal Deficit (% GDP)"
layout2["yaxis"]["title"] = "Next-Year Inflation (%)"
layout2["legend"] = dict(
    orientation="h",
    yanchor="top",
    y=-0.14,
    xanchor="left",
    x=0,
    bgcolor="rgba(0,0,0,0)",
    font=dict(size=12, color="#E8EEF9"),
)
layout2["margin"] = dict(l=20, r=20, t=78, b=85)
fig_scatter.update_layout(**layout2)
st.plotly_chart(fig_scatter, use_container_width=True)

summary = (
    df.groupby(["Administration", "Party"], as_index=False)[["DeficitPctGDP", "InflationNextYear"]]
    .mean()
    .round(2)
)

admin_color_map = {
    row["Administration"]: ("#DC2626" if row["Party"] == "Republican" else "#2563EB")
    for _, row in summary.iterrows()
}

fig_admin = go.Figure()
fig_admin.add_trace(
    go.Bar(
        x=summary["Administration"],
        y=summary["DeficitPctGDP"],
        name="Avg Deficit % GDP",
        marker_color=[admin_color_map[a] for a in summary["Administration"]],
    )
)
fig_admin.add_trace(
    go.Bar(
        x=summary["Administration"],
        y=summary["InflationNextYear"],
        name="Avg Next-Year Inflation",
        marker_color="#F59E0B",
    )
)

layout3 = base_layout("Average Simulated Values by Administration")
layout3["height"] = 500
layout3["hovermode"] = "closest"
layout3["barmode"] = "group"
layout3["xaxis"]["title"] = "Administration"
layout3["yaxis"]["title"] = "Value"
layout3["legend"] = dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1,
    bgcolor="rgba(0,0,0,0)",
)
fig_admin.update_layout(**layout3)
st.plotly_chart(fig_admin, use_container_width=True)

st.markdown('<div class="section-title">Simulated Dataset</div>', unsafe_allow_html=True)
st.dataframe(df, use_container_width=True, height=560)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv,
    file_name="inflation_simulation_v8.csv",
    mime="text/csv",
)

st.markdown('<div class="section-title">References</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-note">Source pages used for the variables, coding choices, and political science framing of the simulation.</div>',
    unsafe_allow_html=True,
)

for ref in REFERENCES:
    st.markdown(
        f"""
        <div class="reference-card">
            <div>{ref["citation"]}</div>
            <div style="margin-top:0.5rem;">
                <a href="{ref["url"]}" target="_blank">Open source</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )