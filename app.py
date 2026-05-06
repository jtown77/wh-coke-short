"""wh-coke-short — Wolf Hill COKE short thesis pitch site. Password-gated Streamlit app."""
from __future__ import annotations

import streamlit as st

import loaders

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

    st.markdown("# Coca-Cola Consolidated (COKE) — Short Thesis")
    st.caption("Wolf Hill Capital Management — internal")

    summary = loaders.load_summary()
    live_price = loaders.load_live_price()
    cap_table = loaders.derive_cap_table(summary["cap_table_static"], live_price)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price", f"${cap_table['price']:.2f}")
    c2.metric("Market Cap", f"${cap_table['market_cap']:,.0f}M")
    c3.metric("Enterprise Value", f"${cap_table['enterprise_value']:,.0f}M")
    c4.metric("Net Debt", f"${cap_table['net_debt']:,.0f}M")

    st.info("Phase 1 scaffold loaded. Sections coming online in Phase 2.")


if __name__ == "__main__":
    main()
