from pathlib import Path
import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Deficits, Inflation, and Presidential Party",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_DIR = Path(__file__).parent
DATA_PATH = APP_DIR / "data" / "official_fiscal_inflation_panel.csv"

COLORS = {
    "bg": "#05070C",
    "panel": "#0B111A",
    "panel_alt": "#121A26",
    "text": "#EEF3FB",
    "muted": "#A1B1C8",
    "soft": "#CED9EA",
    "grid": "rgba(161, 177, 200, 0.14)",
    "border": "rgba(161, 177, 200, 0.14)",
    "blue": "#4CA8FF",
    "blue_fill": "rgba(76, 168, 255, 0.10)",
    "red": "#FF5B6E",
    "red_fill": "rgba(255, 91, 110, 0.10)",
    "amber": "#FFB34D",
    "silver": "#AFC1DB",
    "white": "#F7FAFF",
}

RECESSION_YEARS = {1980, 1981, 1982, 1990, 1991, 2001, 2008, 2009, 2020}
SIM_DEFICIT_SPIKES = {1983, 1984, 1985, 2009, 2010, 2020, 2021}
SIM_OIL_SPIKES = {1980: 2.2, 1981: 1.4, 1990: 1.5, 2008: 2.1, 2011: 0.9, 2022: 2.4}

ADMINISTRATIONS = [
    {"name": "Carter", "start": 1980, "end": 1980, "party": "Democrat", "fill": "rgba(76, 168, 255, 0.08)"},
    {"name": "Reagan", "start": 1981, "end": 1988, "party": "Republican", "fill": "rgba(255, 91, 110, 0.07)"},
    {"name": "Bush 41", "start": 1989, "end": 1992, "party": "Republican", "fill": "rgba(255, 91, 110, 0.05)"},
    {"name": "Clinton", "start": 1993, "end": 2000, "party": "Democrat", "fill": "rgba(76, 168, 255, 0.06)"},
    {"name": "Bush 43", "start": 2001, "end": 2008, "party": "Republican", "fill": "rgba(255, 91, 110, 0.05)"},
    {"name": "Obama", "start": 2009, "end": 2016, "party": "Democrat", "fill": "rgba(76, 168, 255, 0.06)"},
    {"name": "Trump", "start": 2017, "end": 2020, "party": "Republican", "fill": "rgba(255, 91, 110, 0.07)"},
    {"name": "Biden", "start": 2021, "end": 2025, "party": "Democrat", "fill": "rgba(76, 168, 255, 0.08)"},
]

OUTCOME_OPTIONS = {
    "Next-year inflation (main design)": {
        "column": "inflation_next_year_pct",
        "label": "Next-year inflation",
        "description": "Fiscal year deficit in year t matched to inflation in year t+1.",
    },
    "Same-year inflation": {
        "column": "inflation_same_year_pct",
        "label": "Same-year inflation",
        "description": "Fiscal year deficit in year t matched to inflation in year t.",
    },
}

SIM_CONTROL_SPECS = {
    "base_inflation": {"label": "Base inflation", "baseline": 2.1},
    "deficit_effect": {"label": "Deficit effect", "baseline": 0.22},
    "republican_boost": {"label": "Republican boost", "baseline": 0.12},
    "oil_effect": {"label": "Oil shock effect", "baseline": 0.55},
    "recession_effect": {"label": "Recession effect", "baseline": -0.65},
    "noise_scale": {"label": "Random variation", "baseline": 0.45},
}

SOURCE_CARDS = [
    {
        "title": "OMB Historical Table 1.2",
        "used_for": "Federal surplus or deficit as a percent of GDP",
        "url": "https://www.govinfo.gov/app/details/BUDGET-2025-TAB/BUDGET-2025-TAB-2-2",
        "note": "Official federal budget historical table. The app uses only the actual rows through 2023 and excludes estimate rows.",
    },
    {
        "title": "BLS Public Data API v2",
        "used_for": "Annual average CPI-U values used to compute inflation",
        "url": "https://www.bls.gov/developers/api_signature_v2.htm",
        "note": "The real-data panel is regenerated from the official BLS API using annual averages.",
    },
    {
        "title": "BLS CPI-U Series CUUR0000SA0",
        "used_for": "Series definition for All items, U.S. city average",
        "url": "https://download.bls.gov/pub/time.series/cu/cu.series",
        "note": "This is the exact CPI-U series used to calculate same-year and next-year inflation.",
    },
]

EVENTS = {
    1980: "1980 inflation spike",
    1998: "Budget surplus era",
    2009: "Great Recession",
    2020: "Pandemic deficit shock",
}


