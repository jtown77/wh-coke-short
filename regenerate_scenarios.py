"""Capture a full model snapshot to data/snapshot.json.

The site reads this snapshot exclusively. The live Excel model is never opened during
normal page loads — only by this script when the owner clicks Refresh. That makes the
site robust to transient model issues (Bloomberg add-in unloaded, file mid-edit, etc.)
and keeps the deployed copy in sync with whatever was last refreshed and committed.

What gets captured:
  - cap_table_static: diluted shares, total debt, cash, NCI (model price too, though the
    site overlays live yfinance price on top)
  - per scenario (Bull/Base/Bear), by flipping Summary!D4: revenue, EBITDA, EBITDA margin,
    EPS and their YoY arrays for 2022-2029, full return scenarios (EPS-based and EBITDA-based),
    and the valuation rows
  - Segment Build tab (quarterly volume/price/YoY series) — captured once under Base
  - COGS Sensitivity tab (LME / midwest premium / all-in / CCK markup, etc.) — once under Base

Run from Site/:
    python regenerate_scenarios.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import win32com.client as win32

LIVE_MODEL = Path(
    r"C:\Users\JoshuaLehrman\Wolf Hill Capital Management LLC\Shared - Documents\Josh\COKE\Models\WH COKE Model v04.29.2026.xlsx"
)
SNAPSHOT_FILE = Path(__file__).parent / "data" / "snapshot.json"

SCENARIO_VALUES = [("Bull", "1 - Bull"), ("Base", "2 - Base"), ("Bear", "3 - Bear")]
YEAR_COLS = ["G", "H", "I", "J", "K", "L", "M", "N"]  # 2022-2029 on Summary

# Summary tab row numbers (1-indexed Excel rows)
SUMMARY_ROWS = {
    "revenue": 4,
    "revenue_yoy": 5,
    "ebitda": 12,
    "ebitda_margin": 13,
    "ebitda_yoy": 14,
    "eps": 22,
    "eps_yoy": 23,
}
VALUATION_ROWS = {
    "ev_sales": 30,
    "ev_ebitda": 33,
    "pe": 34,
    "shares_out": 36,
    "net_debt": 37,
    "adj_tev": 38,
}
RETURN_EPS_ROWS = {"Bull": 5, "Base": 6, "Bear": 7}
RETURN_EBITDA_ROWS = {"Bull": 11, "Base": 12, "Bear": 13}
RETURN_COLS = ["Q", "R", "S", "T", "U", "V"]  # metric, multiple, target, npv, ret, irr
RETURN_FIELDS = ["metric", "multiple", "target", "npv", "ret", "irr"]


def _num(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    # Excel error codes (#N/A, #NAME?, #REF!, etc.) come through COM as ~-2.1B sentinels.
    # Reject any obviously-impossible large negative number.
    if f < -1e9:
        return None
    return f


def _row(ws, row: int, cols: list[str]) -> list[float | None]:
    return [_num(ws.Range(f"{c}{row}").Value) for c in cols]


def capture_summary_scenario(ws_summary) -> dict:
    out = {k: _row(ws_summary, r, YEAR_COLS) for k, r in SUMMARY_ROWS.items()}
    out["valuation"] = {k: _row(ws_summary, r, YEAR_COLS) for k, r in VALUATION_ROWS.items()}
    return out


def capture_return_tables(ws_summary) -> tuple[list, list]:
    """Return EPS-based and EBITDA-based return scenario tables. The model's Summary tab
    shows all three scenarios at once in this region, independent of D4 — capture once."""
    return_eps = [
        {"label": label,
         **{f: _num(ws_summary.Range(f"{RETURN_COLS[i]}{RETURN_EPS_ROWS[label]}").Value)
            for i, f in enumerate(RETURN_FIELDS)}}
        for label in ("Bull", "Base", "Bear")
    ]
    return_ebitda = [
        {"label": label,
         **{f: _num(ws_summary.Range(f"{RETURN_COLS[i]}{RETURN_EBITDA_ROWS[label]}").Value)
            for i, f in enumerate(RETURN_FIELDS)}}
        for label in ("Bull", "Base", "Bear")
    ]
    return return_eps, return_ebitda


def capture_cap_table(ws_summary) -> dict:
    return {
        "price": _num(ws_summary.Range("D7").Value),
        "diluted_shares": _num(ws_summary.Range("D8").Value),
        "total_debt": _num(ws_summary.Range("D10").Value),
        "cash": _num(ws_summary.Range("D11").Value),
        "nci": _num(ws_summary.Range("D13").Value) or 0.0,
    }


def capture_segment_build(ws) -> dict:
    quarters = [ws.Range(f"{_col(c)}5").Value for c in range(5, 61)]

    def row(r: int) -> list:
        return [_num(ws.Range(f"{_col(c)}{r}").Value) for c in range(5, 61)]

    return {
        "quarters": quarters,
        "total_revenue": row(8),
        "total_cases": row(9),
        "total_cases_yoy": row(10),
        "sparkling_volume": row(12),
        "sparkling_volume_yoy": row(13),
        "sparkling_price": row(18),
        "sparkling_price_yoy": row(19),
        "still_volume": row(25),
        "still_volume_yoy": row(26),
        "still_price": row(31),
        "still_price_yoy": row(32),
    }


def capture_cogs_sensitivity(ws) -> dict:
    quarters = [ws.Range(f"{_col(c)}5").Value for c in range(5, 61)]

    def row(r: int) -> list:
        return [_num(ws.Range(f"{_col(c)}{r}").Value) for c in range(5, 61)]

    return {
        "quarters": quarters,
        "lme_price": row(14),
        "midwest_premium": row(15),
        "all_in_us_price": row(16),
        "cck_markup": row(17),
        "all_in_cost_per_kg": row(41),
        "aluminum_volume_kg_mm": row(40),
        "aluminum_spend_mm": row(42),
        "cases_in_cans_mm": row(27),
        "kg_per_total_case": row(37),
        "content": {
            "cans_per_case": _num(ws.Range("E33").Value),
            "grams_per_can": _num(ws.Range("E34").Value),
            "kg_per_can_case": _num(ws.Range("E35").Value),
        },
    }


def _col(idx_zero: int) -> str:
    """0-indexed column number → Excel letter (E=4, F=5, ...). Up to ZZ."""
    n = idx_zero + 1
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def main() -> int:
    if not LIVE_MODEL.exists():
        print(f"ERROR: live model not found at {LIVE_MODEL}", file=sys.stderr)
        return 1

    print("Launching Excel via COM...")
    excel = win32.gencache.EnsureDispatch("Excel.Application")
    # Visible=True coaxes Excel into loading installed add-ins (notably Bloomberg).
    # A hidden COM-launched Excel often skips add-in load, leaving =BDP/=BQL formulas
    # as errors which COM returns as large negative ints (-2146826273 etc.).
    excel.Visible = True
    excel.DisplayAlerts = False
    # Force Bloomberg add-in to be loaded if installed
    try:
        for ai in excel.AddIns2:
            if "Bloomberg" in (ai.Name or ""):
                if not ai.Installed:
                    ai.Installed = True
                print(f"  Add-in: {ai.Name} ({'loaded' if ai.Installed else 'not loaded'})")
    except Exception as e:
        print(f"  Add-in check skipped: {e}")

    snapshot: dict = {}
    wb = None
    try:
        print(f"Opening {LIVE_MODEL.name}...")
        wb = excel.Workbooks.Open(str(LIVE_MODEL), ReadOnly=False, UpdateLinks=0)
        ws_summary = wb.Worksheets("Summary")
        original_d4 = ws_summary.Range("D4").Value
        print(f"  D4 was: {original_d4!r}")

        # Initial settle — let Bloomberg fetch data after open
        excel.CalculateFullRebuild()
        time.sleep(3)

        def _set_d4_and_recalc(value: str, sleep_after: float = 2.0) -> None:
            for attempt in range(3):
                try:
                    ws_summary.Range("D4").Value = value
                    excel.CalculateFullRebuild()
                    try:
                        excel.CalculateUntilAsyncQueriesDone()
                    except Exception:
                        pass
                    time.sleep(sleep_after)
                    return
                except Exception as e:
                    print(f"    retry D4={value!r} (attempt {attempt+1}): {e}")
                    time.sleep(2)
            raise RuntimeError(f"failed to set D4={value!r} after 3 attempts")

        # Loop scenarios
        scen_data: dict[str, dict] = {}
        for label, value in SCENARIO_VALUES:
            print(f"  Setting D4 = {value!r} and recalculating...")
            _set_d4_and_recalc(value)
            scen_data[label] = capture_summary_scenario(ws_summary)
            r26 = scen_data[label]["revenue"][4]
            e26 = scen_data[label]["ebitda"][4]
            p26 = scen_data[label]["eps"][4]
            r26s = f"{r26:,.0f}M" if r26 is not None else "n/a"
            e26s = f"{e26:,.0f}M" if e26 is not None else "n/a"
            p26s = f"${p26:.2f}" if p26 is not None else "n/a"
            print(f"    {label}: rev 2026={r26s}  ebitda 2026={e26s}  eps 2026={p26s}")

        # Capture cap table + return tables once (D4=Base for clean state)
        _set_d4_and_recalc("2 - Base")
        cap_static = capture_cap_table(ws_summary)
        return_eps, return_ebitda = capture_return_tables(ws_summary)
        # Attach return tables to every scenario view (they're scenario-independent)
        for label in scen_data:
            scen_data[label]["return_eps"] = return_eps
            scen_data[label]["return_ebitda"] = return_ebitda
        px = cap_static.get("price")
        sh = cap_static.get("diluted_shares")
        px_str = f"${px:.2f}" if px is not None else "n/a"
        sh_str = f"{sh:.2f}M" if sh is not None else "n/a"
        print(f"  Cap table: {px_str} px / {sh_str} shares")

        # Segment Build + COGS Sensitivity (under Base)
        seg = capture_segment_build(wb.Worksheets("Segment Build"))
        cogs = capture_cogs_sensitivity(wb.Worksheets("COGS Sensitivity"))
        print(f"  Segment Build: {len(seg['quarters'])} quarters")
        print(f"  COGS Sensitivity: {len(cogs['quarters'])} quarters")

        # Restore original
        print(f"  Restoring D4 to {original_d4!r}")
        ws_summary.Range("D4").Value = original_d4
        excel.CalculateFullRebuild()

        # Close WITHOUT saving
        wb.Close(SaveChanges=False)
        wb = None
    finally:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        excel.Quit()

    snapshot = {
        "_note": "Full model snapshot — regenerate with regenerate_scenarios.py.",
        "_captured_at": datetime.now().isoformat(timespec="seconds"),
        "_model_name": LIVE_MODEL.name,
        "static": {
            "years": list(range(2022, 2030)),
            "cap_table_static": cap_static,
        },
        "scenarios": scen_data,
        "segment_build": seg,
        "cogs_sensitivity": cogs,
    }
    SNAPSHOT_FILE.write_text(json.dumps(snapshot, indent=2, default=str))
    print(f"\nWrote {SNAPSHOT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
