"""Scenario selection — Bull / Base / Bear all read from data/snapshot.json."""
from __future__ import annotations

import loaders


def apply_scenario(_unused: dict, scenario_name: str) -> dict:
    """Return summary dict for the chosen scenario by re-loading from snapshot."""
    return loaders.load_summary(scenario_name)


def scenario_status(scenario_name: str) -> str:
    """All three scenarios are first-class snapshot reads now."""
    snap = loaders.load_snapshot()
    return "live" if scenario_name in snap.get("scenarios", {}) else "todo"
