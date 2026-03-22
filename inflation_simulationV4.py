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

# -----------------------------
# DEFAULTS
# -----------------------------
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

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

# -----------------------------
# PARTY / ADMINISTRATION SETUP
# -----------------------------
ADMINS = [
    {"name": "Carter",  "start": 1980, "end": 1980, "party": "Democrat",   "line": "#1D4ED8", "fill": "rgba(29,78,216,0.18)"},
    {"name": "Reagan",  "start": 1981, "end": 1988, "party": "Republican", "line": "#B91C1C", "fill": "rgba(185,28,28,0.18)"},
    {"name": "Bush 41", "start": 1989, "end": 1992, "party": "Republican", "line": "#FCA5A5", "fill": "rgba(252,165,165,0.16)"},
    {"name": "Clinton", "start": 1993, "end": 2000, "party": "Democrat",   "line": "#93C5FD", "fill": "rgba(147,197,253,0.16)"},
    {"name": "Bush 43", "start": 2001, "end": 2008, "party": "Republican", "line": "#FCA5A5", "fill": "rgba(252,165,165,0.16)"},
    {"name": "Obama",   "start": 2009, "end": 2016, "party": "Democrat",   "line": "#1D4ED8", "fill": "rgba(29,78,216,0.18)"},
    {"name": "Trump",   "start": 2017, "end": 2020, "party": "Republican", "line": "#B91C1C", "fill": "rgba(185,28,28,0.18)"},
    {"name": "Biden",   "start": 2021, "end": 2025, "party": "Democrat",   "line": "#93C5FD", "fill": "rgba(147,197,253,0.16)"},
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

# -----------------------------
# HELPERS
# -----------------------------
def get_theme_colors(mode: str):
    if mode == "Dark":
        return {
            "bg": "#05080F",
            "bg2": "#0A1020",
            "panel": "#0B1220",
            "panel2": "#101A2F",
            "text": "#E8EEF9",
            "muted": "#9DB1D3",
            "border": "rgba(125,151,195,0.18)",
            "accent": "#60A5FA",
            "accent2": "#93C5FD",
            "chart_bg": "#08101D",
            "grid": "rgba(125,151,195,0.14)",
            "shadow": "0 18px 46px rgba(0,0,0,0.30)",
            "toolbar_bg": "rgba(5,8,15,0.86)",
        }
    return {
        "bg": "#F4F8FF",
        "bg2": "#EAF2FF",
        "panel": "#FFFFFF",
        "panel2": "#F4F8FF",
        "text": "#0F172A",
        "muted": "#52627F",
        "border": "rgba(15,23,42,0.10)",
        "accent": "#1D4ED8",
        "accent2": "#60A5FA",
        "chart_bg": "#FFFFFF",
        "grid": "rgba(15,23,42,0.10)",
        "shadow": "0 18px 36px rgba(15,23,42,0.08)",
        "toolbar_bg": "rgba(255,255,255,0.86)",
    }

def inject_css(c):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(29,78,216,0.18), transparent 22%),
                radial-gradient(circle at top right, rgba(96,165,250,0.12), transparent 22%),
                linear-gradient(180deg, {c["bg"]} 0%, {c["bg2"]} 100%);
            color: {c["text"]};
        }}

        .block-container {{
            padding-top: 5.4rem !important;
            padding-bottom: 2rem !important;
            max-width: 1360px;
        }}

        div[data-testid="stHorizontalBlock"]:first-of-type {{
            position: sticky;
            top: 3.7rem;
            z-index: 999;
            padding: 0.35rem 0.4rem;
            margin-bottom: 1.1rem;
            background: {c["toolbar_bg"]};
            backdrop-filter: blur(10px);
            border: 1px solid {c["border"]};
            border-radius: 22px;
            box-shadow: {c["shadow"]};
        }}

        div[data-testid="stPopover"] button {{
            min-height: 3.2rem !important;
            padding: 0.85rem 1.2rem !important;
            border-radius: 999px !important;
            border: 1px solid rgba(96,165,250,0.28) !important;
            background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 55%, #60A5FA 100%) !important;
            color: white !important;
            font-weight: 800 !important;
            font-size: 1rem !important;
            box-shadow: 0 14px 28px rgba(37,99,235,0.30) !important;
            width: 100% !important;
        }}

        div[data-testid="stPopover"] button:hover {{
            filter: brightness(1.05);
            transform: translateY(-1px);
        }}

        div[data-testid="stSelectbox"] > div {{
            background: transparent !important;
        }}

        .hero-card {{
            padding: 1.2rem 1.25rem 0.65rem 1.25rem;
            border-radius: 28px;
            background: linear-gradient(145deg, {c["panel"]}, {c["panel2"]});
            border: 1px solid {c["border"]};
            box-shadow: {c["shadow"]};
            margin-bottom: 0.9rem;
        }}

        .hero-title {{
            font-size: 2.35rem;
            font-weight: 900;
            letter-spacing: -0.03em;
            line-height: 1.02;
            color: {c["text"]};
            margin-bottom: 0.45rem;
        }}

        .hero-sub {{
            font-size: 1.05rem;
            line-height: 1.65;
            color: {c["muted"]};
            max-width: 1020px;
            margin-bottom: 0.1rem;
        }}

        div[data-testid="stMetric"] {{
            background: linear-gradient(145deg, {c["panel"]}, {c["panel2"]});
            border: 1px solid {c["border"]};
            border-radius: 24px;
            padding: 0.55rem 0.95rem;
            box-shadow: {c["shadow"]};
        }}

        div[data-testid="stMetricLabel"] {{
            color: {c["muted"]};
            font-weight: 700;
        }}

        div[data-testid="stMetricValue"] {{
            color: {c["text"]};
            font-weight: 900;
        }}

        .stPlotlyChart, .stDataFrame {{
            border-radius: 26px;
            overflow: hidden;
            border: 1px solid {c["border"]};
            box-shadow: {c["shadow"]};
            background: {c["panel"]};
        }}

        .section-title {{
            font-size: 1.22rem;
            font-weight: 850;
            color: {c["text"]};
            margin: 1rem 0 0.6rem 0;
        }}

        .section-note {{
            color: {c["muted"]};
            font-size: 0.94rem;
            margin-bottom: 0.7rem;
        }}

        .reference-card {{
            padding: 1rem 1rem;
            border-radius: 18px;
            background: linear-gradient(145deg, {c["panel"]}, {c["panel2"]});
            border: 1px solid {c["border"]};
            box-shadow: {c["shadow"]};
            margin-bottom: 0.7rem;
        }}

        .reference-card a {{
            color: {c["accent"]} !important;
            font-weight: 800;
            text-decoration: none;
        }}

        .reference-card a:hover {{
            text-decoration: underline;
        }}

        .stDownloadButton button {{
            border-radius: 999px !important;
            padding: 0.72rem 1.05rem !important;
            border: 1px solid {c["border"]} !important;
            background: linear-gradient(135deg, {c["panel2"]}, {c["panel"]}) !important;
            color: {c["text"]} !important;
            font-weight: 800 !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.35rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 999px;
            padding: 0.45rem 0.9rem;
        }}
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
    admin_colors = np.array([a["line"] for a in admins])

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

    df = pd.DataFrame({
        "Year": years,
        "Administration": administrations,
        "Party": parties,
        "DeficitPctGDP": np.round(deficit, 2),
        "OilShock": np.round(oil_shock, 2),
        "Recession": recession,
        "InflationNextYear": np.round(inflation_next_year, 2),
        "AdminColor": admin_colors,
    })

    df["RecessionLabel"] = np.where(df["Recession"] == 1, "Recession Year", "No Recession")
    return df

