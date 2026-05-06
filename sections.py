"""Streamlit section renderers — each function builds one section of the page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import charts
import scenarios as scen


def render_snapshot(cap: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price (COKE)", f"${cap['price']:.2f}")
    c2.metric("Market Cap", f"${cap['market_cap']:,.0f}M")
    c3.metric("Enterprise Value", f"${cap['enterprise_value']:,.0f}M")
    c4.metric("Net Debt", f"${cap['net_debt']:,.0f}M")


def render_scenario_selector() -> str:
    import subprocess
    import sys
    from pathlib import Path

    import loaders

    options = ["Base", "Bull", "Bear"]
    statuses = {opt: scen.scenario_status(opt) for opt in options}
    labels = [f"{o}" + (" • TODO" if statuses[o] == "todo" else "") for o in options]
    label_to_opt = dict(zip(labels, options))

    chosen_label = st.radio(
        "Scenario",
        options=labels,
        horizontal=True,
        index=0,
        key="scenario_selector",
        label_visibility="collapsed",
    )

    if loaders.LIVE_MODEL.exists():
        if st.button("↻ Refresh Bull / Bear from live model",
                     help="Opens Excel via COM, flips Summary!D4 to capture each scenario, writes scenarios.json."):
            with st.spinner("Flipping scenario switch in Excel — this takes ~10 seconds..."):
                script = Path(__file__).parent / "regenerate_scenarios.py"
                result = subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True, text=True, cwd=str(Path(__file__).parent),
                )
            if result.returncode == 0:
                st.cache_data.clear()
                st.success("Scenarios refreshed.")
                st.rerun()
            else:
                st.error(f"Refresh failed:\n```\n{result.stderr or result.stdout}\n```")

    chosen = label_to_opt[chosen_label]
    if statuses[chosen] == "todo":
        st.warning(f"**{chosen}** not populated yet — showing Base. Click ↻ Refresh to capture from model.")
    return chosen


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
    st.markdown("#### Financial Summary")
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
        st.markdown("#### Valuation Multiples (Live)")
        v = s["valuation"]
        target_years = [2025, 2026, 2027, 2028, 2029]
        idx_map = {y: v["years"].index(y) for y in target_years if y in v["years"]}

        live_price = cap["price"]
        live_shares_static = cap["diluted_shares"]
        nci = cap["nci"]

        ev_sales_row, ev_ebitda_row, pe_row = [], [], []
        for y in target_years:
            i = idx_map[y]
            shares_y = v["shares_out"][i] if v["shares_out"][i] not in (None, 0) else live_shares_static
            net_debt_y = v["net_debt"][i] if v["net_debt"][i] is not None else cap["net_debt"]
            mkt_cap_y = live_price * shares_y
            ev_y = mkt_cap_y + net_debt_y + nci

            rev = s["revenue"][i] if i < len(s["revenue"]) else None
            ebitda = s["ebitda"][i] if i < len(s["ebitda"]) else None
            eps = s["eps"][i] if i < len(s["eps"]) else None

            ev_sales_row.append(_fmt_x(ev_y / rev, 2) if rev else "")
            ev_ebitda_row.append(_fmt_x(ev_y / ebitda, 1) if ebitda else "")
            pe_row.append(_fmt_x(live_price / eps, 1) if eps else "")

        cols = ["Multiple"] + [str(y) for y in target_years]
        rows = [
            ["EV / Sales"] + ev_sales_row,
            ["EV / EBITDA"] + ev_ebitda_row,
            ["P / E"] + pe_row,
        ]
        val_df = pd.DataFrame(rows, columns=cols)
        st.dataframe(val_df, hide_index=True, use_container_width=True)
        st.caption(f"Multiples computed live: EV = ${live_price:.2f} × forecast shares + forecast net debt; P/E = ${live_price:.2f} / forecast EPS.")

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
        "**Placeholder — to be drafted together.** Replace this block with the executive summary "
        "paragraph framing the COKE short thesis (positioning, what's mispriced, time horizon, key catalyst)."
    )


def render_thesis() -> None:
    st.markdown("### Thesis")
    st.info(
        "**Placeholder — to be drafted together.** Replace with bullet points covering "
        "(1) volume / price elasticity dynamics, (2) commodity cost exposure (aluminum + oil), "
        "(3) margin compression mechanics, (4) valuation gap to fair value, "
        "(5) catalysts to realize the short."
    )


def render_elasticity(seg: dict, segment: str, figure_num: int) -> None:
    if segment == "Sparkling":
        price = seg["sparkling_price_yoy"]
        vol = seg["sparkling_volume_yoy"]
        commentary = (
            "Sparkling is COKE's largest revenue contributor and the segment most exposed to "
            "consumer pushback on price. The negative slope here is the demand-elasticity story: "
            "as price growth moderates, volume should recover. If pricing has to come down to "
            "defend volume, gross margin compresses."
        )
    else:
        price = seg["still_price_yoy"]
        vol = seg["still_volume_yoy"]
        commentary = (
            "Still beverages (water, sports drinks, juices) historically run at lower margins than "
            "sparkling and have shown more volatile volume response to pricing. A flatter or "
            "positive-sloping relationship here would suggest weaker pricing power than sparkling."
        )

    fig = charts.elasticity_scatter(price, vol, seg["quarters"], segment, figure_num)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(commentary)


def render_quarterly_yoy(seg: dict, figure_num: int) -> None:
    fig = charts.quarterly_yoy_chart(seg, figure_num)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Six series across Sparkling, Still, and Total — solid lines for volume YoY, dashed for "
        "price YoY. The price-volume divergence post-2022 is the central observation: pricing carried "
        "revenue while volumes flattened or declined."
    )


def render_commodity_stack(cogs: dict, oil: dict, figure_num: int) -> None:
    fig = charts.commodity_stack_chart(
        cogs["quarters"], cogs["all_in_us_price"], oil["quarters"], oil["close"], figure_num,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Aluminum drives the can-pack portion of COGS (~55%+ of physical cases by 2026); WTI oil drives "
        "PET-resin pricing and freight cost. Both have spiked in the post-COVID era and remain elevated "
        "vs. the 2016-2019 baseline."
    )


def render_aluminum_sensitivity(cogs: dict, summary: dict, cap: dict, figure_num: int) -> None:
    annual_cans_cases_mm = 200.0  # round forecast figure for can-pack volume
    content = cogs["content"]
    kg_per_can_case = content["kg_per_can_case"]
    base_eps_2026 = summary["eps"][summary["years"].index(2026)]

    quarters = cogs["quarters"]
    cck_price = cogs["cck_markup"]  # what CCK actually pays per MT (market all-in + supplier markup)
    q26 = ["Q1 26", "Q2 26", "Q3 26", "Q4 26"]
    indices_26 = [quarters.index(q) for q in q26 if q in quarters]
    base_cck_2026 = sum(cck_price[i] for i in indices_26 if cck_price[i] is not None) / max(len(indices_26), 1)
    diluted_shares = cap["diluted_shares"]
    tax_rate = 0.25

    fig = charts.aluminum_sensitivity_curve(
        base_cck_2026, annual_cans_cases_mm, kg_per_can_case,
        base_eps_2026, diluted_shares, tax_rate, figure_num,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Try it: dial in an aluminum price assumption")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        pct_change = st.slider(
            "Move from base case (%)",
            min_value=-50, max_value=50, value=0, step=5,
            help=f"Base case: ${base_cck_2026:,.0f}/MT (CCK delivered, incl. supplier markup)",
            key="al_slider",
        )
    new_price = base_cck_2026 * (1 + pct_change / 100)
    annual_kg_mm = annual_cans_cases_mm * kg_per_can_case
    annual_mt = annual_kg_mm * 1_000  # mm KG × 1000 = MT
    new_spend = annual_mt * new_price / 1_000_000  # $M
    base_spend = annual_mt * base_cck_2026 / 1_000_000
    delta_spend = new_spend - base_spend
    delta_eps = -delta_spend * (1 - tax_rate) / diluted_shares
    new_eps = base_eps_2026 + delta_eps

    with c2:
        st.metric("Implied 2026 EPS", f"${new_eps:.2f}",
                  delta=f"${delta_eps:+.2f}" if pct_change != 0 else None)
    with c3:
        st.metric("ΔAluminum Spend", f"${delta_spend:+,.0f}M")

    st.caption(
        f"Built from model assumptions: {annual_cans_cases_mm:.0f}M can-cases × {kg_per_can_case:.2f} KG/case "
        f"= {annual_mt:,.0f} MT of aluminum demand. CCK pays an all-in delivered price (market + supplier markup) "
        f"of ${base_cck_2026:,.0f}/MT base case for 2026 — at ${new_price:,.0f}/MT, spend changes by "
        f"${delta_spend:+,.0f}M, after-tax @ {int(tax_rate*100)}% = {delta_eps:+.2f} EPS impact. "
        f"Linear flow-through; ignores second-order effects."
    )
