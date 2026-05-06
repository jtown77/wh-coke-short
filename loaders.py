"""Excel + market-data loaders. All cached so the app reads the model once per session."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

MODEL_FILE = Path(__file__).parent / "data" / "WH COKE Model v04.29.2026.xlsx"
TICKER = "COKE"


@st.cache_data(show_spinner=False)
def load_workbook_bytes() -> bytes:
    return MODEL_FILE.read_bytes()


def _read_sheet(sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(MODEL_FILE, sheet_name=sheet_name, header=None, engine="openpyxl")


@st.cache_data(show_spinner=False)
def load_summary() -> dict:
    """Pulls the Summary tab into a structured dict for the top block."""
    df = _read_sheet("Summary")

    years = list(range(2022, 2030))
    cols_g_to_n = list(range(6, 14))

    def row(i: int) -> list[float]:
        return [df.iat[i, c] for c in cols_g_to_n]

    revenue = row(3)
    ebitda = row(11)
    ebitda_margin = row(12)
    eps = row(21)
    eps_yoy = row(22)
    revenue_yoy = row(4)
    ebitda_yoy = row(13)

    valuation_years = years
    ev_sales = row(29)
    wh_ev_ebitda = row(32)
    wh_pe = row(33)
    shares_out = row(35)
    net_debt_yr = row(36)
    adj_tev = row(37)

    cap_table = {
        "price": float(df.iat[6, 3]),
        "diluted_shares": float(df.iat[7, 3]),
        "total_debt": float(df.iat[9, 3]),
        "cash": float(df.iat[10, 3]),
        "nci": float(df.iat[12, 3]),
    }

    return_scenarios_eps = [
        {"label": "Bull", "metric": float(df.iat[4, 16]), "multiple": float(df.iat[4, 17]),
         "target": float(df.iat[4, 18]), "npv": float(df.iat[4, 19]),
         "ret": float(df.iat[4, 20]), "irr": float(df.iat[4, 21])},
        {"label": "Base", "metric": float(df.iat[5, 16]), "multiple": float(df.iat[5, 17]),
         "target": float(df.iat[5, 18]), "npv": float(df.iat[5, 19]),
         "ret": float(df.iat[5, 20]), "irr": float(df.iat[5, 21])},
        {"label": "Bear", "metric": float(df.iat[6, 16]), "multiple": float(df.iat[6, 17]),
         "target": float(df.iat[6, 18]), "npv": float(df.iat[6, 19]),
         "ret": float(df.iat[6, 20]), "irr": float(df.iat[6, 21])},
    ]
    return_scenarios_ebitda = [
        {"label": "Bull", "metric": float(df.iat[10, 16]), "multiple": float(df.iat[10, 17]),
         "target": float(df.iat[10, 18]), "npv": float(df.iat[10, 19]),
         "ret": float(df.iat[10, 20]), "irr": float(df.iat[10, 21])},
        {"label": "Base", "metric": float(df.iat[11, 16]), "multiple": float(df.iat[11, 17]),
         "target": float(df.iat[11, 18]), "npv": float(df.iat[11, 19]),
         "ret": float(df.iat[11, 20]), "irr": float(df.iat[11, 21])},
        {"label": "Bear", "metric": float(df.iat[12, 16]), "multiple": float(df.iat[12, 17]),
         "target": float(df.iat[12, 18]), "npv": float(df.iat[12, 19]),
         "ret": float(df.iat[12, 20]), "irr": float(df.iat[12, 21])},
    ]

    return {
        "years": years,
        "revenue": revenue,
        "revenue_yoy": revenue_yoy,
        "ebitda": ebitda,
        "ebitda_margin": ebitda_margin,
        "ebitda_yoy": ebitda_yoy,
        "eps": eps,
        "eps_yoy": eps_yoy,
        "valuation": {
            "years": valuation_years,
            "ev_sales": ev_sales,
            "ev_ebitda": wh_ev_ebitda,
            "pe": wh_pe,
            "shares_out": shares_out,
            "net_debt": net_debt_yr,
            "adj_tev": adj_tev,
        },
        "cap_table_static": cap_table,
        "return_eps": return_scenarios_eps,
        "return_ebitda": return_scenarios_ebitda,
    }


@st.cache_data(show_spinner=False)
def load_segment_build() -> dict:
    """Pulls Segment Build tab — quarterly Sparkling and Still volume + price YoY growth + scatter source data."""
    df = _read_sheet("Segment Build")

    quarter_labels = [df.iat[4, c] for c in range(5, 61)]

    def row(i: int, start: int = 5, end: int = 61) -> list[float | None]:
        out = []
        for c in range(start, end):
            v = df.iat[i, c]
            out.append(v if pd.notna(v) else None)
        return out

    return {
        "quarters": quarter_labels,
        "total_revenue": row(7),
        "total_cases": row(8),
        "total_cases_yoy": row(9),
        "sparkling_volume": row(11),
        "sparkling_volume_yoy": row(12),
        "sparkling_price": row(17),
        "sparkling_price_yoy": row(18),
        "still_volume": row(24),
        "still_volume_yoy": row(25),
        "still_price": row(30),
        "still_price_yoy": row(31),
    }


@st.cache_data(show_spinner=False)
def load_cogs_sensitivity() -> dict:
    """Pulls COGS Sensitivity tab — aluminum price/volume/spend by quarter."""
    df = _read_sheet("COGS Sensitivity")
    quarter_labels = [df.iat[4, c] for c in range(5, 61)]

    def row(i: int) -> list[float | None]:
        return [df.iat[i, c] if pd.notna(df.iat[i, c]) else None for c in range(5, 61)]

    return {
        "quarters": quarter_labels,
        "lme_price": row(13),
        "midwest_premium": row(14),
        "all_in_us_price": row(15),
        "cck_markup": row(16),
        "all_in_cost_per_kg": row(40),
        "aluminum_volume_kg_mm": row(39),
        "aluminum_spend_mm": row(41),
        "yoy_change_combined": row(20),
    }


@st.cache_data(ttl=300, show_spinner=False)
def load_live_price() -> float:
    t = yf.Ticker(TICKER)
    info = t.info
    p = info.get("regularMarketPrice") or info.get("currentPrice")
    if p is None:
        hist = t.history(period="1d")
        p = float(hist["Close"].iloc[-1])
    return float(p)


def derive_cap_table(static: dict, live_price: float) -> dict:
    """Replicates the Summary cap-table math with a live price input."""
    market_cap = live_price * static["diluted_shares"]
    net_debt = static["total_debt"] - static["cash"]
    enterprise_value = market_cap + net_debt + static["nci"]
    return {
        "price": live_price,
        "diluted_shares": static["diluted_shares"],
        "market_cap": market_cap,
        "total_debt": static["total_debt"],
        "cash": static["cash"],
        "net_debt": net_debt,
        "nci": static["nci"],
        "enterprise_value": enterprise_value,
    }