def chart_layout(c, title):
    return dict(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=c["chart_bg"],
        font=dict(color=c["text"]),
        margin=dict(l=20, r=20, t=70, b=20),
        xaxis=dict(
            title="Year",
            showgrid=True,
            gridcolor=c["grid"],
            zeroline=False,
            color=c["text"],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=c["grid"],
            zeroline=False,
            color=c["text"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
        height=560,
    )

# -----------------------------
# UI STATE
# -----------------------------
theme_bar_left, theme_bar_mid, theme_bar_right = st.columns([2.7, 5.3, 1.8], gap="small")

with theme_bar_left:
    controls_host = st.popover("⚙️ Open Simulation Controls", use_container_width=True)

with theme_bar_right:
    theme_choice = st.selectbox(
        "Theme",
        ["Dark", "Light"],
        index=0 if st.session_state.theme_mode == "Dark" else 1,
        label_visibility="collapsed",
    )
    st.session_state.theme_mode = theme_choice

colors = get_theme_colors(st.session_state.theme_mode)
inject_css(colors)

with controls_host:
    st.markdown("#### Controls")
    st.caption("Adjust the model and instantly update the simulation.")

    years_tab, model_tab, shock_tab = st.tabs(["Years", "Model", "Shocks"])

    with years_tab:
        year_range = st.slider("Year range", 1980, 2025, DEFAULTS["year_range"])
        seed = st.number_input("Random seed", min_value=1, max_value=9999, value=DEFAULTS["seed"], step=1)

    with model_tab:
        base_inflation = st.slider("Base inflation", 0.0, 5.0, DEFAULTS["base_inflation"], 0.1)
        deficit_effect = st.slider("Deficit effect", 0.00, 1.00, DEFAULTS["deficit_effect"], 0.01)
        republican_boost = st.slider("Republican deficit boost", 0.00, 0.50, DEFAULTS["republican_boost"], 0.01)

    with shock_tab:
        oil_effect = st.slider("Oil shock effect", 0.00, 1.50, DEFAULTS["oil_effect"], 0.01)
        recession_effect = st.slider("Recession effect", -2.00, 1.00, DEFAULTS["recession_effect"], 0.01)
        noise_scale = st.slider("Random variation", 0.00, 1.20, DEFAULTS["noise_scale"], 0.01)

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

# -----------------------------
# HERO
# -----------------------------
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

m1, m2, m3, m4 = st.columns(4)
m1.metric("Years Shown", f"{len(df)}")
m2.metric("Avg Deficit % GDP", f"{df['DeficitPctGDP'].mean():.2f}")
m3.metric("Avg Next-Year Inflation", f"{df['InflationNextYear'].mean():.2f}%")
m4.metric("Recession Years", f"{int(df['Recession'].sum())}")

# -----------------------------
# CHART 1: TIME SERIES
# -----------------------------
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
        line_color="rgba(148,163,184,0.70)"
    )

time_layout = chart_layout(colors, "Simulated Deficits and Next-Year Inflation Over Time")
time_layout["yaxis"]["title"] = "Inflation (%)"
time_layout["yaxis2"] = dict(
    title="Deficit (% GDP)",
    overlaying="y",
    side="right",
    showgrid=False,
    color=colors["text"],
)
fig_time.update_layout(**time_layout)
st.plotly_chart(fig_time, use_container_width=True)

# -----------------------------
# CHART 2: SCATTER
# -----------------------------
admin_color_map = {a["name"]: a["line"] for a in ADMINS}

fig_scatter = px.scatter(
    df,
    x="DeficitPctGDP",
    y="InflationNextYear",
    color="Administration",
    symbol="RecessionLabel",
    color_discrete_map=admin_color_map,
    hover_data=["Year", "Party", "OilShock"],
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
    )
)

