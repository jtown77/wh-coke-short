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
WH_BG = "#ffffff"
WH_GRID = "#e7eaef"


def _apply_style(fig: go.Figure, title: str, subtitle: str | None = None, height: int = 480) -> go.Figure:
    title_text = title if not subtitle else f"{title}<br><sup style='color:{WH_GRAY};font-weight:400'>{subtitle}</sup>"
    fig.update_layout(
        title=dict(text=title_text, font=dict(size=18, color=WH_NAVY, family="sans serif"), x=0.0, xanchor="left"),
        paper_bgcolor=WH_BG,
        plot_bgcolor=WH_BG,
        font=dict(family="sans serif", color="#1a2230", size=12),
        margin=dict(l=60, r=30, t=80, b=60),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor=WH_GRID, zeroline=False, linecolor=WH_GRID)
    fig.update_yaxes(showgrid=True, gridcolor=WH_GRID, zeroline=True, zerolinecolor=WH_GRAY, zerolinewidth=1, linecolor=WH_GRID)
    return fig


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


def elasticity_scatter(price_yoy: list, volume_yoy: list, quarter_labels: list, segment: str) -> go.Figure:
    """X = Avg Sales/Case YoY %, Y = Case Volume YoY %. Quarterly historical scatter with OLS trendline."""
    x, y, labels = _filter_pairs(price_yoy, volume_yoy, quarter_labels)
    if not x:
        fig = go.Figure()
        return _apply_style(fig, f"{segment} Beverages — Demand Elasticity", "No data available")

    color = WH_NAVY if segment == "Sparkling" else WH_ACCENT
    years = [int("20" + q.split()[-1]) for q in labels]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[xi * 100 for xi in x],
        y=[yi * 100 for yi in y],
        mode="markers",
        name="Quarterly observations",
        text=labels,
        marker=dict(
            size=11,
            color=years,
            colorscale=[[0, WH_GRAY], [1, color]],
            showscale=True,
            colorbar=dict(title=dict(text="Year", side="right"), thickness=12, len=0.6, x=1.02),
            line=dict(width=1, color="white"),
        ),
        hovertemplate="<b>%{text}</b><br>Price YoY: %{x:.1f}%<br>Volume YoY: %{y:.1f}%<extra></extra>",
    ))

    # OLS regression
    xa = np.array(x) * 100
    ya = np.array(y) * 100
    if len(xa) > 2:
        slope, intercept = np.polyfit(xa, ya, 1)
        x_line = np.linspace(min(xa) - 1, max(xa) + 1, 50)
        y_line = slope * x_line + intercept
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode="lines", name=f"OLS fit (slope = {slope:.2f})",
            line=dict(color=WH_GRAY, width=2, dash="dash"),
            hoverinfo="skip",
        ))

    fig.update_xaxes(title="Avg Sales / Case YoY %", ticksuffix="%")
    fig.update_yaxes(title="Case Volume YoY %", ticksuffix="%")
    return _apply_style(
        fig,
        f"{segment} Beverages — Demand Elasticity",
        f"Quarterly Price vs Volume YoY % ({labels[0]} – {labels[-1]})",
        height=520,
    )


def quarterly_yoy_chart(seg: dict) -> go.Figure:
    """Six-line chart: Sparkling, Still, Total — volume (solid) and price (dashed) YoY."""
    quarters = seg["quarters"]

    total_price_yoy = []
    rev = seg["total_revenue"]
    cases = seg["total_cases"]
    avg_price = [(r / c) if (r is not None and c not in (None, 0)) else None for r, c in zip(rev, cases)]
    for i, p in enumerate(avg_price):
        if i < 4 or p is None or avg_price[i - 4] in (None, 0):
            total_price_yoy.append(None)
        else:
            total_price_yoy.append(p / avg_price[i - 4] - 1)

    series = [
        ("Sparkling Volume", seg["sparkling_volume_yoy"], WH_NAVY, "solid"),
        ("Sparkling Price", seg["sparkling_price_yoy"], WH_NAVY, "dash"),
        ("Still Volume", seg["still_volume_yoy"], WH_ACCENT, "solid"),
        ("Still Price", seg["still_price_yoy"], WH_ACCENT, "dash"),
        ("Total Volume", seg["total_cases_yoy"], WH_GRAY, "solid"),
        ("Total Price (derived)", total_price_yoy, WH_GRAY, "dash"),
    ]

    fig = go.Figure()
    for name, vals, color, dash in series:
        ys = [v * 100 if v is not None else None for v in vals]
        fig.add_trace(go.Scatter(
            x=quarters, y=ys, mode="lines", name=name,
            line=dict(color=color, width=2, dash=dash),
            connectgaps=False,
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
        ))

    forecast_start = "Q1 26"
    if forecast_start in quarters:
        idx = quarters.index(forecast_start)
        fig.add_vline(x=idx - 0.5, line=dict(color=WH_GRAY, width=1, dash="dot"))
        fig.add_annotation(x=idx, y=1, yref="paper", text="Forecast →",
                           showarrow=False, xanchor="left", yanchor="bottom",
                           font=dict(color=WH_GRAY, size=11))

    fig.update_xaxes(title="", tickangle=-45, nticks=20)
    fig.update_yaxes(title="YoY % Change", ticksuffix="%")
    return _apply_style(
        fig,
        "Quarterly Price & Volume YoY Growth",
        "Sparkling, Still, and Total — historical actuals and Wolf Hill forecast",
        height=540,
    )


