"""Plotly chart builders. Each function returns a go.Figure ready for st.plotly_chart()."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

WH_NAVY = "#303f55"
WH_NAVY_LIGHT = "#5e6e85"
WH_ACCENT = "#c0392b"
WH_AMBER = "#d49a3a"
WH_GREEN = "#3f7a4e"
WH_GRAY = "#8b95a3"
WH_GRAY_LIGHT = "#c7ccd3"
WH_BG = "#ffffff"
WH_GRID = "#eef0f3"


def _apply_style(fig: go.Figure, title: str, subtitle: str | None = None, height: int = 460) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" + (f"<br><span style='font-size:13px;color:{WH_GRAY};font-weight:400'>{subtitle}</span>" if subtitle else ""),
            font=dict(size=20, color=WH_NAVY, family="Source Serif Pro, Georgia, serif"),
            x=0.0, xanchor="left", y=0.96, yanchor="top",
            pad=dict(t=10, b=10),
        ),
        paper_bgcolor=WH_BG,
        plot_bgcolor=WH_BG,
        font=dict(family="Source Sans Pro, sans-serif", color="#1a2230", size=12),
        margin=dict(l=60, r=30, t=110 if subtitle else 80, b=60),
        height=height,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(size=11),
        ),
        hovermode="closest",
    )
    fig.update_xaxes(showgrid=True, gridcolor=WH_GRID, zeroline=False, linecolor=WH_GRID)
    fig.update_yaxes(showgrid=True, gridcolor=WH_GRID, zeroline=True, zerolinecolor=WH_GRAY_LIGHT, zerolinewidth=1, linecolor=WH_GRID)
    return fig


def _filter_history(values: list, quarters: list, end_label: str = "Q4 25") -> tuple[list, list]:
    """Truncate a series at the end of the historical period (default Q4 25)."""
    if end_label not in quarters:
        return values, quarters
    idx = quarters.index(end_label) + 1
    return values[:idx], quarters[:idx]


def _filter_pairs(x: list, y: list, labels: list, start_label: str = "Q1 18", end_label: str = "Q4 25"):
    out_x, out_y, out_l = [], [], []
    started = False
    for xi, yi, li in zip(x, y, labels):
        if li == start_label:
            started = True
        if started and xi is not None and yi is not None:
            out_x.append(float(xi))
            out_y.append(float(yi))
            out_l.append(li)
        if li == end_label:
            break
    return out_x, out_y, out_l


def elasticity_scatter(price_yoy: list, volume_yoy: list, quarter_labels: list, segment: str, figure_num: int) -> go.Figure:
    """X = Avg Sales/Case YoY %, Y = Case Volume YoY %. Quarterly historical scatter with OLS trendline."""
    x, y, labels = _filter_pairs(price_yoy, volume_yoy, quarter_labels)
    color = WH_NAVY if segment == "Sparkling" else WH_ACCENT

    fig = go.Figure()
    if not x:
        return _apply_style(fig, f"Figure {figure_num}. {segment} Beverages — Demand Elasticity", "No data available")

    years = [int("20" + q.split()[-1]) for q in labels]

    fig.add_trace(go.Scatter(
        x=[xi * 100 for xi in x],
        y=[yi * 100 for yi in y],
        mode="markers",
        name="Quarterly observations",
        text=labels,
        marker=dict(
            size=12,
            color=years,
            colorscale=[[0, WH_GRAY_LIGHT], [1, color]],
            showscale=True,
            colorbar=dict(title=dict(text="Year", side="right"), thickness=10, len=0.55, x=1.02, tickfont=dict(size=10)),
            line=dict(width=1, color="white"),
        ),
        hovertemplate="<b>%{text}</b><br>Price YoY: %{x:.1f}%<br>Volume YoY: %{y:.1f}%<extra></extra>",
    ))

    xa = np.array(x) * 100
    ya = np.array(y) * 100
    if len(xa) > 2:
        slope, intercept = np.polyfit(xa, ya, 1)
        x_line = np.linspace(min(xa) - 1, max(xa) + 1, 50)
        fig.add_trace(go.Scatter(
            x=x_line, y=slope * x_line + intercept, mode="lines",
            name=f"OLS fit (slope = {slope:.2f})",
            line=dict(color=WH_GRAY, width=2, dash="dash"),
            hoverinfo="skip",
        ))

    fig.update_xaxes(title="Avg Sales / Case YoY %", ticksuffix="%")
    fig.update_yaxes(title="Case Volume YoY %", ticksuffix="%")
    return _apply_style(
        fig,
        f"Figure {figure_num}. {segment} Beverages — Demand Elasticity",
        f"Quarterly Price vs. Volume YoY % • {labels[0]} – {labels[-1]}",
        height=520,
    )


def quarterly_yoy_chart(seg: dict, figure_num: int) -> go.Figure:
    """Six-line chart, history only (truncated at Q4 25). Volume = solid, Price = dashed."""
    quarters_full = seg["quarters"]
    quarters = []
    end = "Q4 25"
    for q in quarters_full:
        quarters.append(q)
        if q == end:
            break
    n = len(quarters)

    rev = seg["total_revenue"][:n]
    cases = seg["total_cases"][:n]
    avg_price = [(r / c) if (r is not None and c not in (None, 0)) else None for r, c in zip(rev, cases)]
    total_price_yoy = []
    for i, p in enumerate(avg_price):
        if i < 4 or p is None or avg_price[i - 4] in (None, 0):
            total_price_yoy.append(None)
        else:
            total_price_yoy.append(p / avg_price[i - 4] - 1)

    series = [
        ("Sparkling Volume", seg["sparkling_volume_yoy"][:n], WH_NAVY, "solid"),
        ("Sparkling Price", seg["sparkling_price_yoy"][:n], WH_NAVY, "dash"),
        ("Still Volume", seg["still_volume_yoy"][:n], WH_ACCENT, "solid"),
        ("Still Price", seg["still_price_yoy"][:n], WH_ACCENT, "dash"),
        ("Total Volume", seg["total_cases_yoy"][:n], WH_GRAY, "solid"),
        ("Total Price (derived)", total_price_yoy, WH_GRAY, "dash"),
    ]

    fig = go.Figure()
    for name, vals, color, dash in series:
        ys = [v * 100 if v is not None else None for v in vals]
        fig.add_trace(go.Scatter(
            x=quarters, y=ys, mode="lines", name=name,
            line=dict(color=color, width=2.2, dash=dash),
            connectgaps=False,
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_xaxes(title="", tickangle=-45, nticks=14)
    fig.update_yaxes(title="YoY % Change", ticksuffix="%")
    return _apply_style(
        fig,
        f"Figure {figure_num}. Quarterly Price & Volume YoY Growth",
        "Sparkling, Still, Total • Volume (solid) vs Price (dashed) • historicals through Q4 2025",
        height=520,
    )


def commodity_stack_chart(quarters: list, all_in_aluminum: list, oil_quarters: list, oil_close: list, figure_num: int) -> go.Figure:
    """Aluminum (left axis, $/MT) and WTI Oil (right axis, $/bbl) — quarterly historical only."""
    # Truncate aluminum to history
    al_vals, al_q = _filter_history(all_in_aluminum, quarters, end_label="Q4 25")
    # Filter oil to matching range
    oil_filtered_q, oil_filtered_v = [], []
    valid_q = set(al_q)
    for q, v in zip(oil_quarters, oil_close):
        if q in valid_q:
            oil_filtered_q.append(q)
            oil_filtered_v.append(v)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=al_q, y=al_vals, mode="lines", name="Aluminum All-in ($/MT, left)",
        line=dict(color=WH_NAVY, width=2.5),
        hovertemplate="<b>Aluminum</b><br>%{x}: $%{y:,.0f}/MT<extra></extra>",
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=oil_filtered_q, y=oil_filtered_v, mode="lines", name="WTI Oil ($/bbl, right)",
        line=dict(color=WH_AMBER, width=2.5),
        hovertemplate="<b>WTI</b><br>%{x}: $%{y:.1f}/bbl<extra></extra>",
        yaxis="y2",
    ))

    fig.update_layout(
        yaxis=dict(title="Aluminum All-in ($/MT)", tickprefix="$", separatethousands=True,
                   showgrid=True, gridcolor=WH_GRID),
        yaxis2=dict(title="WTI Oil ($/bbl)", tickprefix="$", overlaying="y", side="right",
                    showgrid=False),
    )
    fig.update_xaxes(title="", tickangle=-45, nticks=14)
    return _apply_style(
        fig,
        f"Figure {figure_num}. Commodity Cost Stack — Aluminum & WTI Oil",
        "Quarterly historical • aluminum drives can-pack COGS, oil drives PET-resin and freight",
        height=460,
    )


def forecast_cone_chart(
    history_dates: list,
    history_close: list,
    current_price: float,
    scenarios: list[dict],
    target_date,
) -> go.Figure:
    """Stock chart with Bull/Base/Bear forecast cone. `scenarios` = [{label,target,ret},...] ordered Bull, Base, Bear."""
    from datetime import datetime, timedelta

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=history_dates, y=history_close, mode="lines",
        name="COKE",
        line=dict(color=WH_NAVY, width=2.2),
        hovertemplate="%{x|%b %d, %Y}<br>$%{y:.2f}<extra></extra>",
    ))

    if history_dates:
        anchor_date = history_dates[-1]
    else:
        anchor_date = datetime.now()

    bull = next(s for s in scenarios if s["label"] == "Bull")
    base = next(s for s in scenarios if s["label"] == "Base")
    bear = next(s for s in scenarios if s["label"] == "Bear")

    # Single Wolf Hill blue cone fill — outer envelope (Bull-to-Bear) shaded once
    fig.add_trace(go.Scatter(
        x=[anchor_date, target_date, target_date, anchor_date],
        y=[current_price, bull["target"], bear["target"], current_price],
        fill="toself", fillcolor="rgba(48, 63, 85, 0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False, hoverinfo="skip",
    ))

    # Three forecast lines (kept distinct so each scenario reads)
    line_specs = [
        ("Bull", bull, WH_GREEN, "solid"),
        ("Base", base, WH_NAVY, "dash"),
        ("Bear", bear, WH_ACCENT, "solid"),
    ]
    for label, scen, color, dash in line_specs:
        fig.add_trace(go.Scatter(
            x=[anchor_date, target_date],
            y=[current_price, scen["target"]],
            mode="lines",
            name=f"{label}: ${scen['target']:.0f} ({scen['ret']*100:+.1f}%)",
            line=dict(color=color, width=2.5, dash=dash),
            hovertemplate=f"<b>{label}</b><br>Target: $%{{y:.2f}}<br>Return: {scen['ret']*100:+.1f}%<extra></extra>",
        ))
        fig.add_annotation(
            x=target_date, y=scen["target"],
            text=f"<b>{label}</b><br>${scen['target']:.0f} • {scen['ret']*100:+.1f}%",
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(color=color, size=11),
            xshift=8,
        )

    fig.add_trace(go.Scatter(
        x=[anchor_date], y=[current_price],
        mode="markers+text",
        name=f"Spot: ${current_price:.2f}",
        marker=dict(color=WH_NAVY, size=12, line=dict(width=2, color="white")),
        text=[f"${current_price:.2f}"], textposition="top center",
        textfont=dict(color=WH_NAVY, size=11),
        hoverinfo="skip",
        showlegend=False,
    ))

    # Custom range buttons (updatemenus supports relayout; rangeselector doesn't)
    def _btn_args(start_dt):
        return [{"xaxis.range": [start_dt.isoformat(), target_date.isoformat()],
                 "yaxis.autorange": True}]

    earliest = history_dates[0] if history_dates else anchor_date
    range_buttons = [
        dict(label="1D",  method="relayout", args=_btn_args(anchor_date - timedelta(days=1))),
        dict(label="5D",  method="relayout", args=_btn_args(anchor_date - timedelta(days=5))),
        dict(label="1M",  method="relayout", args=_btn_args(anchor_date - timedelta(days=31))),
        dict(label="6M",  method="relayout", args=_btn_args(anchor_date - timedelta(days=183))),
        dict(label="YTD", method="relayout", args=_btn_args(datetime(anchor_date.year, 1, 1))),
        dict(label="1Y",  method="relayout", args=_btn_args(anchor_date - timedelta(days=365))),
        dict(label="5Y",  method="relayout", args=_btn_args(anchor_date - timedelta(days=365 * 5))),
        dict(label="MAX", method="relayout", args=_btn_args(earliest)),
    ]

    # Google Finance-style: subtle pills, gray text, active highlighted
    fig.update_layout(
        updatemenus=[dict(
            type="buttons",
            direction="right",
            x=0, xanchor="left",
            y=1.0, yanchor="top",
            showactive=True,
            pad=dict(l=4, r=4, t=4, b=4),
            bgcolor="#f1f3f4",
            bordercolor="#dadce0",
            borderwidth=0,
            font=dict(size=11, color="#5f6368", family="Roboto, Arial, sans-serif"),
            buttons=range_buttons,
        )]
    )

    fig.update_yaxes(title="Price ($)", tickprefix="$")
    fig.update_xaxes(
        title="",
        range=_range(anchor_date - timedelta(days=365)),  # default: 1Y + cone
    )
    fig = _apply_style(
        fig,
        "COKE — Price History & Forecast Cone",
        f"Spot: ${current_price:.2f} • Targets via 2026 YE return scenarios (EPS-based)",
        height=560,
    )
    # Cone-specific overrides: room for buttons below subtitle, room for target labels on right,
    # hide legend (redundant with annotations at the right edge of the cone)
    fig.update_layout(
        margin=dict(l=60, r=130, t=160, b=60),
        showlegend=False,
    )
    return fig


def aluminum_sensitivity_curve(
    base_all_in_price: float,
    annual_cans_cases_mm: float,
    kg_per_can_case: float,
    base_eps_2026: float,
    diluted_shares: float,
    tax_rate: float = 0.25,
    figure_num: int = 0,
) -> go.Figure:
    """Curve: 2026 EPS as a function of all-in aluminum price. Spend = cases × KG/case × $/MT."""
    annual_kg_mm = annual_cans_cases_mm * kg_per_can_case  # mm KG
    annual_mt = annual_kg_mm * 1_000  # MT (since 1 MT = 1000 KG, mm KG × 1000 = thousands of MT, but mm KG × 1000 = M kg = thousand MT? Let me re-derive)
    # Correct math: cases (mm) × KG/case = mm KG. mm KG / 1000 = '000 MT. So MT = mm KG × 1000.
    # Wait: 1 mm KG = 1,000,000 KG = 1000 MT. So MT = mm_KG × 1000. Confirmed.
    annual_mt = annual_kg_mm * 1_000

    pct_range = np.linspace(-0.5, 0.5, 41)
    prices = base_all_in_price * (1 + pct_range)
    base_spend_M = annual_mt * base_all_in_price / 1_000_000  # spend in $M
    new_spends_M = annual_mt * prices / 1_000_000
    delta_spend_M = new_spends_M - base_spend_M
    delta_eps = -delta_spend_M * (1 - tax_rate) / diluted_shares
    eps = base_eps_2026 + delta_eps

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=prices, y=eps, mode="lines", name="2026 EPS",
        line=dict(color=WH_NAVY, width=3),
        hovertemplate="$%{x:,.0f}/MT → 2026 EPS $%{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[base_all_in_price], y=[base_eps_2026], mode="markers+text",
        name=f"Base (${base_all_in_price:,.0f}/MT)",
        marker=dict(color=WH_ACCENT, size=14, line=dict(width=2, color="white")),
        text=["Base"], textposition="top center",
        textfont=dict(color=WH_ACCENT, size=12),
        hoverinfo="skip",
    ))

    fig.update_xaxes(title="All-in Aluminum Price ($/MT)", tickprefix="$", separatethousands=True)
    fig.update_yaxes(title="2026 Adj. EPS ($)", tickprefix="$")
    return _apply_style(
        fig,
        f"Figure {figure_num}. 2026 EPS Sensitivity to Aluminum",
        f"{annual_cans_cases_mm:.0f}M can-cases × {kg_per_can_case:.2f} KG/case × $/MT • after-tax @ {int(tax_rate*100)}%",
        height=440,
    )
