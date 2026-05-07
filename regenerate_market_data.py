"""Capture market data snapshot to data/market_data.json.

The deployed site reads this JSON instead of calling yfinance directly. Streamlit
Cloud's shared IP pool gets rate-limited by Yahoo Finance (yfinance.YFRateLimitError),
so live calls fail in cloud. This mirrors the snapshot.json pattern for the model.

Run from Site/ on the owner's machine (where yfinance works):
    python regenerate_market_data.py
"""
from __future__ import annotations

import json
import sys
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

    payload = {
        "_note": "Market data snapshot. Regenerate with regenerate_market_data.py.",
        "_captured_at": datetime.now().isoformat(timespec="seconds"),
        "live_price": live_price,
        "stock_history_1y": history,
        "commodities_daily_3y": commodities,
    }

    tmp = MARKET_DATA_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(MARKET_DATA_FILE)
    print(f"\nWrote {MARKET_DATA_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
