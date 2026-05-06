"""wh-coke-short — Wolf Hill COKE short thesis pitch site. Password-gated Streamlit app."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

import loaders
import scenarios as scen
import sections

st.set_page_config(
    page_title="Wolf Hill — COKE Short Thesis",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed",
)


_EDITORIAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+Pro:wght@400;600;700&family=Source+Sans+Pro:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Source Sans Pro', sans-serif;
    color: #1a2230;
}

.main .block-container {
    max-width: 1180px;
    padding-top: 1.6rem;
    padding-bottom: 4rem;
}

h1, h2, h3, h4, h5 {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    color: #1a2230 !important;
    letter-spacing: -0.01em;
}
h1 { font-size: 2.4rem !important; font-weight: 700 !important; line-height: 1.15; }
h2 { font-size: 1.6rem !important; font-weight: 600 !important; margin-top: 1.6rem !important; }
h3 { font-size: 1.25rem !important; font-weight: 600 !important; margin-top: 1.4rem !important; }
h4 { font-size: 1.0rem !important; font-weight: 600 !important; color: #303f55 !important; margin-top: 1rem !important; }
h5 { font-size: 0.92rem !important; font-weight: 600 !important; color: #5e6e85 !important; text-transform: uppercase; letter-spacing: 0.06em; }

.eyebrow {
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #8b95a3;
    margin-bottom: 0.4rem;
}

hr {
    margin: 2rem 0 !important;
    border: none !important;
    border-top: 1px solid #e7eaef !important;
}

[data-testid="stCaptionContainer"], .stCaption, .caption, [data-testid="stMarkdownContainer"] em {
    font-size: 0.92rem !important;
    color: #5e6e85 !important;
    line-height: 1.55;
}

[data-testid="stMetric"] {
    background: #fafbfc;
    border-left: 3px solid #303f55;
    padding: 0.7rem 0.9rem;
    border-radius: 4px;
}
[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
    color: #5e6e85 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    font-size: 1.6rem !important;
    color: #1a2230 !important;
}

[data-testid="stRadio"] > div { gap: 0.4rem; }
[data-testid="stRadio"] label {
    background: #fafbfc;
    border: 1px solid #e7eaef;
    padding: 0.45rem 1rem;
    border-radius: 999px;
    transition: all 0.12s ease;
}
[data-testid="stRadio"] label:hover {
    border-color: #303f55;
}

.dataframe, [data-testid="stDataFrame"] {
    font-size: 0.92rem;
}

button[kind="primary"] {
    background: #303f55 !important;
    border: none !important;
}

.brand-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #303f55;
    padding-bottom: 0.6rem;
    margin-bottom: 1.4rem;
}
.brand-bar .left {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-weight: 700;
    font-size: 1.05rem;
    color: #303f55;
    letter-spacing: 0.02em;
}
.brand-bar .right {
    font-size: 0.82rem;
    color: #8b95a3;
}
</style>
"""


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
    st.markdown(_EDITORIAL_CSS, unsafe_allow_html=True)
    if not _password_gate():
        return

    summary_base = loaders.load_summary()
    seg = loaders.load_segment_build()
    cogs = loaders.load_cogs_sensitivity()
    oil = loaders.load_oil_quarterly()
    live_price = loaders.load_live_price()
    cap = loaders.derive_cap_table(summary_base["cap_table_static"], live_price)

    today = datetime.now().strftime("%B %-d, %Y") if hasattr(datetime, "now") else "Today"
    try:
        today = datetime.now().strftime("%B %d, %Y").replace(" 0", " ")
    except Exception:
        today = "Today"

    st.markdown(
        f'<div class="brand-bar"><div class="left">WOLF HILL CAPITAL MANAGEMENT</div>'
        f'<div class="right">Internal Research • {today}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="eyebrow">Equity Short Thesis</div>', unsafe_allow_html=True)
    st.markdown("# Coca-Cola Consolidated (NASDAQ: COKE)")
    st.markdown(
        '<p style="font-size:1.05rem;color:#5e6e85;margin-top:-0.4rem;line-height:1.5;">'
        'Largest U.S. Coca-Cola bottler. Margin tailwinds reversing as commodity costs and pricing-volume '
        'tradeoffs squeeze 2026-2029 earnings.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    sections.render_snapshot(cap)
    st.markdown("")

    # Scenario selector
    st.markdown('<div class="eyebrow">Scenario</div>', unsafe_allow_html=True)
    chosen_scenario = sections.render_scenario_selector()
    summary = scen.apply_scenario(summary_base, chosen_scenario)

    st.markdown("---")
    sections.render_summary_block(summary, cap)

    st.markdown("---")
    sections.render_executive_summary()
    sections.render_thesis()

    st.markdown("---")
    st.markdown('<div class="eyebrow">Demand & Pricing</div>', unsafe_allow_html=True)
    st.markdown("## Volume vs. Price — Where the Pressure Sits")
    sections.render_elasticity(seg, "Sparkling", figure_num=1)
    st.markdown("")
    sections.render_elasticity(seg, "Still", figure_num=2)
    st.markdown("")
    sections.render_quarterly_yoy(seg, figure_num=3)

    st.markdown("---")
    st.markdown('<div class="eyebrow">Cost Stack</div>', unsafe_allow_html=True)
    st.markdown("## Commodity Exposure — Aluminum and Oil")
    sections.render_commodity_stack(cogs, oil, figure_num=4)
    st.markdown("")
    sections.render_aluminum_sensitivity(cogs, summary, cap, figure_num=5)


if __name__ == "__main__":
    main()