def aluminum_history_chart(quarters: list, lme: list, mwp: list, all_in: list) -> go.Figure:
    """Historical aluminum cost components ($/MT) — LME, Midwest Premium, All-in."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=quarters, y=lme, mode="lines", name="LME ($/MT)",
                             line=dict(color=WH_NAVY, width=2),
                             hovertemplate="<b>LME</b><br>%{x}: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=quarters, y=mwp, mode="lines", name="Midwest Premium ($/MT)",
                             line=dict(color=WH_AMBER, width=2),
                             hovertemplate="<b>MWP</b><br>%{x}: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=quarters, y=all_in, mode="lines", name="All-in US Price ($/MT)",
                             line=dict(color=WH_ACCENT, width=2.5),
                             hovertemplate="<b>All-in</b><br>%{x}: $%{y:,.0f}<extra></extra>"))

    forecast_start = "Q1 26"
    if forecast_start in quarters:
        idx = quarters.index(forecast_start)
        fig.add_vline(x=idx - 0.5, line=dict(color=WH_GRAY, width=1, dash="dot"))
        fig.add_annotation(x=idx, y=1, yref="paper", text="Forecast →",
                           showarrow=False, xanchor="left", yanchor="bottom",
                           font=dict(color=WH_GRAY, size=11))

    fig.update_xaxes(title="", tickangle=-45, nticks=20)
    fig.update_yaxes(title="$/MT", tickprefix="$", separatethousands=True)
    return _apply_style(
        fig,
        "Aluminum Cost Stack — Historical & Forecast",
        "LME base + Midwest Premium = All-in US Price (excl. CCK markup)",
        height=460,
    )


def aluminum_sensitivity_curve(
    base_all_in_price: float,
    base_aluminum_spend_2026: float,
    base_eps_2026: float,
    diluted_shares: float,
    tax_rate: float = 0.25,
) -> go.Figure:
    """Curve: 2026 EPS as a function of all-in aluminum price ($/MT). Assumes linear flow-through."""
    pct_range = np.linspace(-0.5, 0.5, 41)
    prices = base_all_in_price * (1 + pct_range)

    delta_spend = base_aluminum_spend_2026 * pct_range
    delta_net_income = -delta_spend * (1 - tax_rate)
    delta_eps = delta_net_income / diluted_shares
    eps = base_eps_2026 + delta_eps

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=prices, y=eps, mode="lines",
        name="2026 EPS",
        line=dict(color=WH_NAVY, width=3),
        hovertemplate="All-in $%{x:,.0f}/MT<br>2026 EPS: $%{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[base_all_in_price], y=[base_eps_2026], mode="markers+text",
        name=f"Base case (${base_all_in_price:,.0f}/MT, ${base_eps_2026:.2f})",
        marker=dict(color=WH_ACCENT, size=14, line=dict(width=2, color="white")),
        text=["Base"], textposition="top center",
        textfont=dict(color=WH_ACCENT, size=12),
        hoverinfo="skip",
    ))

    fig.update_xaxes(title="All-in Aluminum Price ($/MT)", tickprefix="$", separatethousands=True)
    fig.update_yaxes(title="2026 Adj. EPS ($)", tickprefix="$")
    return _apply_style(
        fig,
        "2026 EPS Sensitivity to Aluminum Price",
        f"Linear flow-through: ΔSpend = volume × ΔPrice, after-tax @ {int(tax_rate*100)}%",
        height=420,
    )