def inject_css() -> None:
    st.markdown(
        textwrap.dedent(
            f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800&family=Space+Grotesk:wght@400;500;700&display=swap');

            html, body, [class*="css"] {{
                font-family: "Space Grotesk", sans-serif;
            }}

            .stApp {{
                background:
                    radial-gradient(circle at 15% 0%, rgba(76, 168, 255, 0.12), transparent 24%),
                    radial-gradient(circle at 88% 8%, rgba(255, 91, 110, 0.10), transparent 22%),
                    linear-gradient(180deg, #04060A 0%, #060910 28%, #090C14 100%);
                color: {COLORS["text"]};
            }}

            .stApp::before {{
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background-image:
                    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
                background-size: 38px 38px;
                mask-image: linear-gradient(180deg, rgba(255,255,255,0.18), transparent 80%);
            }}

            .block-container {{
                max-width: 1460px;
                padding-top: 1.8rem !important;
                padding-bottom: 2rem !important;
            }}

            section[data-testid="stSidebar"] {{
                background:
                    linear-gradient(180deg, rgba(10,16,25,0.98), rgba(8,13,21,0.97)),
                    linear-gradient(135deg, rgba(76,168,255,0.06), rgba(255,91,110,0.05));
                border-right: 1px solid {COLORS["border"]};
            }}

            section[data-testid="stSidebar"] > div {{
                padding-top: 0.9rem;
            }}

            .sidebar-shell {{
                padding-top: 0.15rem;
            }}

            .sidebar-badge {{
                display: block;
                width: 100%;
                padding: 0.92rem 1rem;
                border-radius: 18px;
                background: linear-gradient(135deg, rgba(76,168,255,0.18), rgba(255,91,110,0.18));
                border: 1px solid rgba(255,255,255,0.14);
                box-shadow: 0 18px 36px rgba(0,0,0,0.22);
                backdrop-filter: blur(18px) saturate(140%);
                -webkit-backdrop-filter: blur(18px) saturate(140%);
                color: {COLORS["text"]};
                font-family: "Orbitron", sans-serif;
                font-size: 0.92rem;
                font-weight: 800;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                text-align: center;
                margin-bottom: 0.85rem;
            }}

            .sidebar-sub {{
                color: {COLORS["muted"]};
                font-size: 0.91rem;
                line-height: 1.5;
                margin-bottom: 1rem;
            }}

            .sidebar-divider {{
                height: 1px;
                background: linear-gradient(90deg, rgba(76,168,255,0.32), rgba(255,91,110,0.26), transparent);
                margin: 0.95rem 0;
            }}

            .hero-card {{
                position: relative;
                overflow: hidden;
                padding: 1.25rem 1.3rem 1.05rem 1.3rem;
                border-radius: 28px;
                background:
                    linear-gradient(145deg, rgba(10,16,25,0.78), rgba(15,23,35,0.72)),
                    linear-gradient(135deg, rgba(76,168,255,0.08), rgba(255,91,110,0.07));
                border: 1px solid rgba(255,255,255,0.14);
                box-shadow: 0 24px 56px rgba(0,0,0,0.28);
                backdrop-filter: blur(20px) saturate(145%);
                -webkit-backdrop-filter: blur(20px) saturate(145%);
                margin-top: 0.45rem;
                margin-bottom: 1rem;
            }}

            .hero-card::after {{
                content: "";
                position: absolute;
                inset: -12% auto -12% -36%;
                width: 34%;
                background: linear-gradient(115deg, transparent 0%, rgba(255,255,255,0.09) 48%, transparent 100%);
                transform: skewX(-18deg) translateX(-180%);
                animation: hero-sheen 11s ease-in-out infinite;
                opacity: 0;
                pointer-events: none;
            }}

            @keyframes hero-sheen {{
                0%, 12% {{
                    transform: skewX(-18deg) translateX(-180%);
                    opacity: 0;
                }}
                26% {{
                    opacity: 0.22;
                }}
                44% {{
                    transform: skewX(-18deg) translateX(520%);
                    opacity: 0;
                }}
                100% {{
                    transform: skewX(-18deg) translateX(520%);
                    opacity: 0;
                }}
            }}

            .hero-rail {{
                height: 5px;
                border-radius: 999px;
                background: linear-gradient(90deg, {COLORS["blue"]} 0%, {COLORS["blue"]} 48%, {COLORS["red"]} 52%, {COLORS["red"]} 100%);
                margin-bottom: 1rem;
            }}

            .hero-grid {{
                display: grid;
                grid-template-columns: minmax(0, 1.85fr) minmax(260px, 0.95fr);
                gap: 1rem;
                align-items: stretch;
            }}

            .hero-eyebrow {{
                color: {COLORS["muted"]};
                font-family: "Orbitron", sans-serif;
                font-size: 0.77rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                margin-bottom: 0.5rem;
            }}

            .hero-title {{
                color: {COLORS["text"]};
                font-family: "Orbitron", sans-serif;
                font-size: 2.05rem;
                font-weight: 800;
                letter-spacing: -0.03em;
                line-height: 1.03;
                margin-bottom: 0.55rem;
            }}

            .hero-sub {{
                color: {COLORS["soft"]};
                font-size: 0.98rem;
                line-height: 1.58;
                max-width: 920px;
                margin-bottom: 0.8rem;
            }}

            .chip-row {{
                display: flex;
                gap: 0.6rem;
                flex-wrap: wrap;
            }}

            .chip {{
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                padding: 0.42rem 0.8rem;
                border-radius: 999px;
                font-size: 0.83rem;
                color: {COLORS["text"]};
                border: 1px solid rgba(255,255,255,0.10);
                background: rgba(255,255,255,0.03);
            }}

            .chip-dot {{
                width: 10px;
                height: 10px;
                border-radius: 999px;
                display: inline-block;
            }}

            .hero-side {{
                display: grid;
                gap: 0.72rem;
                padding-top: 1.05rem;
                align-content: start;
            }}

            .hero-mini {{
                padding: 0.88rem 0.95rem;
                border-radius: 18px;
                background: linear-gradient(145deg, rgba(13,21,33,0.74), rgba(18,29,45,0.66));
                border: 1px solid rgba(255,255,255,0.12);
                backdrop-filter: blur(16px) saturate(140%);
                -webkit-backdrop-filter: blur(16px) saturate(140%);
            }}

            .hero-mini-label {{
                color: {COLORS["muted"]};
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 0.22rem;
            }}

            .hero-mini-value {{
                color: {COLORS["text"]};
                font-family: "Orbitron", sans-serif;
                font-size: 1rem;
                font-weight: 700;
                line-height: 1.3;
            }}

            div[data-testid="stMetric"] {{
                background: linear-gradient(145deg, rgba(10,16,25,0.96), rgba(15,23,35,0.94));
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 22px;
                padding: 0.7rem 0.95rem;
                box-shadow: 0 18px 40px rgba(0,0,0,0.24);
            }}

            div[data-testid="stMetricLabel"] {{
                color: {COLORS["muted"]};
                font-weight: 700;
            }}

            div[data-testid="stMetricValue"] {{
                color: {COLORS["text"]};
                font-family: "Orbitron", sans-serif;
                font-weight: 700;
            }}

            .stPlotlyChart, .stDataFrame {{
                border-radius: 24px;
                overflow: hidden;
                border: 1px solid rgba(255,255,255,0.08);
                box-shadow: 0 20px 46px rgba(0,0,0,0.26);
                background: rgba(10,16,25,0.92);
            }}

            .section-title {{
                margin: 1rem 0 0.25rem 0;
                color: {COLORS["text"]};
                font-family: "Orbitron", sans-serif;
                font-size: 1.03rem;
                font-weight: 700;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }}

            .section-note {{
                color: {COLORS["muted"]};
                font-size: 0.91rem;
                line-height: 1.55;
                margin-bottom: 0.72rem;
            }}

            .info-card, .source-card, .model-card {{
                padding: 0.95rem 0.95rem 0.9rem 0.95rem;
                border-radius: 20px;
                background:
                    linear-gradient(145deg, rgba(10,16,25,0.76), rgba(15,23,35,0.68)),
                    linear-gradient(135deg, rgba(76,168,255,0.06), rgba(255,91,110,0.05));
                border: 1px solid rgba(255,255,255,0.11);
                box-shadow: 0 18px 36px rgba(0,0,0,0.20);
                backdrop-filter: blur(16px) saturate(140%);
                -webkit-backdrop-filter: blur(16px) saturate(140%);
            }}

            .info-kicker {{
                color: {COLORS["muted"]};
                font-family: "Orbitron", sans-serif;
                font-size: 0.72rem;
                letter-spacing: 0.10em;
                text-transform: uppercase;
                margin-bottom: 0.42rem;
            }}

            .info-title {{
                color: {COLORS["text"]};
                font-size: 1rem;
                font-weight: 700;
                margin-bottom: 0.3rem;
            }}

            .info-copy {{
                color: {COLORS["soft"]};
                font-size: 0.9rem;
                line-height: 1.52;
            }}

            .source-card a {{
                color: {COLORS["blue"]} !important;
                text-decoration: none;
                font-weight: 700;
            }}

            .source-card a:hover {{
                text-decoration: underline;
            }}

            .summary-box {{
                padding: 0.95rem 1rem 0.9rem 1rem;
                border-radius: 20px;
                background:
                    linear-gradient(145deg, rgba(10,16,25,0.80), rgba(15,23,35,0.72)),
                    linear-gradient(135deg, rgba(76,168,255,0.07), rgba(255,91,110,0.06));
                border: 1px solid rgba(255,255,255,0.12);
                color: {COLORS["soft"]};
                line-height: 1.58;
                margin-bottom: 0.85rem;
                backdrop-filter: blur(16px) saturate(140%);
                -webkit-backdrop-filter: blur(16px) saturate(140%);
            }}

            .summary-box strong {{
                color: {COLORS["text"]};
            }}

            .model-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.72rem;
                margin-bottom: 0.85rem;
            }}

            .model-label {{
                color: {COLORS["muted"]};
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 0.2rem;
            }}

            .model-value {{
                color: {COLORS["text"]};
                font-family: "Orbitron", sans-serif;
                font-size: 1.15rem;
                font-weight: 700;
            }}

            .callout {{
                padding: 0.95rem 1rem;
                border-radius: 18px;
                background: linear-gradient(135deg, rgba(76,168,255,0.10), rgba(255,91,110,0.09));
                border: 1px solid rgba(255,255,255,0.10);
                color: {COLORS["soft"]};
                line-height: 1.55;
                backdrop-filter: blur(14px) saturate(135%);
                -webkit-backdrop-filter: blur(14px) saturate(135%);
            }}

            .callout strong {{
                color: {COLORS["text"]};
            }}

            .stDownloadButton button {{
                border-radius: 999px !important;
                padding: 0.72rem 1rem !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                background: linear-gradient(135deg, rgba(76,168,255,0.16), rgba(255,91,110,0.16)) !important;
                color: {COLORS["text"]} !important;
                font-weight: 700 !important;
            }}

            .stSlider label, .stRadio label, .stToggle label {{
                color: {COLORS["text"]} !important;
                font-weight: 700 !important;
            }}

            div[data-baseweb="slider"] > div > div > div {{
                border-radius: 999px !important;
            }}

            div[data-baseweb="slider"] [role="slider"] {{
                background: linear-gradient(135deg, rgba(76,168,255,0.30), rgba(255,91,110,0.34)) !important;
                border: 1px solid rgba(255,255,255,0.20) !important;
                box-shadow: 0 8px 22px rgba(255,91,110,0.18), inset 0 1px 0 rgba(255,255,255,0.28) !important;
            }}

            @media (max-width: 980px) {{
                .hero-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


def administration_for_year(year: int) -> dict:
    for admin in ADMINISTRATIONS:
        if admin["start"] <= year <= admin["end"]:
            return admin
    return ADMINISTRATIONS[-1]


def prepare_panel(df: pd.DataFrame) -> pd.DataFrame:
    panel = df.copy()
    panel["party_indicator"] = (panel["party"] == "Republican").astype(int)
    panel["admin_order"] = pd.Categorical(
        panel["administration"],
        categories=[admin["name"] for admin in ADMINISTRATIONS],
        ordered=True,
    )
    return panel


@st.cache_data
def load_real_panel() -> pd.DataFrame:
    return prepare_panel(pd.read_csv(DATA_PATH))


def map_adjustment_to_value(adjustment_pct: int, baseline: float) -> float:
    return baseline * (1 + (adjustment_pct / 100))


def build_simulated_panel(control_positions: dict[str, int], real_panel: pd.DataFrame) -> pd.DataFrame:
    baseline = real_panel.sort_values("year").reset_index(drop=True).copy()
    mapped = {
        key: map_adjustment_to_value(
            adjustment_pct=control_positions[key],
            baseline=spec["baseline"],
        )
        for key, spec in SIM_CONTROL_SPECS.items()
    }

    years = baseline["year"].to_numpy(dtype=int)
    deficit = baseline["deficit_pct_gdp"].to_numpy(dtype=float)
    party_num = baseline["party_indicator"].to_numpy(dtype=float)
    recession = np.array([1.0 if year in RECESSION_YEARS else 0.0 for year in years], dtype=float)
    oil_shock = np.array([SIM_OIL_SPIKES.get(year, 0.0) for year in years], dtype=float)

    base_structured = (
        SIM_CONTROL_SPECS["base_inflation"]["baseline"]
        + SIM_CONTROL_SPECS["deficit_effect"]["baseline"] * deficit
        + SIM_CONTROL_SPECS["oil_effect"]["baseline"] * oil_shock
        + SIM_CONTROL_SPECS["recession_effect"]["baseline"] * recession
        + SIM_CONTROL_SPECS["republican_boost"]["baseline"] * (deficit * party_num)
    )
    adjusted_structured = (
        mapped["base_inflation"]
        + mapped["deficit_effect"] * deficit
        + mapped["oil_effect"] * oil_shock
        + mapped["recession_effect"] * recession
        + mapped["republican_boost"] * (deficit * party_num)
    )

    same_base = baseline["inflation_same_year_pct"].to_numpy(dtype=float)
    next_base = baseline["inflation_next_year_pct"].to_numpy(dtype=float)
    residual_scale = 0.0 if np.isclose(SIM_CONTROL_SPECS["noise_scale"]["baseline"], 0) else (
        mapped["noise_scale"] / SIM_CONTROL_SPECS["noise_scale"]["baseline"]
    )

    same_residual = same_base - base_structured
    next_residual = next_base - base_structured

    sim_same = adjusted_structured + same_residual * residual_scale
    sim_next = adjusted_structured + next_residual * residual_scale

    first_cpi = float(baseline.loc[0, "cpi_annual_avg"])
    first_inflation = float(baseline.loc[0, "inflation_same_year_pct"])
    previous_cpi = first_cpi / (1 + first_inflation / 100)
    sim_cpi = []
    for inflation_rate in sim_same:
        current_cpi = previous_cpi * (1 + inflation_rate / 100)
        sim_cpi.append(current_cpi)
        previous_cpi = current_cpi

    panel = baseline.copy()
    panel["cpi_annual_avg"] = np.round(sim_cpi, 3)
    panel["inflation_same_year_pct"] = sim_same
    panel["inflation_next_year_pct"] = sim_next
    return prepare_panel(panel)


def chart_layout(title: str) -> dict:
    return {
        "title": {"text": title, "font": {"family": "Orbitron, sans-serif", "size": 18}},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": COLORS["panel"],
        "font": {"color": COLORS["text"], "family": "Space Grotesk, sans-serif"},
        "margin": {"l": 24, "r": 24, "t": 82, "b": 26},
        "xaxis": {
            "showgrid": True,
            "gridcolor": COLORS["grid"],
            "zeroline": False,
            "color": COLORS["text"],
            "tickfont": {"size": 11},
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": COLORS["grid"],
            "zeroline": False,
            "color": COLORS["text"],
            "tickfont": {"size": 11},
        },
        "hovermode": "x unified",
    }


def fit_line(x: pd.Series, y: pd.Series):
    if len(x) < 2 or np.isclose(x.std(ddof=0), 0):
        return None
    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.linspace(float(x.min()), float(x.max()), 120)
    y_line = slope * x_line + intercept
    return slope, intercept, x_line, y_line


def interaction_model(df: pd.DataFrame, outcome_col: str) -> dict:
    y = df[outcome_col].to_numpy()
    x = df["deficit_pct_gdp"].to_numpy()
    party = df["party_indicator"].to_numpy()
    X = np.column_stack([np.ones(len(df)), x, party, x * party])
    coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ coeffs
    ss_res = np.sum((y - fitted) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = np.nan if np.isclose(ss_tot, 0) else 1 - (ss_res / ss_tot)
    return {
        "dem_slope": coeffs[1],
        "rep_slope": coeffs[1] + coeffs[3],
        "interaction": coeffs[3],
        "r_squared": r_squared,
    }


def correlation(series_x: pd.Series, series_y: pd.Series) -> float:
    if len(series_x) < 2 or np.isclose(series_x.std(ddof=0), 0) or np.isclose(series_y.std(ddof=0), 0):
        return np.nan
    return float(np.corrcoef(series_x, series_y)[0, 1])


def fmt_signed(value: float, decimals: int = 2) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:+.{decimals}f}"


def add_admin_bands(fig: go.Figure, start_year: int, end_year: int) -> None:
    for admin in ADMINISTRATIONS:
        if admin["end"] < start_year or admin["start"] > end_year:
            continue
        x0 = max(admin["start"], start_year) - 0.5
        x1 = min(admin["end"], end_year) + 0.5
        fig.add_vrect(
            x0=x0,
            x1=x1,
            fillcolor=admin["fill"],
            line_width=0,
            opacity=1.0,
            layer="below",
        )


def build_time_series_figure(
    df: pd.DataFrame,
    outcome_col: str,
    outcome_label: str,
    balance_name: str,
    show_bands: bool,
    show_annotations: bool,
) -> go.Figure:
    fig = go.Figure()

    if show_bands:
        add_admin_bands(fig, int(df["year"].min()), int(df["year"].max()))

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df[outcome_col],
            mode="lines+markers",
            name=outcome_label,
            line={"color": COLORS["amber"], "width": 3},
            marker={"size": 8, "color": COLORS["amber"], "line": {"color": COLORS["panel"], "width": 1}},
            customdata=np.stack([df["administration"], df["party"]], axis=1),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{customdata[0]} (%{customdata[1]})<br>"
                + outcome_label
                + ": %{y:.2f}%<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["deficit_pct_gdp"],
            mode="lines+markers",
            name=balance_name,
            yaxis="y2",
            line={"color": COLORS["silver"], "width": 3},
            marker={"size": 8, "color": COLORS["silver"], "line": {"color": COLORS["panel"], "width": 1}},
            customdata=np.stack([df["administration"], df["omb_balance_pct_gdp"]], axis=1),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{customdata[0]}<br>"
                + balance_name
                + ": %{y:.1f}% of GDP<br>"
                "Budget balance sign: %{customdata[1]:.1f}% of GDP<extra></extra>"
            ),
        )
    )

    if show_annotations:
        for year, label in EVENTS.items():
            if year not in df["year"].values:
                continue
            row = df.loc[df["year"] == year].iloc[0]
            fig.add_annotation(
                x=int(row["year"]),
                y=float(row[outcome_col]),
                text=label,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1,
                ax=0,
                ay=-42,
                bgcolor="rgba(11,17,26,0.92)",
                bordercolor="rgba(255,255,255,0.08)",
                font={"size": 10, "color": COLORS["text"]},
            )

    layout = chart_layout(f"Deficits and {outcome_label.lower()} over time")
    layout["height"] = 580
    layout["legend"] = {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1,
        "bgcolor": "rgba(0,0,0,0)",
    }
    layout["yaxis"]["title"] = "Inflation (%)"
    layout["yaxis2"] = {
        "title": "Deficit size (% GDP)",
        "overlaying": "y",
        "side": "right",
        "showgrid": False,
        "color": COLORS["text"],
    }
    fig.update_layout(**layout)
    return fig


