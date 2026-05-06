"""Streamlit section renderers — each function builds one section of the page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import charts


def render_snapshot(cap: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price (COKE)", f"${cap['price']:.2f}")
    c2.metric("Market Cap", f"${cap['market_cap']:,.0f}M")
    c3.metric("Enterprise Value", f"${cap['enterprise_value']:,.0f}M")
    c4.metric("Net Debt", f"${cap['net_debt']:,.0f}M")


def _fmt_money(v, dec=0):
    if v is None or pd.isna(v):
        return ""
    return f"${v:,.{dec}f}"


def _fmt_pct(v, dec=1):
    if v is None or pd.isna(v):
        return ""
    return f"{v*100:.{dec}f}%"


def _fmt_x(v, dec=1):
    if v is None or pd.isna(v):
        return ""
    return f"{v:.{dec}f}x"


def render_summary_block(s: dict, cap: dict) -> None:
    st.markdown("### Financial Summary")
    years = s["years"]
    fin_df = pd.DataFrame({
        "": ["Revenue ($M)", "  YoY %", "EBITDA ($M)", "  Margin %", "  YoY %", "Adj. EPS ($)", "  YoY %"],
        **{
            str(y): [
                _fmt_money(s["revenue"][i], 0),
                _fmt_pct(s["revenue_yoy"][i]),
                _fmt_money(s["ebitda"][i], 0),
                _fmt_pct(s["ebitda_margin"][i]),
                _fmt_pct(s["ebitda_yoy"][i]),
                f"${s['eps'][i]:.2f}" if s["eps"][i] is not None else "",
                _fmt_pct(s["eps_yoy"][i]),
            ] for i, y in enumerate(years)
        }
    })
    st.dataframe(fin_df, hide_index=True, use_container_width=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Cap Table (Live)")
        cap_df = pd.DataFrame([
            ["Price (COKE)", f"${cap['price']:.2f}"],
            ["Diluted Shares (M)", f"{cap['diluted_shares']:.2f}"],
            ["Market Cap ($M)", f"${cap['market_cap']:,.0f}"],
            ["Total Debt ($M)", f"${cap['total_debt']:,.0f}"],
            ["Cash ($M)", f"${cap['cash']:,.0f}"],
            ["Net Debt ($M)", f"${cap['net_debt']:,.0f}"],
            ["NCI ($M)", f"${cap['nci']:,.0f}"],
            ["Enterprise Value ($M)", f"${cap['enterprise_value']:,.0f}"],
        ], columns=["", "Value"])
        st.dataframe(cap_df, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("#### Valuation Multiples (WH)")
        v = s["valuation"]
        val_rows = []
        for i, y in enumerate(v["years"]):
            val_rows.append([
                str(y),
                _fmt_x(v["ev_sales"][i], 2) if v["ev_sales"][i] else "",
                _fmt_x(v["ev_ebitda"][i], 1) if v["ev_ebitda"][i] else "",
                _fmt_x(v["pe"][i], 1) if v["pe"][i] else "",
            ])
        val_df = pd.DataFrame(val_rows, columns=["Year", "EV / Sales", "EV / EBITDA", "P / E"])
        st.dataframe(val_df, hide_index=True, use_container_width=True)

    st.markdown("#### 2026 YE Return Scenarios")
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        st.markdown("**EPS-based**")
        eps_df = pd.DataFrame([
            [r["label"], f"${r['metric']:.2f}", _fmt_x(r["multiple"], 0),
             f"${r['target']:.2f}", f"${r['npv']:.2f}",
             _fmt_pct(r["ret"]), _fmt_pct(r["irr"])]
            for r in s["return_eps"]
        ], columns=["Scenario", "EPS", "P/E", "Target", "NPV", "% Return", "IRR"])
        st.dataframe(eps_df, hide_index=True, use_container_width=True)

    with rcol2:
        st.markdown("**EBITDA-based**")
        eb_df = pd.DataFrame([
            [r["label"], f"${r['metric']:,.0f}M", _fmt_x(r["multiple"], 0),
             f"${r['target']:.2f}", f"${r['npv']:.2f}",
             _fmt_pct(r["ret"]), _fmt_pct(r["irr"])]
            for r in s["return_ebitda"]
        ], columns=["Scenario", "EBITDA", "EV/EBITDA", "Target", "NPV", "% Return", "IRR"])
        st.dataframe(eb_df, hide_index=True, use_container_width=True)


def render_executive_summary() -> None:
    st.markdown("### Executive Summary")
    st.info(
        "**Placeholder — to be drafted.** Replace this block with the executive summary paragraph "
        "framing the COKE short thesis (positioning, what's mispriced, time horizon, key catalyst)."
    )


def render_thesis() -> None:
    st.markdown("### Thesis")
    st.info(
        "**Placeholder — to be drafted.** Replace with bullet points covering "
        "(1) volume / price elasticity dynamics, (2) aluminum cost exposure, "
        "(3) margin compression mechanics, (4) valuation gap to fair value, "
        "(5) catalysts to realize the short."
    )


def render_elasticity(seg: dict, segment: str) -> None:
    if segment == "Sparkling":
        price = seg["sparkling_price_yoy"]
        vol = seg["sparkling_volume_yoy"]
        commentary = (
            "Sparkling is COKE's largest revenue contributor and the segment most exposed to "
            "consumer pushback on price. The negative slope here is the demand-elasticity story: "
            "as price increases moderate, volume should recover — but if pricing has to come down "
            "to defend volume, gross margin compresses."
        )
    else:
        price = seg["still_price_yoy"]
        vol = seg["still_volume_yoy"]
        commentary = (
            "Still beverages (water, sports drinks, juices) historically run at lower margins than "
            "sparkling and have shown more volatile volume response to pricing. A flatter or "
            "positive-sloping relationship here would suggest weaker pricing power than sparkling."
        )

    fig = charts.elasticity_scatter(price, vol, seg["quarters"], segment)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(commentary)


def render_quarterly_yoy(seg: dict) -> None:
    fig = charts.quarterly_yoy_chart(seg)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Six series across Sparkling, Still, and Total — solid lines for volume YoY, dashed "
        "for price YoY. Forecast period (Q1 2026 onward) reflects Wolf Hill's Base case for "
        "volume and price growth. The price-volume divergence post-2022 is the central observation: "
        "pricing carried revenue while volumes flattened or declined."
    )


def render_aluminum(cogs: dict, summary: dict, cap: dict) -> None:
    st.markdown("### Aluminum Sensitivity")

    # Historical price chart
    fig_hist = charts.aluminum_history_chart(
        cogs["quarters"], cogs["lme_price"], cogs["midwest_premium"], cogs["all_in_us_price"]
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # Compute base case for 2026
    quarters = cogs["quarters"]
    spend = cogs["aluminum_spend_mm"]
    all_in = cogs["all_in_us_price"]
    q26 = ["Q1 26", "Q2 26", "Q3 26", "Q4 26"]
    indices_26 = [quarters.index(q) for q in q26 if q in quarters]
    base_spend_2026 = sum(spend[i] for i in indices_26 if spend[i] is not None)
    base_all_in_2026 = sum(all_in[i] for i in indices_26 if all_in[i] is not None) / max(len(indices_26), 1)
    base_eps_2026 = summary["eps"][summary["years"].index(2026)]
    diluted_shares = cap["diluted_shares"]
    tax_rate = 0.25

    # Sensitivity curve
    fig_sens = charts.aluminum_sensitivity_curve(
        base_all_in_2026, base_spend_2026, base_eps_2026, diluted_shares, tax_rate
    )
    st.plotly_chart(fig_sens, use_container_width=True)

    # Interactive slider
    st.markdown("#### Try it: dial in an aluminum price assumption")
    c1, c2 = st.columns([2, 1])
    with c1:
        pct_change = st.slider(
            "Move from base case (%)",
            min_value=-50, max_value=50, value=0, step=5,
            help=f"Base case: ${base_all_in_2026:,.0f}/MT all-in",
        )
    new_price = base_all_in_2026 * (1 + pct_change / 100)
    new_spend = base_spend_2026 * (1 + pct_change / 100)
    delta_spend = new_spend - base_spend_2026
    delta_eps = -delta_spend * (1 - tax_rate) / diluted_shares
    new_eps = base_eps_2026 + delta_eps

    with c2:
        st.metric(
            "Implied 2026 EPS",
            f"${new_eps:.2f}",
            delta=f"${delta_eps:+.2f}" if pct_change != 0 else None,
        )

    st.caption(
        f"At ${new_price:,.0f}/MT all-in (vs base ${base_all_in_2026:,.0f}/MT), 2026 aluminum "
        f"spend changes by ${delta_spend:+,.0f}M, flowing through to a {delta_eps:+.2f} EPS impact "
        f"after a 25% tax assumption. Linear flow-through; ignores second-order effects "
        f"(D&A, share buyback timing, indirect cost pass-through)."
    )
