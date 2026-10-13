"""Plotly chart builders for the Streamlit dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from i18n import tr


REGIME_COLORS = {
    "Bull Run": "rgba(34, 197, 94, 0.16)",
    "Bear / Crash": "rgba(239, 68, 68, 0.18)",
}


def _regime_spans(frame: pd.DataFrame):
    changes = frame["Regime"].ne(frame["Regime"].shift()).fillna(True).to_numpy(dtype=bool)
    groups = np.cumsum(changes)
    for _, segment in frame.groupby(groups):
        yield segment.index[0], segment.index[-1], str(segment["Regime"].iloc[0])


def build_market_chart(frame: pd.DataFrame, locale: str = "en") -> go.Figure:
    fig = go.Figure(
        go.Candlestick(
            x=frame.index,
            open=frame["Open"],
            high=frame["High"],
            low=frame["Low"],
            close=frame["Close"],
            name="BTC-USD",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
        )
    )
    for start, end, regime in _regime_spans(frame):
        color = REGIME_COLORS.get(regime)
        if color:
            fig.add_vrect(x0=start, x1=end + pd.Timedelta(hours=1), fillcolor=color, line_width=0, layer="below")

    entries = frame[frame["Position"].diff().fillna(frame["Position"]) == 1]
    exits = frame[frame["Position"].diff() == -1]
    fig.add_trace(
        go.Scatter(
            x=entries.index,
            y=entries["Close"],
            mode="markers",
            name=tr(locale, "entry"),
            marker=dict(symbol="triangle-up", size=11, color="#22c55e"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=exits.index,
            y=exits["Close"],
            mode="markers",
            name=tr(locale, "exit"),
            marker=dict(symbol="triangle-down", size=11, color="#ef4444"),
        )
    )
    fig.update_layout(
        height=620,
        template="plotly_dark",
        paper_bgcolor="#0b1220",
        plot_bgcolor="#111827",
        margin=dict(l=15, r=15, t=50, b=15),
        title=tr(locale, "market_chart_title"),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(orientation="h", y=1.02, x=0),
        yaxis_title="USD",
    )
    return fig


def build_equity_chart(frame: pd.DataFrame, locale: str = "en") -> go.Figure:
    benchmark = 10_000 * frame["Close"] / frame["Close"].iloc[0]
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    fig.add_trace(
        go.Scatter(x=frame.index, y=frame["Equity"], name=tr(locale, "strategy"), line=dict(color="#38bdf8", width=2))
    )
    fig.add_trace(
        go.Scatter(x=frame.index, y=benchmark, name=tr(locale, "buy_hold"), line=dict(color="#94a3b8", dash="dot"))
    )
    fig.update_layout(
        height=360,
        template="plotly_dark",
        paper_bgcolor="#0b1220",
        plot_bgcolor="#111827",
        margin=dict(l=15, r=15, t=45, b=15),
        title=tr(locale, "equity_chart_title"),
        hovermode="x unified",
        yaxis_title=tr(locale, "account_value"),
    )
    return fig

