"""Excel + market-data loaders. Cached, mtime-keyed for live model edits."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

import shutil
import tempfile

LIVE_MODEL = Path(
    r"C:\Users\JoshuaLehrman\Wolf Hill Capital Management LLC\Shared - Documents\Josh\COKE\Models\WH COKE Model v04.29.2026.xlsx"
)
BUNDLED_MODEL = Path(__file__).parent / "data" / "WH COKE Model v04.29.2026.xlsx"
TICKER = "COKE"


def _model_path() -> Path:
    return LIVE_MODEL if LIVE_MODEL.exists() else BUNDLED_MODEL


def model_mtime() -> float:
    return _model_path().stat().st_mtime


def _read_sheet(sheet_name: str) -> pd.DataFrame:
    src = _model_path()
    if src == LIVE_MODEL:
        # Copy to temp to avoid Excel file lock when the user has the workbook open
        dst = Path(tempfile.gettempdir()) / "coke_model_live_snapshot.xlsx"
        try:
            shutil.copy2(src, dst)
            return pd.read_excel(dst, sheet_name=sheet_name, header=None, engine="openpyxl")
        except Exception:
            return pd.read_excel(BUNDLED_MODEL, sheet_name=sheet_name, header=None, engine="openpyxl")
    return pd.read_excel(src, sheet_name=sheet_name, header=None, engine="openpyxl")


def load_summary() -> dict:
    return _load_summary_cached(model_mtime())


@st.cache_data(show_spinner=False)
def _load_summary_cached(_mtime: float) -> dict:
    df = _read_sheet("Summary")
    years = list(range(2022, 2030))
    cols_g_to_n = list(range(6, 14))

    def row(i: int) -> list:
        return [df.iat[i, c] if pd.notna(df.iat[i, c]) else None for c in cols_g_to_n]

    cap_table = {
        "price": float(df.iat[6, 3]),
        "diluted_shares": float(df.iat[7, 3]),
        "total_debt": float(df.iat[9, 3]),
        "cash": float(df.iat[10, 3]),
        "nci": float(df.iat[12, 3]) if pd.notna(df.iat[12, 3]) else 0.0,
    }

    return_eps = [
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
    return_ebitda = [
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
        "revenue": row(3),
        "revenue_yoy": row(4),
        "ebitda": row(11),
        "ebitda_margin": row(12),
        "ebitda_yoy": row(13),
        "eps": row(21),
        "eps_yoy": row(22),
        "valuation": {
            "years": years,
            "ev_sales": row(29),
            "ev_ebitda": row(32),
            "pe": row(33),
            "shares_out": row(35),
            "net_debt": row(36),
            "adj_tev": row(37),
        },
        "cap_table_static": cap_table,
        "return_eps": return_eps,
        "return_ebitda": return_ebitda,
    }


def load_segment_build() -> dict:
    return _load_segment_build_cached(model_mtime())


@st.cache_data(show_spinner=False)
def _load_segment_build_cached(_mtime: float) -> dict:
    df = _read_sheet("Segment Build")
    quarter_labels = [df.iat[4, c] for c in range(5, 61)]

    def row(i: int) -> list:
        return [df.iat[i, c] if pd.notna(df.iat[i, c]) else None for c in range(5, 61)]

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


def load_cogs_sensitivity() -> dict:
    return _load_cogs_sensitivity_cached(model_mtime())


@st.cache_data(show_spinner=False)
def _load_cogs_sensitivity_cached(_mtime: float) -> dict:
    df = _read_sheet("COGS Sensitivity")
    quarter_labels = [df.iat[4, c] for c in range(5, 61)]

    def row(i: int) -> list:
        return [df.iat[i, c] if pd.notna(df.iat[i, c]) else None for c in range(5, 61)]

    cans_per_case = float(df.iat[32, 4])  # E33
    grams_per_can = float(df.iat[33, 4])  # E34
    kg_per_can_case = float(df.iat[34, 4])  # E35

    return {
        "quarters": quarter_labels,
        "lme_price": row(13),
        "midwest_premium": row(14),
        "all_in_us_price": row(15),
        "cck_markup": row(16),
        "all_in_cost_per_kg": row(40),
        "aluminum_volume_kg_mm": row(39),
        "aluminum_spend_mm": row(41),
        "cases_in_cans_mm": row(26),
        "kg_per_total_case": row(36),
        "content": {
            "cans_per_case": cans_per_case,
            "grams_per_can": grams_per_can,
            "kg_per_can_case": kg_per_can_case,
        },
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


@st.cache_data(ttl=900, show_spinner=False)
def load_stock_history(period: str = "max") -> dict:
    """Daily close history for COKE from yfinance. period: 1y, 5y, max, etc."""
    t = yf.Ticker(TICKER)
    hist = t.history(period=period, interval="1d")
    if hist.empty:
        return {"dates": [], "close": []}
    return {
        "dates": [d.to_pydatetime() for d in hist.index],
        "close": [float(c) for c in hist["Close"]],
    }


@st.cache_data(ttl=300, show_spinner=False)
def load_intraday(period: str, interval: str) -> dict:
    """Intraday history for COKE. period e.g. '1d','5d','1mo' • interval e.g. '5m','30m','1h'."""
    t = yf.Ticker(TICKER)
    hist = t.history(period=period, interval=interval)
    if hist.empty:
        return {"dates": [], "close": []}
    return {
        "dates": [d.to_pydatetime() for d in hist.index],
        "close": [float(c) for c in hist["Close"]],
    }


@st.cache_data(ttl=86400, show_spinner=False)
def load_oil_quarterly() -> dict:
    """Quarterly close of WTI futures from yfinance, 2016-present."""
    t = yf.Ticker("CL=F")
    hist = t.history(start="2016-01-01", interval="3mo")
    if hist.empty:
        return {"quarters": [], "close": []}
    quarters = []
    for d in hist.index:
        q = (d.month - 1) // 3 + 1
        quarters.append(f"Q{q} {str(d.year)[-2:]}")
    return {"quarters": quarters, "close": [float(c) for c in hist["Close"]]}


def derive_cap_table(static: dict, live_price: float) -> dict:
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
