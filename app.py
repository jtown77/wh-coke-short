"""wh-coke-short — Wolf Hill COKE short thesis pitch site. Password-gated Streamlit app."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

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
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* Lock layout — narrow viewports get horizontal scroll, not compressed content */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
    min-width: 1180px;
}

.stApp, body {
    background: #FBF8F3 !important;
    font-family: 'Inter', sans-serif;
    color: #1A1A1A;
    font-feature-settings: 'tnum' 1, 'lnum' 1;
}
[data-testid="stHeader"] { background: transparent; }

/* Match handle-shift exactly: 1180px max-width + Streamlit's default 5rem (80px)
   horizontal padding on each side, so content area is ~1020px with breathing room */
.stMain .block-container, .block-container {
    max-width: 1180px !important;
    min-width: 1180px !important;
    padding-top: 4rem !important;
    padding-bottom: 6rem !important;
    padding-left: 9rem !important;
    padding-right: 9rem !important;
}

/* Headlines — Source Serif 4 */
h1 {
    font-family: 'Source Serif 4', serif !important;
    font-weight: 700 !important;
    font-size: clamp(40px, 6vw, 56px) !important;
    line-height: 1.04 !important;
    letter-spacing: -0.02em !important;
    color: #1A1A1A !important;
    margin: 0 0 16px !important;
    padding: 0 !important;
}
h2 {
    font-family: 'Source Serif 4', serif !important;
    font-weight: 600 !important;
    font-size: 32px !important;
    line-height: 1.2 !important;
    letter-spacing: -0.01em !important;
    color: #1A1A1A !important;
    margin: 0 0 12px !important;
}
h3 {
    font-family: 'Source Serif 4', serif !important;
    font-weight: 600 !important;
    font-size: 22px !important;
    line-height: 1.3 !important;
    color: #1A1A1A !important;
    margin: 8px 0 12px !important;
}
h4 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 11px !important;
    letter-spacing: 0.20em !important;
    text-transform: uppercase !important;
    color: #303F55 !important;
    margin: 24px 0 10px !important;
}
h5 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 10px !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: #6B6B6B !important;
    margin: 16px 0 8px !important;
}

/* Editorial atoms */
.eyebrow {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    color: #303F55;
    margin-bottom: 12px;
}
.dek {
    font-family: 'Source Serif 4', serif;
    font-style: italic;
    font-weight: 400;
    font-size: 22px;
    line-height: 1.45;
    color: #4A4A4A;
    max-width: 760px;
    margin: 0 0 28px;
}
.byline {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 500;
    color: #6B6B6B;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    border-top: 1px solid #E5E0D8;
    border-bottom: 1px solid #E5E0D8;
    padding: 12px 0;
    margin: 0 0 36px;
}

/* Brand bar (small masthead row) */
.brand-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #E5E0D8;
    padding-bottom: 14px;
    margin-bottom: 28px;
}
.brand-bar .left {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #303F55;
}
.brand-bar .right {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: #6B6B6B;
}

/* Captions */
[data-testid="stCaptionContainer"], .stCaption, .caption,
[data-testid="stMarkdownContainer"] em {
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    line-height: 1.55 !important;
    color: #4A4A4A !important;
    font-style: italic !important;
}

/* Plotly chart card */
.stPlotlyChart {
    background: #FFFFFF;
    padding: 20px 16px 16px;
    border: 1px solid #E5E0D8;
    overflow: hidden;
    margin-bottom: 8px;
}
.stPlotlyChart .modebar-container { display: none !important; }
/* Force pointer/default cursor across the plot — no drag, no crosshair */
.stPlotlyChart .nsewdrag,
.stPlotlyChart .drag,
.stPlotlyChart .cursor-pointer,
.stPlotlyChart .cursor-crosshair,
.stPlotlyChart .cursor-ew-resize,
.stPlotlyChart .cursor-ns-resize,
.stPlotlyChart .cursor-move,
.stPlotlyChart .js-plotly-plot,
.stPlotlyChart .plot-container { cursor: default !important; }

/* Scenario radio */
[data-testid="stRadio"] > div { gap: 0.4rem; }
[data-testid="stRadio"] label {
    background: #FFFFFF !important;
    border: 1px solid #E5E0D8 !important;
    padding: 0.45rem 1rem !important;
    border-radius: 0 !important;
    transition: all 0.12s ease;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #1A1A1A !important;
}
[data-testid="stRadio"] label:hover { border-color: #303F55 !important; }

/* Buttons */
.stButton button {
    background: #1A1A1A !important;
    color: #FFFFFF !important;
    border: 1px solid #1A1A1A !important;
    border-radius: 0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
button[kind="primary"] {
    background: #1A1A1A !important;
    border: 1px solid #1A1A1A !important;
    border-radius: 0 !important;
}

/* Info / alert blocks */
[data-testid="stAlert"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E0D8 !important;
    border-left: 3px solid #303F55 !important;
    border-radius: 0 !important;
    color: #4A4A4A !important;
    font-family: 'Inter', sans-serif !important;
}

/* HR */
hr {
    margin: 2.5rem 0 !important;
    border: none !important;
    border-top: 1px solid #E5E0D8 !important;
}

/* Slider */
[data-testid="stSlider"] [role="slider"] { background: #303F55 !important; }
</style>
"""


