"""Scenario management — Bull/Base/Bear forecast overlays."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import streamlit as st

SCENARIOS_FILE = Path(__file__).parent / "data" / "scenarios.json"


@st.cache_data(show_spinner=False)
def load_scenarios_config() -> dict:
    return json.loads(SCENARIOS_FILE.read_text())


def apply_scenario(base_summary: dict, scenario_name: str) -> dict:
    """Return a summary dict for the requested scenario. Base = passthrough; Bull/Bear = override if populated."""
    cfg = load_scenarios_config()
    scen = cfg.get(scenario_name, {})

    if scen.get("use_model", False) or scenario_name == "Base":
        return base_summary

    out = copy.deepcopy(base_summary)
    overridden = False
    for key in ("revenue", "ebitda", "eps"):
        vals = scen.get(key)
        if isinstance(vals, list) and len(vals) == len(out.get(key, [])):
            out[key] = vals
            overridden = True

    out["_scenario_status"] = "live" if overridden else "todo"
    return out


def scenario_status(scenario_name: str) -> str:
    cfg = load_scenarios_config()
    scen = cfg.get(scenario_name, {})
    if scenario_name == "Base" or scen.get("use_model"):
        return "live"
    if any(isinstance(scen.get(k), list) for k in ("revenue", "ebitda", "eps")):
        return "live"
    return "todo"
