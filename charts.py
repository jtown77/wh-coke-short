"""Plotly chart builders. Each function returns a go.Figure ready to st.plotly_chart()."""
from __future__ import annotations

import plotly.graph_objects as go

WH_NAVY = "#303f55"
WH_NAVY_LIGHT = "#5e6e85"
WH_ACCENT = "#c0392b"
WH_GRAY = "#8b95a3"
WH_BG = "#ffffff"
WH_GRID = "#e7eaef"


def _apply_style(fig: go.Figure, title: str, *, height: int = 480) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=WH_NAVY, family="sans serif"), x=0.0, xanchor="left"),
        paper_bgcolor=WH_BG,
        plot_bgcolor=WH_BG,
        font=dict(family="sans serif", color="#1a2230", size=12),
        margin=dict(l=50, r=30, t=70, b=50),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor=WH_GRID, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=WH_GRID, zeroline=False)
    return fig