def _password_gate() -> bool:
    if st.session_state.get("authed"):
        return True

    st.markdown(
        """
        <style>
        .gate-eyebrow {
            font-family: 'Inter', sans-serif; font-weight: 600; font-size: 11px;
            letter-spacing: 0.20em; text-transform: uppercase; color: #303F55;
            text-align: center; margin-bottom: 16px;
        }
        .gate-title {
            font-family: 'Source Serif 4', serif; font-weight: 700;
            font-size: clamp(40px, 6vw, 56px); line-height: 1.04; letter-spacing: -0.02em;
            color: #1A1A1A; text-align: center; margin: 0 0 12px;
        }
        p.gate-dek {
            font-family: 'Source Serif 4', serif !important;
            font-style: italic !important;
            font-size: 20px !important; line-height: 1.45 !important;
            color: #4A4A4A !important;
            text-align: center !important;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-bottom: 36px !important;
            max-width: 560px !important;
        }
        img.gate-meme {
            display: block !important;
            margin: 0 auto 36px !important;
            width: 100% !important;
            max-width: 480px !important;
            border: 1px solid #E5E0D8 !important;
            height: auto !important;
        }
        .gate-form {
            max-width: 420px; margin: 0 auto;
        }
        .gate-form [data-testid="stTextInput"] input {
            background: #1A1A1A !important; color: #FFFFFF !important;
            border: 1px solid #1A1A1A !important; border-radius: 0 !important;
            font-family: 'Inter', sans-serif !important; font-size: 14px !important;
            padding: 14px 16px !important;
        }
        .gate-form [data-testid="stTextInput"] input::placeholder { color: #6B6B6B !important; }
        .gate-form .stButton button {
            width: 100%;
            background: #1A1A1A !important; color: #FFFFFF !important;
            border: 1px solid #1A1A1A !important; border-radius: 0 !important;
            padding: 12px 16px !important;
            font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
            font-size: 12px !important; letter-spacing: 0.16em !important;
            text-transform: uppercase !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="gate-eyebrow">Restricted</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="gate-title">Coca-Cola Consolidated</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="gate-dek">Squeezed from both ends — demand softness up front, '
        'commodity costs through the back. Enter the password to read the thesis.</p>',
        unsafe_allow_html=True,
    )

    meme_path = Path(__file__).parent / "assets" / "coke_squeezed_meme.png"
    if meme_path.exists():
        import base64
        b64 = base64.b64encode(meme_path.read_bytes()).decode("ascii")
        st.markdown(
            f'<img src="data:image/png;base64,{b64}" class="gate-meme" alt="COKE squeezed from both ends">',
            unsafe_allow_html=True,
        )

    # Center the form using columns
    left, center, right = st.columns([1, 2, 1])
    with center:
        pw = st.text_input("Password", type="password", key="pw_input",
                           label_visibility="collapsed", placeholder="Password")
        if st.button("Enter", type="primary", use_container_width=True):
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
    history = loaders.load_stock_history(period="1y")

    now = datetime.now()
    today = f"{now.strftime('%B')} {now.day}, {now.year}"

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

    sections.render_forecast_cone(history, cap, summary_base)

    st.markdown("---")

    # Scenario selector — radio sits below the divider
    st.markdown('<div class="eyebrow">Scenario</div>', unsafe_allow_html=True)
    chosen_scenario = sections.render_scenario_selector()
    summary = scen.apply_scenario(summary_base, chosen_scenario)

    sections.render_summary_block(summary, cap)
    sections.render_refresh_block()

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
