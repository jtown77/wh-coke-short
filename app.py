"""wh-coke-short — Wolf Hill COKE short thesis pitch site. Password-gated Streamlit app."""
from __future__ import annotations

import streamlit as st

import loaders
import sections

st.set_page_config(
    page_title="Wolf Hill — COKE Short Thesis",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _password_gate() -> bool:
    if st.session_state.get("authed"):
        return True

    st.markdown("# Wolf Hill — COKE Short Thesis")
    st.caption("Internal — password required")
    pw = st.text_input("Password", type="password", key="pw_input")
    if st.button("Enter", type="primary"):
        if pw == st.secrets.get("password"):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


def main() -> None:
    if not _password_gate():
        return

    summary = loaders.load_summary()
    seg = loaders.load_segment_build()
    cogs = loaders.load_cogs_sensitivity()
    live_price = loaders.load_live_price()
    cap = loaders.derive_cap_table(summary["cap_table_static"], live_price)

    st.markdown("# Coca-Cola Consolidated (COKE) — Short Thesis")
    st.caption("Wolf Hill Capital Management — internal")

    sections.render_snapshot(cap)
    st.divider()

    sections.render_summary_block(summary, cap)
    st.divider()

    sections.render_executive_summary()
    sections.render_thesis()
    st.divider()

    st.markdown("### Demand Elasticity — Sparkling Beverages")
    sections.render_elasticity(seg, "Sparkling")
    st.divider()

    st.markdown("### Demand Elasticity — Still Beverages")
    sections.render_elasticity(seg, "Still")
    st.divider()

    st.markdown("### Quarterly Y/Y Price & Volume Growth")
    sections.render_quarterly_yoy(seg)
    st.divider()

    sections.render_aluminum(cogs, summary, cap)


if __name__ == "__main__":
    main()