def build_scatter_figure(
    df: pd.DataFrame,
    outcome_col: str,
    outcome_label: str,
    split_lines: bool,
) -> go.Figure:
    fig = go.Figure()

    for party, color in [("Democrat", COLORS["blue"]), ("Republican", COLORS["red"])]:
        subset = df[df["party"] == party]
        if subset.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=subset["deficit_pct_gdp"],
                y=subset[outcome_col],
                mode="markers",
                name=party,
                marker={"size": 12, "color": color, "line": {"color": COLORS["panel"], "width": 1}},
                text=subset["year"].astype(str),
                customdata=np.stack([subset["administration"], subset["omb_balance_pct_gdp"]], axis=1),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "%{customdata[0]}<br>"
                    "Deficit size: %{x:.1f}% of GDP<br>"
                    "Budget balance sign: %{customdata[1]:.1f}% of GDP<br>"
                    + outcome_label
                    + ": %{y:.2f}%<extra></extra>"
                ),
            )
        )
        if split_lines:
            fitted = fit_line(subset["deficit_pct_gdp"], subset[outcome_col])
            if fitted:
                _, _, x_line, y_line = fitted
                fig.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode="lines",
                        name=f"{party} fit",
                        line={"color": color, "width": 2.5, "dash": "dash"},
                        hoverinfo="skip",
                    )
                )

    if not split_lines:
        fitted = fit_line(df["deficit_pct_gdp"], df[outcome_col])
        if fitted:
            _, _, x_line, y_line = fitted
            fig.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name="Overall fit",
                    line={"color": COLORS["white"], "width": 2.5, "dash": "dash"},
                    hoverinfo="skip",
                )
            )

    layout = chart_layout(f"Deficit size vs. {outcome_label.lower()}")
    layout["height"] = 540
    layout["margin"] = {"l": 24, "r": 24, "t": 82, "b": 80}
    layout["hovermode"] = "closest"
    layout["xaxis"]["title"] = "Deficit size (% GDP)"
    layout["yaxis"]["title"] = "Inflation (%)"
    layout["legend"] = {
        "orientation": "h",
        "yanchor": "top",
        "y": -0.17,
        "xanchor": "left",
        "x": 0,
        "bgcolor": "rgba(0,0,0,0)",
    }
    fig.update_layout(**layout)
    return fig


