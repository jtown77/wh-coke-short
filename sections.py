"""Streamlit section renderers — each function builds one section of the page."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

import charts
import scenarios as scen


WH_NAVY = "#303F55"
WH_BORDER = "#E5E0D8"
WH_INK = "#1A1A1A"
WH_MUTED = "#6B6B6B"
WH_CARD_BG = "#FFFFFF"


def _style_table(df: pd.DataFrame, first_col_bold: bool = True):
    """Editorial table style — white card, thin cream-tinted borders, JetBrains Mono numerals."""
    sty = df.style.set_table_styles([
        {"selector": "thead th",
         "props": [("background-color", WH_CARD_BG),
                   ("color", WH_MUTED),
                   ("font-family", "'Inter', sans-serif"),
                   ("font-weight", "600"),
                   ("font-size", "10px"),
                   ("letter-spacing", "0.12em"),
                   ("text-transform", "uppercase"),
                   ("text-align", "right"),
                   ("padding", "10px 12px"),
                   ("border-bottom", f"1px solid {WH_NAVY}")]},
        {"selector": "thead th:first-child", "props": [("text-align", "left")]},
        {"selector": "tbody td",
         "props": [("padding", "9px 12px"),
                   ("border-bottom", f"1px solid {WH_BORDER}"),
                   ("text-align", "right"),
                   ("font-family", "'JetBrains Mono', monospace"),
                   ("font-size", "12px"),
                   ("color", WH_INK),
                   ("background", WH_CARD_BG)]},
        {"selector": "tbody td:first-child",
         "props": [("text-align", "left"),
                   ("font-family", "'Inter', sans-serif"),
                   ("font-weight", "500" if first_col_bold else "400"),
                   ("color", WH_INK)]},
        {"selector": "", "props": [("border-collapse", "separate"),
                                    ("border-spacing", "0"),
                                    ("width", "100%"),
                                    ("background", WH_CARD_BG),
                                    ("border", f"1px solid {WH_BORDER}")]},
    ])
    return sty


def _render_styled_table(df: pd.DataFrame, first_col_bold: bool = True) -> None:
    sty = _style_table(df, first_col_bold)
    st.markdown(sty.hide(axis="index").to_html(), unsafe_allow_html=True)


def render_forecast_cone(history: dict, cap: dict, summary: dict) -> None:
    target_date = datetime(2026, 12, 31)
    fig = charts.forecast_cone_chart(
        history["dates"], history["close"], cap["price"],
        summary["return_eps"], target_date,
    )
    st.plotly_chart(fig, use_container_width=True, config=charts.STATIC_CONFIG)


def render_scenario_selector() -> str:
    import loaders  # noqa: F401  (kept for parity with render_refresh_block)

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

    chosen = label_to_opt[chosen_label]
    if statuses[chosen] == "todo":
        st.warning(f"**{chosen}** not populated yet — showing Base. Click ↻ Refresh to capture from model.")
    return chosen


def render_refresh_block() -> None:
    import os
    import subprocess
    import sys
    from pathlib import Path

    import loaders

    OWNER_USERNAME = "JoshuaLehrman"

    is_owner = os.environ.get("USERNAME", "") == OWNER_USERNAME
    captured = loaders.snapshot_captured_at()
    if captured:
        captured_str = f"{captured.strftime('%b')} {captured.day}, {captured.year} at {captured.strftime('%I:%M %p').lstrip('0')}"
    else:
        captured_str = "no snapshot found"

    if is_owner and loaders.LIVE_MODEL.exists():
        if st.button("↻ Refresh snapshot from live model",
                     help="Opens Excel via COM, captures Bull/Base/Bear + segment build + COGS sensitivity into snapshot.json."):
            with st.spinner("Capturing snapshot from Excel — takes ~15 seconds..."):
                script = Path(__file__).parent / "regenerate_scenarios.py"
                result = subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True, text=True, cwd=str(Path(__file__).parent),
                )
            if result.returncode == 0:
                st.cache_data.clear()
                st.success("Snapshot refreshed.")
                st.rerun()
            else:
                st.error(f"Refresh failed:\n```\n{result.stderr or result.stdout}\n```")
    st.caption(f"Snapshot captured: {captured_str}")


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
    left_col, right_col = st.columns([1, 2.5], gap="large")

    # LEFT: Cap Table (unchanged)
    with left_col:
        st.markdown("#### Cap Table (Live)")
        cap_df = pd.DataFrame([
            ["Price (COKE)", f"${cap['price']:.2f}"],
            ["Diluted Shares (M)", f"{cap['diluted_shares']:.2f}"],
            ["Market Cap ($M)", f"${cap['market_cap']:,.0f}"],
            ["Total Debt ($M)", f"${cap['total_debt']:,.0f}"],
            ["Cash ($M)", f"${cap['cash']:,.0f}"],
            ["Net Debt ($M)", f"${cap['net_debt']:,.0f}"],
            ["Enterprise Value ($M)", f"${cap['enterprise_value']:,.0f}"],
        ], columns=["Item", "Value"])
        _render_styled_table(cap_df)

    # RIGHT: Financial Summary with Valuation Multiples appended
    with right_col:
        st.markdown("#### Financial Summary")
        years = s["years"]
        v = s["valuation"]
        live_price = cap["price"]
        live_shares_static = cap["diluted_shares"]
        nci = cap["nci"]

        ev_ebitda_by_year, pe_by_year = {}, {}
        forward_years = {2025, 2026, 2027, 2028, 2029}
        for y in v["years"]:
            if y not in forward_years:
                continue
            i_v = v["years"].index(y)
            shares_y = v["shares_out"][i_v] if v["shares_out"][i_v] not in (None, 0) else live_shares_static
            net_debt_y = v["net_debt"][i_v] if v["net_debt"][i_v] is not None else cap["net_debt"]
            ev_y = (live_price * shares_y) + net_debt_y + nci
            if y in years:
                i_s = years.index(y)
                ebitda = s["ebitda"][i_s] if i_s < len(s["ebitda"]) else None
                eps = s["eps"][i_s] if i_s < len(s["eps"]) else None
                if ebitda:
                    ev_ebitda_by_year[y] = ev_y / ebitda
                if eps:
                    pe_by_year[y] = live_price / eps

        fin_data = {
            "Metric": [
                "Revenue ($M)", "  YoY %",
                "EBITDA ($M)", "  Margin %", "  YoY %",
                "Adj. EPS ($)", "  YoY %",
                "EV/EBITDA", "P/E",
            ],
        }
        for i, y in enumerate(years):
            fin_data[str(y)] = [
                _fmt_money(s["revenue"][i], 0),
                _fmt_pct(s["revenue_yoy"][i]),
                _fmt_money(s["ebitda"][i], 0),
                _fmt_pct(s["ebitda_margin"][i]),
                _fmt_pct(s["ebitda_yoy"][i]),
                f"${s['eps'][i]:.2f}" if s["eps"][i] is not None else "",
                _fmt_pct(s["eps_yoy"][i]),
                _fmt_x(ev_ebitda_by_year[y], 1) if y in ev_ebitda_by_year else "",
                _fmt_x(pe_by_year[y], 1) if y in pe_by_year else "",
            ]
        fin_df = pd.DataFrame(fin_data)
        _render_styled_table(fin_df)

    # FULL WIDTH: Merged Return Scenarios
    st.markdown("")
    st.markdown("#### Return Scenarios — 2026 YE")

    eps_by_label = {r["label"]: r for r in s["return_eps"]}
    eb_by_label = {r["label"]: r for r in s["return_ebitda"]}

    rows = []
    for label in ["Bull", "Base", "Bear"]:
        if label not in eps_by_label or label not in eb_by_label:
            continue
        eps_r = eps_by_label[label]
        eb_r = eb_by_label[label]
        rows.append([
            label,
            f"${eps_r['metric']:.2f}",
            _fmt_x(eps_r["multiple"], 0),
            f"${eps_r['target']:.2f}",
            _fmt_pct(eps_r["ret"]),
            f"${eb_r['metric']:,.0f}M",
            _fmt_x(eb_r["multiple"], 0),
            f"${eb_r['target']:.2f}",
            _fmt_pct(eb_r["ret"]),
        ])

    merged_df = pd.DataFrame(rows, columns=[
        "Scenario", "EPS", "P/E", "EPS Target", "EPS Return",
        "EBITDA", "EV/EBITDA", "EV Target", "EV Return",
    ])
    _render_styled_table(merged_df)


def render_executive_summary() -> None:
    st.markdown("### Executive Summary")
    st.markdown(
        "Coca-Cola Consolidated (COKE) is the largest US Coca-Cola bottler, generating "
        "\\$7+bn of revenue across four regions (Carolinas, Mid-Atlantic, Mid-South, "
        "Mid-West) and ~60 million consumers. The company buys the syrup from The "
        "Coca-Cola Company, mixes it with water and carbon dioxide, and then packages "
        "the beverage in cans and delivers to customers across its coverage. COKE "
        "distributes 40+ sparkling and still beverages and has discretion over the "
        "price it charges the end customers. They operate at 40% gross margins with "
        "aluminum and PET resin accounting for ~10% of total COGS. Both commodities "
        "are up >50% this year which should be a ~\\$3 hit to EPS. The company has zero "
        "sell-side coverage despite having a \\$14.4bn TEV and trading close to \\$100mn "
        "a day. We believe that normalized earnings power for this business is \\$6-7 "
        "EPS and deserves a high teens multiple, giving it a downside of close to 50% "
        "from the current price above \\$200."
    )


def render_thesis() -> None:
    st.markdown("### Short Thesis")

    st.markdown("**Thesis #1: Demand is squeezed from SNAP benefits ending for sugary drinks**")
    st.markdown(
        "- 22 states have already passed legislation to prohibit SNAP benefits to be "
        "used on sugary foods and drinks. 7 states have already pushed through these "
        "regulations (IA, IN, NE, UT, WV on Jan 1; ID Feb 15; FL Apr 20) and 6 states "
        "will push these policies through from now until October, 2026 (AR Jul 1, HI "
        "Aug 1, ND Sep 1, MO/OH/VA Oct 1). 5 of these states sit within COKE's "
        "distribution territory per the FY 2025 10-K (Carolinas, Mid-Atlantic, "
        "Mid-South, Mid-West): WV and IN are already live (Jan 1, 2026), AR goes "
        "effective July 1, and OH and VA go effective October 1, 2026."
    )

    st.markdown("**Thesis #2: Costs are squeezed from the war in Iran**")
    st.markdown(
        "- Aluminum should be a ~\\$200mn headwind to numbers this year assuming "
        "aluminum prices hold through the rest of the year\n"
        "- Diesel costs should prove to be a ~\\$50mn headwind this year, and PET resin "
        "should be a ~\\$25mn headwind"
    )

    st.markdown("**Thesis #3: Pricing has increased >50% since 2019 and consumers are tapped out**")
    st.markdown(
        "- COKE has increased EBITDA margins by 850 bps since 2019 because of intense "
        "pricing increases that are now coming to a head\n"
        "- PEP and KO have signaled that the low income consumer is coming under "
        "pressure and PEP has already announced price declines"
    )

    st.markdown("**Thesis #4: Current valuation is stretched vs historical**")
    st.markdown(
        "- The stock is currently trading at close to 30x LTM EPS vs a historical "
        "high teens multiple"
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
    st.plotly_chart(fig, use_container_width=True, config=charts.STATIC_CONFIG)
    st.caption(commentary)


def render_quarterly_yoy(seg: dict, figure_num: int) -> None:
    fig = charts.quarterly_yoy_chart(seg, figure_num)
    st.plotly_chart(fig, use_container_width=True, config=charts.STATIC_CONFIG)
    st.caption(
        "Sparkling and Still — solid lines are volume YoY, dashed are price YoY. The price-volume "
        "divergence post-2022 is the central observation: pricing carried revenue while volumes "
        "flattened or declined."
    )


def render_cumulative_pricing(seg: dict, cpi: dict, figure_num: int) -> None:
    fig = charts.cumulative_pricing_chart(seg, cpi, figure_num)
    st.plotly_chart(fig, use_container_width=True, config=charts.STATIC_CONFIG)
    st.caption(
        "Per-case prices indexed to Q1 2019 = 100. Total is a case-mix-weighted blend of "
        "sparkling and still. Core CPI (FRED CPILFESL, all items less food and energy, "
        "quarterly average) is the inflation benchmark. The gap between COKE's pricing and "
        "Core CPI since 2021 is the magnitude of the affordability problem."
    )


def render_commodity_stack(commodities: dict, figure_num: int) -> None:
    al = commodities["aluminum"]
    wti = commodities["wti"]
    fig = charts.commodity_stack_chart(
        al["dates"], al["close_per_mt"], wti["dates"], wti["close_per_bbl"], figure_num,
    )
    st.plotly_chart(fig, use_container_width=True, config=charts.STATIC_CONFIG)
    st.caption(
        "Aluminum (CME Midwest U.S., $/MT — LME 3M + Midwest premium) drives the can-pack portion of "
        "COGS; WTI oil drives PET-resin pricing and freight cost. Both have spiked sharply in 2025-2026."
    )


def render_aluminum_sensitivity(cogs: dict, summary: dict, cap: dict, figure_num: int = 5) -> None:
    from pathlib import Path

    annual_cases_mm = 200.0  # round forecast figure for can-pack volume
    content = cogs["content"]
    kg_per_case = content["kg_per_can_case"]
    cans_per_case = 24
    base_eps_2026 = summary["eps"][summary["years"].index(2026)]

    quarters = cogs["quarters"]
    cck_price = cogs["cck_markup"]  # what Crown Holdings (CCK ticker) charges COKE per MT
    q26 = ["Q1 26", "Q2 26", "Q3 26", "Q4 26"]
    indices_26 = [quarters.index(q) for q in q26 if q in quarters]
    base_cck_2026 = sum(cck_price[i] for i in indices_26 if cck_price[i] is not None) / max(len(indices_26), 1)
    diluted_shares = cap["diluted_shares"]
    tax_rate = 0.25

    annual_cans_b = annual_cases_mm * cans_per_case / 1_000  # 200M × 24 / 1000 = 4.8B
    annual_mt = annual_cases_mm * kg_per_case * 1_000  # M cases × KG/case × 1000 = MT
    base_spend_mm = annual_mt * base_cck_2026 / 1_000_000

    assets_dir = Path(__file__).parent / "assets" / "aluminum"

    st.markdown("##### The Build — How Much Aluminum COKE Buys Each Year")

    def _card(img_path, headline, label, sub):
        st.image(str(img_path), use_container_width=True)
        st.markdown(
            f"<div style='text-align:center;font-family:\"Source Serif 4\",Georgia,serif;"
            f"font-size:2.2rem;font-weight:600;color:{WH_INK};line-height:1.05;margin-top:0.6rem'>{headline}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='text-align:center;font-family:Inter,sans-serif;font-size:0.72rem;"
            f"letter-spacing:0.14em;color:{WH_MUTED};text-transform:uppercase;margin-top:0.25rem'>{label}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='text-align:center;font-family:Inter,sans-serif;font-size:0.88rem;"
            f"color:#4A4A4A;margin-top:0.5rem;line-height:1.4'>{sub}</div>",
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        _card(
            assets_dir / "cases.png",
            f"{annual_cases_mm:.0f}M",
            "Cases / year",
            f"{cans_per_case} cans per case",
        )
    with c2:
        _card(
            assets_dir / "cans_wall.png",
            f"{annual_cans_b:.1f}B",
            "Cans / year",
            f"{kg_per_case:.2f} KG aluminum per case",
        )
    with c3:
        _card(
            assets_dir / "ingots.png",
            f"{annual_mt/1000:,.0f}k MT",
            "Aluminum / year",
            f"~${base_spend_mm:,.0f}M spend @ ${base_cck_2026:,.0f}/MT",
        )

    st.markdown("")
    st.markdown("##### What the Aluminum Spike Costs — 2026 EPS Drag vs. 2025 Average")

    q25 = ["Q1 25", "Q2 25", "Q3 25", "Q4 25"]
    indices_25 = [quarters.index(q) for q in q25 if q in quarters]
    base_cck_2025 = sum(cck_price[i] for i in indices_25 if cck_price[i] is not None) / max(len(indices_25), 1)
    base_spend_2025 = annual_mt * base_cck_2025 / 1_000_000

    levels = [base_cck_2025, 9000, 10500, base_cck_2026, 13000, 14500, 16000]
    levels = sorted(set(round(x) for x in levels))

    rows = []
    for price in levels:
        spend = annual_mt * price / 1_000_000
        incremental_spend = spend - base_spend_2025
        eps_drag = -incremental_spend * (1 - tax_rate) / diluted_shares
        delta_price = price - base_cck_2025

        is_2025 = round(price) == round(base_cck_2025)
        is_model = round(price) == round(base_cck_2026)

        if is_2025:
            label = f"${price:,.0f} (2025 actual avg)"
            rows.append([label, "baseline", "—", "—"])
        else:
            suffix = " (model base for 2026)" if is_model else ""
            rows.append([
                f"${price:,.0f}{suffix}",
                f"+${delta_price:,.0f}",
                f"+${incremental_spend:,.0f}M",
                f"-${abs(eps_drag):.2f}",
            ])

    sens_df = pd.DataFrame(rows, columns=[
        "2026 Avg Landed Cost", "vs 2025 ($/MT)", "Incremental Spend", "2026 EPS Drag",
    ])
    _render_styled_table(sens_df, first_col_bold=True)
    st.caption(
        f"Anchored to 2025 actual full-year average (${base_cck_2025:,.0f}/MT). "
        "Drag = (incremental spend × (1 − 25% tax)) ÷ 57.0M diluted shares. "
        "Landed cost = COKE's all-in delivered cost per MT of aluminum content (LME spot + Midwest premium + can manufacturer markup)."
    )


def render_snap_brief() -> None:
    st.markdown('<div class="eyebrow">Demand Catalyst</div>', unsafe_allow_html=True)
    st.markdown("## SNAP Soda Restrictions — Datapoint Brief")
    st.markdown(
        "Sourced from AlphaSense (broker research, NielsenIQ/Numerator scanner data, expert calls) "
        "and earnings transcripts via EarningsCall.biz API. Quotes verbatim."
    )

    # SCANNER DATA
    st.markdown("##### Scanner Data")
    scanner_df = pd.DataFrame([
        ("CSD velocity (period ending Apr 18, 2026)", "-1.5%", "-5.1%", "JPM NielsenIQ note, 28 Apr 2026"),
        ("Salty snacks velocity (52w)", "—", "-5.5%", "JPM NielsenIQ note, 28 Apr 2026"),
        ("% of US shopping trips using SNAP (Mar 2026)", "—", "3.3%", "JPM Numerator (Above the Line), 22 Apr 2026"),
        ("% Walmart trips using SNAP", "—", "5.7%", "JPM Numerator, 22 Apr 2026"),
        ("% Albertsons (ACI) trips using SNAP", "—", "5.7%", "JPM Numerator, 22 Apr 2026"),
    ], columns=["Metric", "4-week", "52-week", "Source"])
    _render_styled_table(scanner_df)

    # BRAND-TIER EXPOSURE
    st.markdown("")
    st.markdown("##### SNAP Exposure by Brand Tier (Walmart Sr Manager, 8 May 2025)")
    tier_df = pd.DataFrame([
        ("Value soda", "Faygo, Shasta", "40-45%"),
        ("National brand", "Coca-Cola, Pepsi", "15-20%"),
    ], columns=["Brand Tier", "Examples", "% of Sales Paid via SNAP (Midwest WMT)"])
    _render_styled_table(tier_df)
    st.markdown(
        "**Read for COKE:** as a national-brand bottler (Coca-Cola Trademark), COKE sits in the "
        "lower-exposure 15-20% bucket, not the 40-45% value tier."
    )

    # STATE WAIVERS
    st.markdown("")
    st.markdown("##### State Waivers — Effective Dates")
    waivers_df = pd.DataFrame([
        ("Iowa", "Jan 1, 2026", "Soda + taxable foods", "No"),
        ("Indiana", "Jan 1, 2026", "Soft drinks + candy", "Yes (Mid-West)"),
        ("Nebraska", "Jan 1, 2026", "Soda + energy drinks", "No"),
        ("Utah", "Jan 1, 2026", "Soft drinks", "No"),
        ("West Virginia", "Jan 1, 2026", "Soda", "Yes (Mid-Atlantic)"),
        ("Idaho", "Feb 15, 2026", "Soda + candy", "No"),
        ("Florida", "Apr 20, 2026", "Soda, energy, candy, prepared desserts", "No"),
        ("Arkansas", "Jul 1, 2026", "Soda, sugary drinks, candy", "Yes (Mid-South)"),
        ("Hawaii", "Aug 1, 2026", "Soft drinks", "No"),
        ("North Dakota", "Sep 1, 2026", "Sweetened bev, energy, candy", "No"),
        ("Missouri", "Oct 1, 2026", "Candy, desserts, sweetened bev", "No"),
        ("Ohio", "Oct 1, 2026", "Sugar-sweetened bev", "Yes (Mid-West, Mid-Atlantic)"),
        ("Virginia", "Oct 1, 2026", "Sweetened bev", "Yes (Carolinas, Mid-Atlantic)"),
    ], columns=["State", "Effective", "Restricted", "COKE Territory"])
    _render_styled_table(waivers_df)
    st.caption(
        "Source: USDA FNS Food Restriction Waivers (waivers, dates, restricted categories); "
        "COKE FY 2025 10-K (territory mapping by region). ~22 states approved overall; "
        "10+ implemented as of late April 2026. 5 waiver states sit in COKE territory: "
        "WV and IN live, AR (Jul 1), OH and VA (Oct 1)."
    )

    # MANAGEMENT & EXPERT QUOTES
    st.markdown("")
    st.markdown("##### Management & Expert Quotes — Verbatim")

    st.markdown("**PepsiCo Q1 2026** *(via JPM Carla Casella, 16 Apr 2026)*")
    st.markdown(
        "> *\"Eight states began SNAP purchase restrictions in 1Q, primarily affecting beverages and "
        "candy. Management noted that it is watching how consumer reallocation between SNAP benefits "
        "and other discretionary income [evolves].\"*  \n"
        "> — **PepsiCo mgmt commentary** as captured by JPM"
    )

    st.markdown("**KDP National Sales Director** *(Expert Insight, 11 Feb 2026) — COUNTER-INDICATOR*")
    st.markdown(
        "> *\"Things that we thought were going to hit us have not. What we learned with SNAP is that "
        "when the government shut down and people lost their benefits, they still continue to purchase "
        "products like ours, CSD, things like that that didn't affect it.\"*  \n"
        "> — **KDP National Sales Director**, AlphaSense Expert Call"
    )

    st.markdown("**SVP National Grocery Chain** *(Expert Insight, 24 Mar 2026) — BEAR-SUPPORTING*")
    st.markdown(
        "> *\"Main factors... [include] the change in SNAP benefits where consumers are no longer "
        "allowed in a lot of states to buy products with sugar in them... I think that needs to be "
        "solved and a resolution is needed, or it could hurt the category as we move forward, "
        "particularly around carbonated soft drinks.\"*  \n"
        "> — **SVP at National Grocery Chain**, AlphaSense Expert Call"
    )

    st.markdown("**VP Discount Grocery Chain** *(Expert Insight, 12 Mar 2026)*")
    st.markdown(
        "SNAP benefit changes flagged as the **second-biggest** factor impacting category sales, "
        "after general economic pressure on lower-income shoppers."
    )

    # KO Q1 2026 EARNINGS CALL
    st.markdown("")
    st.markdown("##### KO Q1 2026 Earnings Call (28 Apr 2026)")

    st.markdown("**Henrique Braun (CEO) on pricing & affordability** — to Dara Mohsenian (MS):")
    st.markdown(
        "> *\"Pricing is embedded into this equation as well. We are going where the consumer is, "
        "right? Affordability continues to be part of the revenue growth management architecture that "
        "we have, not only in the U.S., but in different parts of the world as well. The consumers "
        "that have pressure today are the low-income consumers, and we really dialed up our "
        "affordability options to get closer to them. In North America, for instance, we went into "
        "bringing options not only on the single-serve, but on the multi-serve and the entry packs "
        "and helped us to continue to keep them in the franchise.\"*"
    )

    st.markdown("**John Murphy (President & CFO) on bottler cost exposure** — to Steve Powers (DB):")
    st.markdown(
        "> *\"Right now we estimate it's manageable at the company level, given we have less "
        "exposure. **Our bottling partners have more exposure, particularly aluminum and PET**, on "
        "the back of both the oil price impact and just the overall supply chain disruptions that "
        "are likely to affect us as we go through the year.\"*"
    )

    st.markdown("**John Murphy on Q1 gross margin:**")
    st.markdown(
        "> *\"Comparable gross margin declined approximately 30 basis points stemming primarily from "
        "commodity pressures in our tea and coffee businesses, phasing of inventory costs, and timing "
        "of trade spend.\"*"
    )

    # SNAP THESIS LEDGER
    st.markdown("")
    st.markdown("##### SNAP Thesis Ledger — COKE-Specific")
    ledger_df = pd.DataFrame([
        ("CSD velocity -5.1% 52w (NielsenIQ, Apr 2026)", "KDP: gov shutdown 'natural experiment' showed CSD purchases held when SNAP funding paused"),
        ("5 COKE-territory states restricted: WV, IN live; AR Jul 1; OH, VA Oct 1", "National brands only 15-20% SNAP-paid (vs 40-45% for value brands)"),
        ("PEP mgmt explicitly flagged SNAP as 1Q headwind", "KO Q1 26 reported +3% global volume / +10% organic rev, overall not impaired"),
        ("Grocery SVP: 'could hurt the category... particularly CSDs'", "Only 3.3% of total trips use SNAP nationally"),
        ("C-store soda/candy ~45% gross margin, channel pain", "Substitution flow into other COKE still beverages possible"),
    ], columns=["BEAR points", "BULL / counter-points"])
    _render_styled_table(ledger_df, first_col_bold=False)

    # SOURCING NOTES
    st.markdown("")
    st.markdown("##### Sourcing Notes")
    st.markdown(
        "- **TD Cowen Moskow note** previously cited from Perplexity could not be verified on AlphaSense; excluded from working thesis until source confirmed.\n"
        "- **Ibotta cashback panel** previously cited replaced with NielsenIQ scanner data (industry-standard panel) via JPM 28 Apr 2026 note.\n"
        "- **PEP Q1 26 call** not yet ingested in EarningsCall.biz API; PEP SNAP commentary sourced via JPM Carla Casella note dated 16 Apr 2026.\n"
        "- **KO Q1 26 quotes** verified verbatim from earnings transcript (call held 28 Apr 2026)."
    )
