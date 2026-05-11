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


def _render_styled_table(df: pd.DataFrame, first_col_bold: bool = True,
                         highlight_rows: list[bool] | None = None) -> None:
    sty = _style_table(df, first_col_bold)
    if highlight_rows:
        # Soft peach for COKE-territory rows (matches the source slide).
        # `!important` because `_style_table` already sets a `tbody td { background: ... }`
        # rule whose `tbody td` selector (specificity 101) outranks the per-cell ID
        # rule (100) that Styler emits for `apply` overrides.
        peach = "#F5DDD5"
        def _row_bg(row):
            i = df.index.get_loc(row.name)
            if i < len(highlight_rows) and highlight_rows[i]:
                return [f"background: {peach} !important"] * len(row)
            return [""] * len(row)
        sty = sty.apply(_row_bg, axis=1)
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
        "a day. We see 2026 EPS landing in the high-\\$6s with through-cycle earnings "
        "power in the \\$7-8 range; at a high-teens multiple that implies material "
        "downside from the current \\$174 — base case -26%, bear case -53%."
    )


def render_thesis() -> None:
    st.markdown("### Short Thesis")

    st.markdown("**Thesis #1: Demand is squeezed from SNAP benefits ending for sugary drinks**")
    st.markdown(
        "- 22 states have passed legislation to prohibit SNAP benefits from being "
        "used on sugary foods and drinks. **8 of these states sit within COKE's "
        "distribution territory** per the FY 2025 10-K (Carolinas, Mid-Atlantic, "
        "Mid-South, Mid-West). Three are already active (IA Jan-26, WV Apr-26, IN "
        "mid-26) and five more go effective in 2H26 (AR Jul-26, TN Jul-26, SC Aug-26, "
        "OH Oct-26, VA Oct-26). **6.8M SNAP participants in COKE regions are now "
        "restricted (8.9% of COKE's regional population).**"
    )

    st.markdown("**Thesis #2: Costs are squeezed from the war in Iran**")
    st.markdown(
        "- Aluminum should be a ~\\$200mn headwind to numbers this year assuming "
        "aluminum prices hold through the rest of the year\n"
        "- Diesel costs should prove to be a ~\\$200mn pre-tax headwind this year, "
        "and PET resin should be a ~\\$25-50mn headwind\n"
        "- KO's Q1 26 call corroborates the bottler-cost setup. CFO **John Murphy**: "
        "*\"Right now we estimate it's manageable at the company level, given we "
        "have less exposure. Our bottling partners have more exposure, particularly "
        "aluminum and PET, on the back of both the oil price impact and just the "
        "overall supply chain disruptions that are likely to affect us as we go "
        "through the year.\"*"
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

    st.markdown("**Thesis #5: GLP-1 adoption is a structural drag on sugary-soft-drink volumes**")
    st.markdown(
        "- Numerator household panel: GLP-1 households cut CSD purchases ~12-15% "
        "post-Rx vs matched controls\n"
        "- ~15M Americans now on GLP-1s, up from <2M in 2022; Trilliant Health "
        "projects 25-35M by 2030"
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
        "sparkling and still. Food at Home CPI (FRED CPIUFDSL, BLS food-at-home component, "
        "the closest benchmark for grocery-channel beverage spend) and Core CPI "
        "(FRED CPILFESL, all items less food and energy) are quarterly averages. "
        "The gap between COKE's pricing and food-at-home inflation since 2021 is the "
        "magnitude of the affordability problem."
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
        "COGS; WTI oil drives PET-resin pricing and freight cost. Both have spiked sharply in 2025-2026. "
        "**Note:** This chart shows raw aluminum (LME 3M + Midwest premium); the cascade table below "
        "uses **all-in landed cost**, which is roughly 3.3× the raw price after layering in the can "
        "manufacturer (CCK) markup."
    )


def render_aluminum_sensitivity(cogs: dict, summary: dict, cap: dict, figure_num: int = 6) -> None:
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

    st.markdown('<div class="eyebrow">Packaging Cost — Aluminum</div>', unsafe_allow_html=True)
    st.markdown(f"## Figure {figure_num}. Aluminum Cost Cascade — From Cans to EPS")
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


def render_pet_resin_sensitivity(cogs: dict, seg: dict, cap: dict, figure_num: int = 7) -> None:
    from pathlib import Path

    diluted_shares = cap["diluted_shares"]
    tax_rate = 0.25

    quarters = cogs["quarters"]
    y25_idx = [i for i, q in enumerate(quarters) if q.endswith(" 25")]

    fy25_total_cases = sum(seg["total_cases"][i] for i in y25_idx if seg["total_cases"][i] is not None)
    fy25_bottle_cases = sum(cogs["cases_in_bottles_mm"][i] for i in y25_idx if cogs["cases_in_bottles_mm"][i] is not None)
    fy25_pet_mm_kg = sum(cogs["pet_volume_mm_kg"][i] for i in y25_idx if cogs["pet_volume_mm_kg"][i] is not None)
    fy25_pet_mt = fy25_pet_mm_kg * 1000.0

    pct_bottles = (fy25_bottle_cases / fy25_total_cases) if fy25_total_cases else 0.46
    kg_per_bottle_case = cogs["content"].get("pet_kg_per_bottle_case") or 0.2016

    # All-in landed PET cost ($/MT) — COKE-paid (raw resin × 1.5 bottler markup).
    # Baseline anchored to FY25 average; 2026 spike per Josh's read off the model.
    base_pet_2025 = 2400.0
    base_pet_2026 = 3600.0

    base_spend_2025 = fy25_pet_mt * base_pet_2025 / 1_000_000
    base_spend_2026 = fy25_pet_mt * base_pet_2026 / 1_000_000

    assets_dir = Path(__file__).parent / "assets" / "pet"

    st.markdown('<div class="eyebrow">Packaging Cost — PET Resin</div>', unsafe_allow_html=True)
    st.markdown(f"## Figure {figure_num}. PET Resin Cost Cascade — From Cases to EPS")
    st.markdown("##### The Build — How Much PET Resin COKE Buys Each Year")

    def _card(img_path, headline, label, sub):
        if img_path.exists():
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
            assets_dir / "total_cases.png",
            f"{fy25_total_cases:,.0f}M",
            "Total cases / year",
            "FY25 total physical case volume per the model",
        )
    with c2:
        _card(
            assets_dir / "bottle_cases.png",
            f"{fy25_bottle_cases:,.0f}M",
            "Bottle cases / year",
            f"{pct_bottles*100:.0f}% of FY25 cases packaged in PET bottles",
        )
    with c3:
        _card(
            assets_dir / "pet_pellets.png",
            f"{fy25_pet_mt/1000:,.0f}k MT",
            "PET resin / year",
            f"~${base_spend_2025:,.0f}M spend @ ${base_pet_2025:,.0f}/MT (all-in, 2025 avg)",
        )

    st.markdown("")
    st.markdown("##### What the PET Resin Spike Costs — 2026 EPS Drag vs. 2025 Average")

    levels = [base_pet_2025, 2800, 3200, base_pet_2026, 4000, 4500, 5000]
    levels = sorted(set(round(x) for x in levels))

    rows = []
    for price in levels:
        spend = fy25_pet_mt * price / 1_000_000
        incremental_spend = spend - base_spend_2025
        eps_drag = -incremental_spend * (1 - tax_rate) / diluted_shares
        delta_price = price - base_pet_2025

        is_2025 = round(price) == round(base_pet_2025)
        is_model = round(price) == round(base_pet_2026)

        if is_2025:
            label = f"${price:,.0f} (2025 actual avg)"
            rows.append([label, "baseline", "—", "—"])
        else:
            suffix = " (2026 spike)" if is_model else ""
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
        f"Anchored to 2025 actual full-year average (\\${base_pet_2025:,.0f}/MT, all-in). "
        "Drag = (incremental spend × (1 − 25% tax)) ÷ 57.0M diluted shares. "
        f"All-in landed cost = raw PET resin (Bloomberg PUSAPEBG Index) × 1.5 bottler markup. "
        f"Volume base = {fy25_pet_mt:,.0f} MT/yr ({fy25_bottle_cases:.0f}M bottle cases × "
        f"{kg_per_bottle_case:.4f} kg/case), captured live from the model's COGS Sensitivity tab."
    )


