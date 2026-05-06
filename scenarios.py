"""Scenario management — Bull/Base/Bear forecast overlays.

Base reads live from the model. Bull/Bear are captured into data/scenarios.json by the
regenerate_scenarios.py COM script, which flips Summary!D4 to recalculate the model.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import streamlit as st

SCENARIOS_FILE = Path(__file__).parent / "data" / "scenarios.json"


def _scenarios_mtime() -> float:
    try:
        return SCENARIOS_FILE.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def load_scenarios_config() -> dict:
    return _load_scenarios_cached(_scenarios_mtime())


@st.cache_data(show_spinner=False)
def _load_scenarios_cached(_mtime: float) -> dict:
    return json.loads(SCENARIOS_FILE.read_text())


def _yoy(arr: list) -> list:
    out: list = [None]
    for i in range(1, len(arr)):
        prev = arr[i - 1]
        cur = arr[i]
        if prev and prev != 0 and cur is not None:
            out.append(cur / prev - 1)
        else:
            out.append(None)
    return out


def apply_scenario(base_summary: dict, scenario_name: str) -> dict:
    """Return summary dict for the chosen scenario. Base = live model passthrough; Bull/Bear use overrides."""
    cfg = load_scenarios_config()
    scen = cfg.get(scenario_name, {})

    if scen.get("use_model", False) or scenario_name == "Base":
        return base_summary

    rev = scen.get("revenue")
    ebitda = scen.get("ebitda")
    eps = scen.get("eps")
    if not (isinstance(rev, list) and isinstance(ebitda, list) and isinstance(eps, list)):
        return base_summary

    out = copy.deepcopy(base_summary)
    out["revenue"] = rev
    out["ebitda"] = ebitda
    out["eps"] = eps
    out["revenue_yoy"] = _yoy(rev)
    out["ebitda_yoy"] = _yoy(ebitda)
    out["eps_yoy"] = _yoy(eps)
    out["ebitda_margin"] = [
        (e / r) if (r and r != 0) else None for e, r in zip(ebitda, rev)
    ]
    return out


def scenario_status(scenario_name: str) -> str:
    cfg = load_scenarios_config()
    scen = cfg.get(scenario_name, {})
    if scenario_name == "Base" or scen.get("use_model"):
        return "live"
    if isinstance(scen.get("revenue"), list) and isinstance(scen.get("ebitda"), list) and isinstance(scen.get("eps"), list):
        return "live"
    return "todo"
