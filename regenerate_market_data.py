"""Capture market data snapshot to data/market_data.json.

The deployed site reads this JSON instead of calling yfinance directly. Streamlit
Cloud's shared IP pool gets rate-limited by Yahoo Finance (yfinance.YFRateLimitError),
so live calls fail in cloud. This mirrors the snapshot.json pattern for the model.

Run from Site/ on the owner's machine (where yfinance works):
    python regenerate_market_data.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

MARKET_DATA_FILE = Path(__file__).parent / "data" / "market_data.json"
TICKER = "COKE"


def fetch_live_price() -> float:
    t = yf.Ticker(TICKER)
    info = t.info
    p = info.get("regularMarketPrice") or info.get("currentPrice")
    if p is None:
        hist = t.history(period="1d")
        p = float(hist["Close"].iloc[-1])
    return float(p)


def fetch_stock_history(period: str = "1y") -> dict:
    t = yf.Ticker(TICKER)
    hist = t.history(period=period, interval="1d")
    if hist.empty:
        return {"dates": [], "close": []}
    return {
        "dates": [d.strftime("%Y-%m-%dT%H:%M:%S") for d in hist.index],
        "close": [float(c) for c in hist["Close"]],
    }


def fetch_commodities_daily(years: int = 3) -> dict:
    start = (datetime.utcnow() - timedelta(days=int(years * 365.25) + 30)).strftime("%Y-%m-%d")

    al = yf.Ticker("ALI=F").history(start=start, interval="1d")
    wti = yf.Ticker("CL=F").history(start=start, interval="1d")

    al_dates = [d.strftime("%Y-%m-%d") for d in al.index] if not al.empty else []
    al_close_mt = [float(c) for c in al["Close"]] if not al.empty else []

    wti_dates = [d.strftime("%Y-%m-%d") for d in wti.index] if not wti.empty else []
    wti_close = [float(c) for c in wti["Close"]] if not wti.empty else []

    return {
        "aluminum": {"dates": al_dates, "close_per_mt": al_close_mt},
        "wti": {"dates": wti_dates, "close_per_bbl": wti_close},
    }


def fetch_core_cpi_quarterly(start_year: int = 2018) -> dict:
    """Core CPI (CPILFESL) from FRED, monthly SA, averaged to quarterly.

    Anchored at start_year so we have a Q1 baseline before Q1 2019.
    """
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPILFESL"
    with urllib.request.urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8")

    monthly = {}  # YYYY-MM -> value
    reader = csv.DictReader(io.StringIO(text))
    for r in reader:
        d = r.get("observation_date") or r.get("DATE")
        v = r.get("CPILFESL")
        if not d or not v or v == ".":
            continue
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            continue
        if dt.year < start_year:
            continue
        monthly[(dt.year, dt.month)] = float(v)

    def _shift(ym, delta):
        y, m = ym
        idx = y * 12 + (m - 1) + delta
        return (idx // 12, idx % 12 + 1)

    for ym in list(monthly.keys()):
        gap = _shift(ym, 1)
        after = _shift(ym, 2)
        if gap not in monthly and after in monthly:
            monthly[gap] = (monthly[ym] + monthly[after]) / 2

    quarters = []
    values = []
    for year in range(start_year, datetime.utcnow().year + 1):
        for q in range(1, 5):
            months = [(year, m) for m in (q * 3 - 2, q * 3 - 1, q * 3)]
            vals = [monthly[m] for m in months if m in monthly]
            if len(vals) == 3:
                quarters.append(f"Q{q} {str(year)[-2:]}")
                values.append(sum(vals) / 3)
    return {"quarters": quarters, "core_cpi": values}


def fetch_diesel_weekly() -> dict:
    """US Weekly Retail Diesel #2 ($/gal) from FRED GASDESW (sourced from EIA).

    Returns full series so the chart layer can do its own truncation.
    """
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GASDESW"
    with urllib.request.urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    dates = []
    values = []
    reader = csv.DictReader(io.StringIO(text))
    for r in reader:
        d = r.get("observation_date") or r.get("DATE")
        v = r.get("GASDESW")
        if not d or not v or v == ".":
            continue
        try:
            float(v)
        except ValueError:
            continue
        dates.append(d)
        values.append(float(v))
    return {"dates": dates, "price_per_gal": values, "latest": values[-1] if values else None}


def main() -> int:
    print(f"Fetching {TICKER} live price...")
    live_price = fetch_live_price()
    print(f"  ${live_price:.2f}")

    print(f"Fetching {TICKER} 1y daily history...")
    history = fetch_stock_history(period="1y")
    print(f"  {len(history['dates'])} bars")

    print("Fetching aluminum + WTI 3y daily...")
    commodities = fetch_commodities_daily(years=3)
    print(f"  ALI=F: {len(commodities['aluminum']['dates'])} bars, "
          f"CL=F: {len(commodities['wti']['dates'])} bars")

    print("Fetching Core CPI (CPILFESL) from FRED...")
    cpi = fetch_core_cpi_quarterly(start_year=2018)
    print(f"  {len(cpi['quarters'])} quarters: {cpi['quarters'][0]} – {cpi['quarters'][-1]}")

    print("Fetching US weekly retail diesel (GASDESW) from FRED...")
    diesel = fetch_diesel_weekly()
    print(f"  {len(diesel['dates'])} weekly bars; latest ${diesel['latest']:.3f}/gal")

    payload = {
        "_note": "Market data snapshot. Regenerate with regenerate_market_data.py.",
        "_captured_at": datetime.now().isoformat(timespec="seconds"),
        "live_price": live_price,
        "stock_history_1y": history,
        "commodities_daily_3y": commodities,
        "core_cpi_quarterly": cpi,
        "diesel_weekly": diesel,
    }

    tmp = MARKET_DATA_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(MARKET_DATA_FILE)
    print(f"\nWrote {MARKET_DATA_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