def build_admin_figure(df: pd.DataFrame, outcome_col: str, outcome_label: str) -> go.Figure:
    summary = (
        df.groupby(["administration", "party"], as_index=False)[["deficit_pct_gdp", outcome_col]]
        .mean()
        .round(2)
    )
    summary["administration"] = pd.Categorical(
        summary["administration"],
        categories=[admin["name"] for admin in ADMINISTRATIONS],
        ordered=True,
    )
    summary = summary.sort_values("administration")

    admin_colors = {
        row["administration"]: COLORS["red"] if row["party"] == "Republican" else COLORS["blue"]
        for _, row in summary.iterrows()
    }

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=summary["administration"],
            y=summary["deficit_pct_gdp"],
            name="Average deficit size",
            marker_color=[admin_colors[name] for name in summary["administration"]],
        )
    )
    fig.add_trace(
        go.Bar(
            x=summary["administration"],
            y=summary[outcome_col],
            name=outcome_label,
            marker_color=COLORS["amber"],
        )
    )

    layout = chart_layout("Average values by administration")
    layout["height"] = 500
    layout["barmode"] = "group"
    layout["hovermode"] = "closest"
    layout["xaxis"]["title"] = "Administration"
    layout["yaxis"]["title"] = "Percent"
    layout["legend"] = {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1,
        "bgcolor": "rgba(0,0,0,0)",
    }
    fig.update_layout(**layout)
    return fig


