"""Plotly chart builders. Each function returns a go.Figure ready for st.plotly_chart()."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

WH_NAVY = "#303F55"
WH_NAVY_LIGHT = "#5E6E85"
WH_ACCENT = "#C0392B"
WH_AMBER = "#D49A3A"
WH_GREEN = "#3F7A4E"
WH_GRAY = "#6B6B6B"
WH_GRAY_LIGHT = "#C7CCD3"
WH_INK = "#1A1A1A"
WH_BG = "#FFFFFF"
WH_GRID = "#E5E0D8"


def _apply_style(fig: go.Figure, title: str, subtitle: str | None = None, height: int = 460) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" + (f"<br><span style='font-size:13px;color:{WH_GRAY};font-weight:400;font-family:Inter,sans-serif'>{subtitle}</span>" if subtitle else ""),
            font=dict(size=22, color=WH_INK, family="Source Serif 4, Georgia, serif"),
            x=0.0, xanchor="left", y=0.96, yanchor="top",
            pad=dict(t=10, b=10),
        ),
        paper_bgcolor=WH_BG,
        plot_bgcolor=WH_BG,
        font=dict(family="Inter, sans-serif", color=WH_INK, size=12),
        margin=dict(l=70, r=40, t=110 if subtitle else 80, b=70),
        height=height,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(size=11, family="Inter, sans-serif"),
        ),
        hovermode="closest",
        dragmode=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor=WH_GRID, zeroline=False, linecolor=WH_GRID, fixedrange=True)
    fig.update_yaxes(showgrid=True, gridcolor=WH_GRID, zeroline=True, zerolinecolor=WH_GRAY_LIGHT, zerolinewidth=1, linecolor=WH_GRID, fixedrange=True)
    return fig


# Plotly config to keep charts non-interactive (just hover tooltips, pointer cursor)
STATIC_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
    "showAxisDragHandles": False,
    "showTips": False,
    "staticPlot": False,  # keep hover, just no drag/zoom
}


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

    fig.update_xaxes(title=dict(text="Avg Sales / Case YoY %", standoff=18), ticksuffix="%")
    fig.update_yaxes(title="Case Volume YoY %", ticksuffix="%")
    fig = _apply_style(
        fig,
        f"Figure {figure_num}. {segment} Beverages — Demand Elasticity",
        f"Quarterly Price vs. Volume YoY % • {labels[0]} – {labels[-1]}",
        height=520,
    )
    fig.update_layout(margin=dict(l=70, r=40, t=110, b=95))
    return fig


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

    series = [
        ("Sparkling Volume", seg["sparkling_volume_yoy"][:n], WH_NAVY, "solid"),
        ("Sparkling Price", seg["sparkling_price_yoy"][:n], WH_NAVY, "dash"),
        ("Still Volume", seg["still_volume_yoy"][:n], WH_ACCENT, "solid"),
        ("Still Price", seg["still_price_yoy"][:n], WH_ACCENT, "dash"),
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
        "Sparkling and Still • Volume (solid) vs Price (dashed) • historicals through Q4 2025",
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
    """Two-panel chart: 1-year daily history (left) + Bull/Base/Bear cone (right)."""
    from datetime import datetime, timedelta

    from plotly.subplots import make_subplots

    def _strip(d):
        return d.replace(tzinfo=None) if hasattr(d, "tzinfo") and d.tzinfo else d

    history_dates_n = [_strip(d) for d in history_dates]
    target_date = _strip(target_date)

    # Filter to last 365 days
    anchor_date = history_dates_n[-1] if history_dates_n else datetime.now()
    one_year_ago = anchor_date - timedelta(days=365)
    paired = [(d, c) for d, c in zip(history_dates_n, history_close)
              if d >= one_year_ago and c is not None and c > 0]
    hist_x = [p[0] for p in paired]
    hist_y = [p[1] for p in paired]

    bull = next(s for s in scenarios if s["label"] == "Bull")
    base = next(s for s in scenarios if s["label"] == "Base")
    bear = next(s for s in scenarios if s["label"] == "Bear")

    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=False,
        horizontal_spacing=0.0,
        column_widths=[0.78, 0.22],
    )

    # LEFT panel: 1-year daily history
    fig.add_trace(go.Scatter(
        x=hist_x, y=hist_y, mode="lines",
        line=dict(color=WH_NAVY, width=2.2),
        hovertemplate="%{x|%b %d, %Y}<br>$%{y:.2f}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    # RIGHT panel: cone fill envelope
    fig.add_trace(go.Scatter(
        x=[anchor_date, target_date, target_date, anchor_date],
        y=[current_price, bull["target"], bear["target"], current_price],
        fill="toself", fillcolor="rgba(48, 63, 85, 0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=2)

    # RIGHT panel: three scenario lines + labels
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
            line=dict(color=color, width=2.5, dash=dash),
            hovertemplate=f"<b>{label}</b><br>Target: $%{{y:.2f}}<br>Return: {scen['ret']*100:+.1f}%<extra></extra>",
            showlegend=False,
        ), row=1, col=2)
        fig.add_annotation(
            x=target_date, y=scen["target"],
            xref="x2", yref="y2",
            text=f"<b>{label}</b><br>${scen['target']:.0f} • {scen['ret']*100:+.1f}%",
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(color=color, size=11),
            xshift=8,
        )

    # Spot marker at the panel boundary
    fig.add_trace(go.Scatter(
        x=[anchor_date], y=[current_price],
        mode="markers",
        marker=dict(color=WH_NAVY, size=11, line=dict(width=2, color="white")),
        hovertemplate=f"Spot: ${current_price:.2f}<extra></extra>",
        showlegend=False,
    ), row=1, col=2)

    # Yahoo-Finance-style current-price tag at the spot
    fig.add_annotation(
        x=anchor_date, y=current_price,
        xref="x2", yref="y2",
        text=f"<b>${current_price:.2f}</b>",
        showarrow=False,
        xanchor="left", yanchor="middle",
        xshift=6,
        bgcolor=WH_NAVY, bordercolor=WH_NAVY, borderwidth=1, borderpad=4,
        font=dict(color="white", size=11, family="Source Sans Pro, sans-serif"),
    )

    # Unified y-range across both panels so gridlines align visually.
    # Range covers everything the user needs to see: 1Y price history + Bear/Bull targets.
    if hist_y:
        all_ys = hist_y + [current_price, bull["target"], bear["target"]]
    else:
        all_ys = [current_price, bull["target"], bear["target"]]
    y_min_data, y_max_data = min(all_ys), max(all_ys)
    pad = max((y_max_data - y_min_data) * 0.06, 1.0)
    unified_y_range = [max(0.0, y_min_data - pad), y_max_data + pad]

    fig.update_yaxes(title="Price ($)", tickprefix="$", range=unified_y_range,
                     row=1, col=1, showline=False,
                     showgrid=True, gridcolor=WH_GRID)
    fig.update_yaxes(showticklabels=False, showline=False, range=unified_y_range,
                     row=1, col=2,
                     showgrid=True, gridcolor=WH_GRID, matches="y")
    fig.update_xaxes(title="", range=[one_year_ago.isoformat(), anchor_date.isoformat()],
                     row=1, col=1, showline=False,
                     showgrid=True, gridcolor=WH_GRID)
    fig.update_xaxes(title="", range=[anchor_date, target_date], showticklabels=False,
                     showline=False, row=1, col=2,
                     showgrid=True, gridcolor=WH_GRID)

    fig = _apply_style(
        fig,
        "COKE — 1-Year Price History & Forecast Cone",
        f"Spot: ${current_price:.2f} • Targets via 2026 YE return scenarios (EPS-based)",
        height=520,
    )
    fig.update_layout(
        margin=dict(l=60, r=130, t=110, b=60),
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