scatter_layout = chart_layout(colors, "Deficit % GDP vs. Next-Year Inflation")
scatter_layout["height"] = 520
scatter_layout["xaxis"]["title"] = "Federal Deficit (% GDP)"
scatter_layout["yaxis"]["title"] = "Next-Year Inflation (%)"
fig_scatter.update_layout(**scatter_layout)
st.plotly_chart(fig_scatter, use_container_width=True)

# -----------------------------
# CHART 3: ADMIN SUMMARY
# -----------------------------
summary = (
    df.groupby(["Administration", "Party"], as_index=False)[["DeficitPctGDP", "InflationNextYear"]]
    .mean()
    .round(2)
)

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

admin_layout = chart_layout(colors, "Average Simulated Values by Administration")
admin_layout["height"] = 500
admin_layout["hovermode"] = "closest"
admin_layout["barmode"] = "group"
admin_layout["xaxis"]["title"] = "Administration"
admin_layout["yaxis"]["title"] = "Value"
fig_admin.update_layout(**admin_layout)
st.plotly_chart(fig_admin, use_container_width=True)

# -----------------------------
# DATA TABLE
# -----------------------------
st.markdown('<div class="section-title">Simulated Dataset</div>', unsafe_allow_html=True)
st.dataframe(df, use_container_width=True, height=560)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv,
    file_name="inflation_simulation_v4.csv",
    mime="text/csv",
)

# -----------------------------
# REFERENCES
# -----------------------------
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