def render_diesel_sensitivity(diesel: dict, cap: dict, figure_num: int = 8) -> None:
    from pathlib import Path

    annual_gallons_m = 100.0   # Clifford (former CFO): COKE burns ~100M gallons of diesel annually
    mpg_blended = 6.0          # Clifford
    annual_miles_m = annual_gallons_m * mpg_blended  # 600M miles
    tax_rate = 0.25
    diluted_shares = cap["diluted_shares"]

    # Anchor to FY2025 actual full-year average (parity with the aluminum cascade,
    # so the diesel-as-%-of-S&H ratio is apples-to-apples FY25 vs FY25).
    pairs_2025 = [
        (d, p) for d, p in zip(diesel.get("dates", []), diesel.get("price_per_gal", []))
        if d.startswith("2025")
    ]
    if pairs_2025:
        diesel_baseline = sum(p for _, p in pairs_2025) / len(pairs_2025)
    else:
        diesel_baseline = diesel.get("latest") or 3.66
    baseline_label = "2025 avg"

    annual_spend_mm = annual_gallons_m * diesel_baseline
    eps_per_dime = (annual_gallons_m * 0.10 * (1 - tax_rate)) / diluted_shares  # $/share per +$0.10/gal

    assets_dir = Path(__file__).parent / "assets" / "diesel"

    st.markdown('<div class="eyebrow">Distribution Cost — Diesel</div>', unsafe_allow_html=True)
    st.markdown(f"## Figure {figure_num}. Diesel Cost Cascade — From Miles to EPS")
    st.markdown("")
    st.markdown("##### The Build — Miles, MPG, Gallons")

    def _card(img_path, headline, label, sub):
        if img_path.exists():
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
            assets_dir / "gary_driving.png",
            f"{annual_miles_m:,.0f}M",
            "Miles / year",
            "4,600 vehicles across 60 distribution centers and 14 states (FY25 10-K)",
        )
    with c2:
        _card(
            assets_dir / "coke_fleet.png",
            f"{mpg_blended:.1f}",
            "MPG (blended)",
            "Mix of Class 8 line-haul tractors and DSD box trucks; per former CFO",
        )
    with c3:
        _card(
            assets_dir / "gary_fueling.png",
            f"{annual_gallons_m:,.0f}M",
            "Gallons / year",
            f"~${annual_spend_mm:,.0f}M annual diesel spend @ ${diesel_baseline:.2f}/gal "
            f"(US retail #2 diesel, {baseline_label})",
        )

    st.markdown("")
    st.markdown(
        f"##### Each \\$0.10/gal move in diesel ≈ \\${eps_per_dime:.2f} EPS impact"
    )

    sh_fy25_mm = 842  # FY2025 SD&A "shipping and handling" line, $M
    diesel_pct_of_sh = annual_spend_mm / sh_fy25_mm * 100

    share_df = pd.DataFrame(
        [[
            f"${annual_spend_mm:,.0f}M",
            f"${sh_fy25_mm:,}M",
            f"{diesel_pct_of_sh:.0f}%",
        ]],
        columns=[
            f"FY25 diesel spend (~{annual_gallons_m:.0f}M gal × ${diesel_baseline:.2f})",
            "FY25 'shipping & handling' (10-K)",
            "Diesel as % of S&H",
        ],
    )
    _render_styled_table(share_df, first_col_bold=False)

    st.caption(
        f"Anchored to FY2025 actual full-year average US retail #2 diesel "
        f"(FRED GASDESW, \\${diesel_baseline:.2f}/gal). Math: ΔEPS = "
        f"(ΔPrice × 100M gal × (1 − 25% tax)) ÷ {diluted_shares:.1f}M diluted shares. "
        f"Reported FY25 SD&A 'shipping & handling' was \\${sh_fy25_mm}M (Q1 26: \\$216M, "
        "+11% YoY); additional S&H sits in COGS for plant→DC movement (not separately "
        "disclosed), so true diesel exposure runs above the \\$842M line."
    )