def insight_copy(model: dict, corr_value: float, mode_label: str, outcome_label: str) -> str:
    if pd.isna(corr_value):
        return "Not enough variation is available in the selected window."
    if mode_label == "Real data":
        return (
            f"This is a descriptive fit for {outcome_label.lower()}. "
            "Use it as evidence of pattern, not as a causal proof."
        )
    return (
        f"This is the simulated relationship implied by your current settings for {outcome_label.lower()}. "
        "A stronger slope means the model is making deficits matter more."
    )


def render_model_panel(model: dict, corr_value: float, mode_label: str, outcome_label: str) -> None:
    st.markdown(
        f"""
        <div class="section-title">Quick Read</div>
        <div class="section-note">Compact descriptive summary for the selected window.</div>
        <div class="model-grid">
            <div class="model-card">
                <div class="model-label">Correlation</div>
                <div class="model-value">{fmt_signed(corr_value)}</div>
            </div>
            <div class="model-card">
                <div class="model-label">Model R-squared</div>
                <div class="model-value">{model["r_squared"]:.2f}</div>
            </div>
            <div class="model-card">
                <div class="model-label">Democratic slope</div>
                <div class="model-value">{fmt_signed(model["dem_slope"])}</div>
            </div>
            <div class="model-card">
                <div class="model-label">Republican slope</div>
                <div class="model-value">{fmt_signed(model["rep_slope"])}</div>
            </div>
        </div>
        <div class="callout"><strong>Interpretation.</strong> {insight_copy(model, corr_value, mode_label, outcome_label)}</div>
        """,
        unsafe_allow_html=True,
    )


