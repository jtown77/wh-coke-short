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
ADJ_CASH_EPS_COLS = ["BQ", "BR", "BS", "BT", "BU", "BV", "BW", "BX"]  # 2022-2029 adj. cash EPS

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
ADJ_CASH_EPS_ROW = 52  # Summary!BQ52:BX52
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


def capture_summary_scenario(ws_summary, ws_wh_model=None) -> dict:
    out = {k: _row(ws_summary, r, YEAR_COLS) for k, r in SUMMARY_ROWS.items()}
    # Adj. Cash EPS lives on WH Model!BQ52:BX52 (labels at WH Model!row 5, B52 = "Adj. Cash EPS")
    if ws_wh_model is not None:
        out["adj_cash_eps"] = _row(ws_wh_model, ADJ_CASH_EPS_ROW, ADJ_CASH_EPS_COLS)
    else:
        out["adj_cash_eps"] = [None] * len(YEAR_COLS)
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

    # Still-segment row mapping audited 2026-05-08 against the Segment Build tab:
    # R12/R13 sparkling volume + YoY, R18/R19 sparkling price + YoY,
    # R30/R31 still volume + YoY, R36/R37 still price + YoY.
    # (Old script used R25/R26/R31/R32 for still — those are sparkling Adj rows
    # which are mostly empty, so still_* was returning None across the board.)
    out = {
        "quarters": quarters,
        "total_revenue": row(8),
        "total_cases": row(9),
        "total_cases_yoy": row(10),
        "sparkling_volume": row(12),
        "sparkling_volume_yoy": row(13),
        "sparkling_price": row(18),
        "sparkling_price_yoy": row(19),
        "still_volume": row(30),
        "still_volume_yoy": row(31),
        "still_price": row(36),
        "still_price_yoy": row(37),
    }

    # Q1 26 calendar adjustment — model has one fewer selling day vs Q1 25, so
    # the raw sparkling/still rows overstate Q1 26. The Adj rows in the model
    # (R25 sparkling vol, R26 sparkling pricing yoy, R27 sparkling vol yoy;
    # R43 still vol, R44 still pricing yoy, R45 still vol yoy) carry the
    # calendar-adjusted values. Overlay them onto the raw fields when present.
    try:
        i = quarters.index("Q1 26")
    except ValueError:
        i = None
    if i is not None:
        adj_sp_rev = row(24)[i]
        adj_sp_vol = row(25)[i]
        adj_sp_pyoy = row(26)[i]
        adj_sp_vyoy = row(27)[i]
        adj_st_rev = row(42)[i]
        adj_st_vol = row(43)[i]
        adj_st_pyoy = row(44)[i]
        adj_st_vyoy = row(45)[i]
        if adj_sp_vol is not None:
            out["sparkling_volume"][i] = adj_sp_vol
        if adj_sp_rev is not None and adj_sp_vol:
            out["sparkling_price"][i] = adj_sp_rev / adj_sp_vol
        if adj_sp_pyoy is not None:
            out["sparkling_price_yoy"][i] = adj_sp_pyoy
        if adj_sp_vyoy is not None:
            out["sparkling_volume_yoy"][i] = adj_sp_vyoy
        if adj_st_vol is not None:
            out["still_volume"][i] = adj_st_vol
        if adj_st_rev is not None and adj_st_vol:
            out["still_price"][i] = adj_st_rev / adj_st_vol
        if adj_st_pyoy is not None:
            out["still_price_yoy"][i] = adj_st_pyoy
        if adj_st_vyoy is not None:
            out["still_volume_yoy"][i] = adj_st_vyoy
    return out


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
        "cases_in_bottles_mm": row(28),
        "pct_volume_cans": row(25),
        "pct_volume_bottles": row(26),
        "kg_per_total_case": row(37),
        "pet_cost_per_mt_raw": row(45),       # Bloomberg PUSAPEBG Index, quarterly avg
        "pet_markup_per_mt": row(46),         # raw * 1.5 (bottler markup)
        "pet_volume_mm_kg": row(54),
        "pet_spend_mm": row(55),
        "content": {
            "cans_per_case": _num(ws.Range("E33").Value),
            "grams_per_can": _num(ws.Range("E34").Value),
            "kg_per_can_case": _num(ws.Range("E35").Value),
            "pet_g_per_oz": _num(ws.Range("E50").Value),
            "pet_kg_per_bottle_case": _num(ws.Range("E51").Value),
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
    last_err = None
    excel = None
    for attempt in range(5):
        try:
            excel = win32.DispatchEx("Excel.Application")
            break
        except Exception as e:
            last_err = e
            print(f"  DispatchEx attempt {attempt + 1}/5 failed: {e}")
            time.sleep(2)
    if excel is None:
        print(f"ERROR: could not launch Excel via COM after 5 retries: {last_err}", file=sys.stderr)
        return 1

    # Visible=True coaxes Excel into loading installed add-ins (notably Bloomberg).
    # A hidden COM-launched Excel often skips add-in load, leaving =BDP/=BQL formulas
    # as errors which COM returns as large negative ints (-2146826273 etc.).
    # If the property put fails (Excel desktop session restricted, etc.), continue and
    # rely on the explicit AddIns2 load below.
    for attempt in range(3):
        try:
            excel.Visible = True
            break
        except Exception as e:
            print(f"  Visible=True attempt {attempt + 1}/3 failed: {e}")
            time.sleep(1.5)
    try:
        excel.DisplayAlerts = False
    except Exception as e:
        print(f"  DisplayAlerts=False failed (continuing): {e}")
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
        ws_wh_model = wb.Worksheets("WH Model")
        original_d4 = ws_summary.Range("D4").Value
        print(f"  D4 was: {original_d4!r}")

        # Initial settle — let Bloomberg fetch data after open. Tolerate Bloomberg
        # being offline: the BDP cells will hold #N/A, but every other static
        # range (volumes, percentages, content cells) still reads correctly.
        try:
            excel.CalculateFullRebuild()
        except Exception as e:
            print(f"  CalculateFullRebuild failed (likely Bloomberg offline): {e}")
        time.sleep(3)

        def _set_d4_and_recalc(value: str, sleep_after: float = 2.0) -> None:
            for attempt in range(3):
                try:
                    ws_summary.Range("D4").Value = value
                    try:
                        excel.CalculateFullRebuild()
                    except Exception as rebuild_err:
                        print(f"    CalculateFullRebuild failed on D4={value!r}: {rebuild_err}")
                        # Fall back to a lighter recalc that won't choke on BBG #N/A.
                        try:
                            excel.Calculate()
                        except Exception:
                            pass
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
            # Bloomberg async queries take time to settle, especially after the first D4 flip.
            # Retry up to 4 times with increasing sleeps if EBITDA/EPS come back None.
            captured = None
            for attempt in range(4):
                sleep_for = 3.0 + 2.0 * attempt  # 3s, 5s, 7s, 9s
                _set_d4_and_recalc(value, sleep_after=sleep_for)
                captured = capture_summary_scenario(ws_summary, ws_wh_model)
                if captured["ebitda"][4] is not None and captured["eps"][4] is not None:
                    break
                print(f"    Bloomberg not settled yet (attempt {attempt+1}/4), retrying...")
            scen_data[label] = captured
            r26 = scen_data[label]["revenue"][4]
            e26 = scen_data[label]["ebitda"][4]
            p26 = scen_data[label]["eps"][4]
            ce26 = scen_data[label]["adj_cash_eps"][4]
            r26s = f"{r26:,.0f}M" if r26 is not None else "n/a"
            e26s = f"{e26:,.0f}M" if e26 is not None else "n/a"
            p26s = f"${p26:.2f}" if p26 is not None else "n/a"
            ce26s = f"${ce26:.2f}" if ce26 is not None else "n/a"
            print(f"    {label}: rev 2026={r26s}  ebitda 2026={e26s}  eps 2026={p26s}  cash eps 2026={ce26s}")

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

    # Validate: every scenario must have non-None targets/rets across return_eps
    # and return_ebitda. If any are None, abort the write so a transient Bloomberg
    # calc-timing miss can't corrupt the saved snapshot.
    bad = []
    for sname, sdata in snapshot["scenarios"].items():
        for kind in ("return_eps", "return_ebitda"):
            for row in sdata.get(kind, []):
                if row.get("target") is None or row.get("ret") is None:
                    bad.append(f"{sname}/{kind}/{row.get('label')}")
    if bad:
        print(f"\nERROR: refusing to write snapshot — incomplete capture for: {', '.join(bad)}",
              file=sys.stderr)
        print("Existing snapshot.json on disk left untouched.", file=sys.stderr)
        return 1

    # Atomic write: temp file + rename, so a crash mid-write can't truncate the live file
    tmp = SNAPSHOT_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(snapshot, indent=2, default=str))
    tmp.replace(SNAPSHOT_FILE)
    print(f"\nWrote {SNAPSHOT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