def render_snap_brief() -> None:
    st.markdown('<div class="eyebrow">Demand Catalyst</div>', unsafe_allow_html=True)
    st.markdown("## SNAP Soda Restrictions — Datapoint Brief")
    st.markdown(
        "Sourced from AlphaSense (broker research, NielsenIQ/Numerator scanner data, expert calls) "
        "and earnings transcripts via EarningsCall.biz API. Quotes verbatim."
    )

    # SNAP EXPOSURE — COKE REGIONAL CUT
    st.markdown("##### SNAP Exposure — COKE Regional Footprint")
    waivers_df = pd.DataFrame([
        ("Ohio",                 "11.8", "13.2%", "1.6", "Yes", "Oct-26",   "Approved"),
        ("North Carolina",       "10.8", "12.2%", "1.3", "No",  "—",        "—"),
        ("Virginia",             "8.7",  "10.5%", "0.9", "Yes", "Oct-26",   "Approved"),
        ("Tennessee",            "7.1",  "13.8%", "1.0", "Yes", "Jul-26",   "Approved"),
        ("Indiana",              "6.9",  "13.0%", "0.9", "Yes", "Mid-2026", "Approved"),
        ("Maryland",             "6.2",  "11.0%", "0.7", "No",  "—",        "—"),
        ("South Carolina",       "5.3",  "13.5%", "0.7", "Yes", "Aug-26",   "Approved"),
        ("Louisiana",            "4.6",  "18.5%", "0.9", "Yes", "Feb-26",   "Active"),
        ("Kentucky",             "4.5",  "14.1%", "0.6", "No",  "—",        "—"),
        ("Iowa",                 "3.2",  "10.0%", "0.3", "Yes", "Jan-26",   "Active"),
        ("Arkansas",             "3.0",  "7.8%",  "0.2", "Yes", "Jul-26",   "Approved"),
        ("West Virginia",        "1.8",  "15.7%", "0.3", "Yes", "Apr-26",   "Active"),
        ("Delaware",             "1.0",  "13.0%", "0.1", "No",  "—",        "—"),
        ("District of Columbia", "0.7",  "17.5%", "0.1", "No",  "—",        "—"),
        ("Total",                "75.6", "—",     "9.6", "—",   "—",        "—"),
    ], columns=[
        "State", "State Population (M)", "SNAP Participation Rate",
        "SNAP Participants (M)", "Soda Restriction", "Effective Date", "Status",
    ])
    # Pink rows = COKE-territory states with an active or approved soda restriction
    # (per the WHCM regional cut). Total row not highlighted.
    coke_territory_yes = {"Ohio", "Virginia", "Tennessee", "Indiana",
                          "South Carolina", "Iowa", "Arkansas", "West Virginia"}
    highlight = [s in coke_territory_yes for s in waivers_df["State"].tolist()]
    _render_styled_table(waivers_df, highlight_rows=highlight)

    st.markdown("")
    summary_df = pd.DataFrame([
        ("SNAP Participants now Restricted",                                      "6.8M"),
        ("Percentage of COKE's Regional Population",                              "8.9%"),
        ("SNAP Propensity to Consume (per Mississippi State Auditor Office)",     "43%"),
        ("Percentage of COKE's Consumption that may be restricted",               "12.8%"),
    ], columns=["Metric", "Value"])
    _render_styled_table(summary_df)

    st.caption(
        "Pink rows = COKE-territory states with an active or approved soda restriction. "
        "Sources: state population (US Census 2024), SNAP participation rate and participants "
        "(USDA FNS Program Data, FY25), waiver status (USDA FNS Food Restriction Waivers), "
        "propensity-to-consume (Mississippi State Auditor Office). "
        "Consumption-at-risk math: restricted-state participants × (1 + propensity uplift) ÷ "
        "regional population = 6.8M × 1.43 / 75.6M ≈ 12.8%."
    )

    # SCANNER DATA
    st.markdown("")
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
        ("8 COKE-territory states restricted (IA/WV/IN active; AR/TN/SC/OH/VA in 2H26)", "National brands only 15-20% SNAP-paid (vs 40-45% for value brands)"),
        ("PEP mgmt explicitly flagged SNAP as 1Q headwind", "KO Q1 26 reported +3% global volume / +10% organic rev, overall not impaired"),
        ("Grocery SVP: 'could hurt the category... particularly CSDs'", "Only 3.3% of total trips use SNAP nationally"),
        ("C-store soda/candy ~45% gross margin, channel pain", "Substitution flow into other COKE still beverages possible"),
    ], columns=["BEAR points", "BULL / counter-points"])
    _render_styled_table(ledger_df, first_col_bold=False)