def render_source_cards() -> None:
    cols = st.columns(3)
    for col, source in zip(cols, SOURCE_CARDS):
        with col:
            st.markdown(
                f"""
                <div class="source-card">
                    <div class="info-kicker">Official source</div>
                    <div class="info-title">{source["title"]}</div>
                    <div class="info-copy"><strong>Used for:</strong> {source["used_for"]}</div>
                    <div class="info-copy" style="margin-top:0.5rem;">{source["note"]}</div>
                    <div class="info-copy" style="margin-top:0.75rem;">
                        <a href="{source["url"]}" target="_blank">Open source</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_hero(mode_label: str, year_range: tuple[int, int], outcome_label: str, summary_text: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-rail"></div>
            <div class="hero-grid">
                <div>
                    <div class="hero-eyebrow">POSC301 | deficits, inflation, and party</div>
                    <div class="hero-title">Deficits, Inflation, and Presidential Party</div>
                    <div class="hero-sub">{summary_text}</div>
                    <div class="chip-row">
                        <div class="chip"><span class="chip-dot" style="background:{COLORS["blue"]};"></span> Democratic years</div>
                        <div class="chip"><span class="chip-dot" style="background:{COLORS["red"]};"></span> Republican years</div>
                        <div class="chip"><span class="chip-dot" style="background:{COLORS["silver"]};"></span> {mode_label}</div>
                    </div>
                </div>
                <div class="hero-side">
                    <div class="hero-mini">
                        <div class="hero-mini-label">Mode</div>
                        <div class="hero-mini-value">{mode_label}</div>
                    </div>
                    <div class="hero-mini">
                        <div class="hero-mini-label">Years</div>
                        <div class="hero-mini-value">{year_range[0]}-{year_range[1]}</div>
                    </div>
                    <div class="hero-mini">
                        <div class="hero-mini-label">View</div>
                        <div class="hero-mini-value">{outcome_label}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()

    real_panel = load_real_panel()

    with st.sidebar:
        st.markdown('<div class="sidebar-shell">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-badge">Research Controls</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-sub">Switch between documented evidence and a calibrated simulation version of the project without changing the overall layout.</div>',
            unsafe_allow_html=True,
        )

        data_mode = st.radio("Data mode", ["Real data", "Simulated data"], horizontal=True)

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        if data_mode == "Real data":
            year_range = st.slider(
                "Panel years",
                min_value=int(real_panel["year"].min()),
                max_value=int(real_panel["year"].max()),
                value=(1980, int(real_panel["year"].max())),
            )
            st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
            st.markdown(
                """
                <div class="info-card">
                    <div class="info-kicker">Real data mode</div>
                    <div class="info-title">Official OMB + BLS panel</div>
                    <div class="info-copy">Uses the cleaned local panel built from published government tables. This is the version to show as evidence.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            sim_positions = None
            panel = real_panel
        else:
            year_range = st.slider(
                "Simulation years",
                min_value=int(real_panel["year"].min()),
                max_value=int(real_panel["year"].max()),
                value=(1980, int(real_panel["year"].max())),
            )
            st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
            st.markdown(
                """
                <div class="info-card">
                    <div class="info-kicker">Simulation mode</div>
                    <div class="info-title">0 = baseline calibration</div>
                    <div class="info-copy">At 0%, the simulation matches the verified real-data panel for the same years. A setting of +1 raises that parameter by 1%, while -1 lowers it by 1%. The full range runs from -100% to +100%.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            sim_positions = {}
            for key, spec in SIM_CONTROL_SPECS.items():
                sim_positions[key] = st.slider(f'{spec["label"]} adjustment (%)', -100, 100, 0, 1)
            panel = build_simulated_panel(sim_positions, real_panel=real_panel)

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        outcome_key = st.radio("Inflation alignment", list(OUTCOME_OPTIONS.keys()), index=0)
        outcome_config = OUTCOME_OPTIONS[outcome_key]

        show_party_trends = st.toggle("Split scatter fit by party", value=True)
        show_admin_bands = st.toggle("Show administration shading", value=True)
        show_annotations = st.toggle("Show milestone annotations", value=True)
        st.markdown("</div>", unsafe_allow_html=True)

    filtered = panel[panel["year"].between(year_range[0], year_range[1])].copy()
    outcome_col = outcome_config["column"]
    outcome_label = outcome_config["label"]
    balance_name = "Deficit size"

    corr_value = correlation(filtered["deficit_pct_gdp"], filtered[outcome_col])
    model = interaction_model(filtered, outcome_col)

    if data_mode == "Real data":
        hero_summary = (
            "Real-data mode uses official OMB fiscal balance percentages and BLS CPI-U annual averages. "
            "The panel is aligned so you can inspect whether bigger deficits are followed by higher inflation."
        )
    else:
        hero_summary = (
            "Simulation mode starts from the verified real-data panel and then applies controlled percentage adjustments to the model parameters. "
            "At 0%, the simulated series matches the real-data baseline for the same years."
        )

    render_hero(data_mode, year_range, outcome_label, hero_summary)

    metric_cols = st.columns(5)
    metric_cols[0].metric("Observations", f"{len(filtered)}")
    metric_cols[1].metric("Avg deficit size", f"{filtered['deficit_pct_gdp'].mean():.2f}%")
    metric_cols[2].metric(outcome_label, f"{filtered[outcome_col].mean():.2f}%")
    metric_cols[3].metric("Overall correlation", f"{corr_value:.2f}" if not pd.isna(corr_value) else "n/a")
    metric_cols[4].metric("Slope gap (R - D)", fmt_signed(model["rep_slope"] - model["dem_slope"]))

    if data_mode == "Real data":
        st.caption(
            "Deficit values come from the official OMB fiscal balance series, with the sign flipped so bigger deficits plot upward. "
            "Estimated OMB rows after 2023 are excluded."
        )
    else:
        st.caption(
            "Simulation mode is anchored to the verified real-data panel. At 0%, it matches the observed series for the same years; nonzero settings show controlled departures from that baseline."
        )

    st.plotly_chart(
        build_time_series_figure(
            filtered,
            outcome_col=outcome_col,
            outcome_label=outcome_label,
            balance_name=balance_name,
            show_bands=show_admin_bands,
            show_annotations=show_annotations,
        ),
        use_container_width=True,
    )

    left, right = st.columns([1.45, 1.0])
    with left:
        st.plotly_chart(
            build_scatter_figure(
                filtered,
                outcome_col=outcome_col,
                outcome_label=outcome_label,
                split_lines=show_party_trends,
            ),
            use_container_width=True,
        )
    with right:
        render_model_panel(model, corr_value, data_mode, outcome_label)

    st.plotly_chart(
        build_admin_figure(filtered, outcome_col=outcome_col, outcome_label=outcome_label),
        use_container_width=True,
    )

    st.markdown('<div class="section-title">Method Snapshot</div>', unsafe_allow_html=True)
    if data_mode == "Real data":
        st.markdown(
            """
            <div class="section-note">Short version: official fiscal values from OMB, official CPI-U values from BLS, then a simple merge to line deficits up with inflation.</div>
            """,
            unsafe_allow_html=True,
        )
        cards = st.columns(3)
        cards[0].markdown(
            """
            <div class="info-card">
                <div class="info-kicker">Variable 1</div>
                <div class="info-title">Deficit as % of GDP</div>
                <div class="info-copy">Taken from OMB Table 1.2. The sign is flipped in the dashboard so larger deficits move upward.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cards[1].markdown(
            """
            <div class="info-card">
                <div class="info-kicker">Variable 2</div>
                <div class="info-title">Annual CPI-U inflation</div>
                <div class="info-copy">Computed from BLS annual average CPI-U values for the U.S. city average.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cards[2].markdown(
            f"""
            <div class="info-card">
                <div class="info-kicker">Match rule</div>
                <div class="info-title">{outcome_label}</div>
                <div class="info-copy">{outcome_config["description"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="section-note">Short version: the simulation begins from the verified panel and then adjusts the theoretical parameters around that baseline.</div>
            """,
            unsafe_allow_html=True,
        )
        cards = st.columns(3)
        cards[0].markdown(
            """
            <div class="info-card">
                <div class="info-kicker">Baseline</div>
                <div class="info-title">Verified real-data panel</div>
                <div class="info-copy">At 0%, the simulated panel uses the same observed deficit and inflation series as real-data mode.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cards[1].markdown(
            """
            <div class="info-card">
                <div class="info-kicker">Equation</div>
                <div class="info-title">Project simulation model</div>
                <div class="info-copy">Inflation is driven by base inflation, deficits, party interaction, oil shocks, recessions, and random noise.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cards[2].markdown(
            """
            <div class="info-card">
                <div class="info-kicker">Controls</div>
                <div class="info-title">Percentage adjustments</div>
                <div class="info-copy">0 keeps the verified baseline. Positive values strengthen a parameter and negative values weaken it.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Panel Table</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">A clean table you can use in a paper appendix, presentation slide, or methods note.</div>',
        unsafe_allow_html=True,
    )

    if data_mode == "Real data":
        display_df = filtered.rename(
            columns={
                "year": "Year",
                "administration": "Administration",
                "party": "Party",
                "omb_balance_pct_gdp": "OMB Fiscal Balance (% GDP)",
                "deficit_pct_gdp": "Deficit Size (% GDP)",
                "cpi_annual_avg": "CPI-U Annual Average",
                "inflation_same_year_pct": "Same-Year Inflation (%)",
                "inflation_next_year_pct": "Next-Year Inflation (%)",
            }
        )
    else:
        display_df = filtered.rename(
            columns={
                "year": "Year",
                "administration": "Administration",
                "party": "Party",
                "omb_balance_pct_gdp": "Simulated Fiscal Balance (% GDP)",
                "deficit_pct_gdp": "Simulated Deficit Size (% GDP)",
                "cpi_annual_avg": "Simulated CPI Index",
                "inflation_same_year_pct": "Simulated Same-Year Inflation (%)",
                "inflation_next_year_pct": "Simulated Next-Year Inflation (%)",
            }
        )

    st.dataframe(display_df, use_container_width=True, height=520)
    st.download_button(
        "Download filtered panel as CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"fiscal_inflation_panel_{data_mode.lower().replace(' ', '_')}_{year_range[0]}_{year_range[1]}.csv",
        mime="text/csv",
    )

    st.markdown('<div class="section-title">Sources and Accuracy</div>', unsafe_allow_html=True)
    if data_mode == "Real data":
        st.markdown(
            """
            <div class="summary-box">
                <strong>How the real data was built.</strong> The app rebuilds the local panel from the official OMB historical table and the official BLS CPI-U API series,
                then computes inflation from those published annual averages. The values are accurate because they come directly from government-published sources and can be checked against the links below.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-note">Official source set used for the real-data panel: OMB Historical Table 1.2, the BLS Public Data API v2, and the CPI-U series definition for CUUR0000SA0.</div>',
            unsafe_allow_html=True,
        )
        render_source_cards()
    else:
        st.markdown(
            """
            <div class="summary-box">
                <strong>How the simulation works.</strong> This mode follows the project’s theoretical model rather than citing official evidence.
                It is best for illustrating the argument, testing assumptions, and showing how stronger or weaker effects would look.
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
