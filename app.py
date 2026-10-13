"""Bilingual Streamlit dashboard for the BTC seven-state regime strategy."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from backtester import run_backtest
from charts import build_equity_chart, build_market_chart
from config import CONFIG
from data_loader import MarketDataError, latest_snapshot_path, load_market_data
from i18n import (
    TRADE_COLUMN_LABELS,
    localize_confirmation,
    localize_exit_reason,
    localize_position,
    localize_regime,
    tr,
)
from indicators import CONFIRMATION_COLUMNS, calculate_indicators
from regime_model import fit_walk_forward_regime_model


st.set_page_config(page_title="BTC 市场状态终端 | Regime Terminal", page_icon="₿", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #07101f; }
    [data-testid="stMetric"] { background: #111827; border: 1px solid #263244; padding: 14px; border-radius: 12px; }
    .signal-card { padding: 20px; border-radius: 14px; border: 1px solid #334155; background: linear-gradient(135deg,#111827,#0f172a); }
    .signal { font-size: 2rem; font-weight: 750; margin: 0; }
    .muted { color: #94a3b8; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def get_data() -> pd.DataFrame:
    return load_market_data()


@st.cache_resource(show_spinner=False)
def analyse(data: pd.DataFrame):
    enriched = calculate_indicators(data)
    regimes = fit_walk_forward_regime_model(enriched)
    result = run_backtest(regimes.frame)
    return regimes, result


def pct(value: float) -> str:
    return f"{value:+.2%}"


with st.sidebar:
    locale = st.segmented_control(
        "语言 / Language",
        options=["zh", "en"],
        default="zh",
        required=True,
        format_func=lambda value: {"zh": "中文", "en": "English"}[value],
        key="language",
        width="stretch",
        bind="query-params",
    )

st.title(tr(locale, "app_title"))
st.caption(tr(locale, "app_caption"))

with st.sidebar:
    st.header(tr(locale, "controls"))
    chart_days = st.select_slider(
        tr(locale, "chart_window"),
        options=[30, 90, 180, 365, 730],
        value=90,
        format_func=lambda value: tr(locale, "days", value=value),
    )
    force_refresh = st.button(tr(locale, "refresh"), width="stretch")
    st.divider()
    st.caption(tr(locale, "research_only"))
    st.caption(tr(locale, "execution_assumption"))

try:
    with st.spinner(tr(locale, "loading")):
        if force_refresh:
            market_data = load_market_data(force_refresh=True)
            get_data.clear()
            analyse.clear()
            st.toast(tr(locale, "refresh_success"), icon=":material/check_circle:")
        else:
            market_data = get_data()
        regime_result, backtest = analyse(market_data)
except (MarketDataError, ValueError, RuntimeError) as exc:
    st.error(tr(locale, "load_error", error=exc))
    st.stop()

latest = backtest.frame.iloc[-1]
position_color = "#22c55e" if backtest.current_position == "Long" else "#cbd5e1"
current_regime = regime_result.current_regime
current_confirmations = int(latest["Confirmation_Count"])
regime_color = "#22c55e" if current_regime == "Bull Run" else "#ef4444" if current_regime == "Bear / Crash" else "#f59e0b"

if backtest.current_position == "Long" and current_regime == "Bear / Crash":
    action_key = "action_exit"
    meaning_key = "meaning_exit"
    action_color = "#ef4444"
elif backtest.current_position == "Cash" and current_regime == "Bull Run" and current_confirmations >= CONFIG.required_confirmations:
    action_key = "action_enter"
    meaning_key = "meaning_enter"
    action_color = "#22c55e"
elif backtest.current_position == "Long":
    action_key = "action_hold"
    meaning_key = "meaning_hold"
    action_color = "#38bdf8"
else:
    action_key = "action_wait"
    meaning_key = "meaning_wait"
    action_color = "#f59e0b"

left, middle, right = st.columns(3)
with left:
    st.markdown(
        f'<div class="signal-card"><div class="muted">{tr(locale, "current_signal")}</div>'
        f'<p class="signal" style="color:{position_color}">{localize_position(backtest.current_position, locale)}</p></div>',
        unsafe_allow_html=True,
    )
with middle:
    st.markdown(
        f'<div class="signal-card"><div class="muted">{tr(locale, "market_regime", state=regime_result.current_state)}</div>'
        f'<p class="signal" style="color:{regime_color}">{localize_regime(current_regime, locale)}</p></div>',
        unsafe_allow_html=True,
    )
with right:
    st.markdown(
        f'<div class="signal-card"><div class="muted">{tr(locale, "next_action")}</div>'
        f'<p class="signal" style="color:{action_color}">{tr(locale, action_key)}</p></div>',
        unsafe_allow_html=True,
    )

with st.container(border=True):
    st.subheader(tr(locale, "what_it_tells"))
    st.markdown(tr(locale, meaning_key, count=current_confirmations))
    st.caption(tr(locale, "walk_forward_note"))
    st.caption(
        tr(
            locale,
            "model_asof",
            trained=f"{regime_result.current_model_trained_through:%Y-%m-%d %H:%M}",
            observed=f"{regime_result.current_observation_time:%Y-%m-%d %H:%M}",
        )
    )
    snapshot = latest_snapshot_path()
    if snapshot is not None:
        st.caption(tr(locale, "snapshot", name=snapshot.name))

metric_cols = st.columns(4)
metric_cols[0].metric(
    tr(locale, "total_return"),
    pct(backtest.metrics["Total Return"]),
    tr(locale, "final_equity", value=backtest.metrics["Final Equity"]),
)
metric_cols[1].metric(
    tr(locale, "alpha"),
    pct(backtest.metrics["Alpha vs Buy & Hold"]),
    tr(locale, "buy_hold_short", value=pct(backtest.metrics["Buy & Hold Return"])),
)
metric_cols[2].metric(
    tr(locale, "win_rate"),
    f'{backtest.metrics["Win Rate"]:.1%}',
    tr(locale, "closed_trades", value=int(backtest.metrics["Closed Trades"])),
)
metric_cols[3].metric(tr(locale, "max_drawdown"), f'{backtest.metrics["Max Drawdown"]:.2%}')

cutoff = backtest.frame.index[-1] - pd.Timedelta(days=chart_days)
chart_frame = backtest.frame.loc[backtest.frame.index >= cutoff]
st.plotly_chart(build_market_chart(chart_frame, locale), width="stretch", config={"displaylogo": False})
st.plotly_chart(build_equity_chart(backtest.frame, locale), width="stretch", config={"displaylogo": False})

tab1, tab2, tab3 = st.tabs(
    [tr(locale, "confirmations_tab"), tr(locale, "trade_log_tab"), tr(locale, "hmm_states_tab")]
)
with tab1:
    confirmation_table = pd.DataFrame(
        {
            tr(locale, "condition"): [localize_confirmation(column, locale) for column in CONFIRMATION_COLUMNS],
            tr(locale, "status"): [
                tr(locale, "pass") if bool(latest[column]) else tr(locale, "fail") for column in CONFIRMATION_COLUMNS
            ],
        }
    )
    st.subheader(tr(locale, "confirmations_passed", value=int(latest["Confirmation_Count"])))
    st.dataframe(confirmation_table, hide_index=True, width="stretch")
with tab2:
    if backtest.trades.empty:
        st.info(tr(locale, "no_closed_trades"))
    else:
        display_trades = backtest.trades.sort_values("Exit Time", ascending=False).copy()
        for column in ["Unlevered Return", "Leveraged Return"]:
            display_trades[column] = display_trades[column].map(lambda value: f"{value:.2%}")
        display_trades["Exit Regime"] = display_trades["Exit Regime"].map(
            lambda value: localize_regime(str(value), locale)
        )
        display_trades["Exit Reason"] = display_trades["Exit Reason"].map(
            lambda value: localize_exit_reason(str(value), locale)
        )
        if locale == "zh":
            display_trades = display_trades.rename(columns=TRADE_COLUMN_LABELS)
        st.dataframe(display_trades, hide_index=True, width="stretch")
with tab3:
    states = regime_result.state_statistics.copy()
    states[tr(locale, "state_label")] = states["Label"].map(lambda value: localize_regime(str(value), locale))
    states[tr(locale, "mean_return")] = states["Mean_Return"].map(
        lambda value: f"{value:.5%}" if pd.notna(value) else tr(locale, "not_available")
    )
    states[tr(locale, "mean_range")] = states["Mean_Range"].map(
        lambda value: f"{value:.3%}" if pd.notna(value) else tr(locale, "not_available")
    )
    states = states.rename(columns={"Observations": tr(locale, "observations")})
    states.index.name = tr(locale, "state")
    st.dataframe(
        states[
            [
                tr(locale, "state_label"),
                tr(locale, "mean_return"),
                tr(locale, "mean_range"),
                tr(locale, "observations"),
            ]
        ],
        width="stretch",
    )

st.caption(
    tr(
        locale,
        "footer",
        start=f"{market_data.index[0]:%Y-%m-%d %H:%M}",
        end=f"{market_data.index[-1]:%Y-%m-%d %H:%M}",
        rows=len(market_data),
        evaluation=f"{regime_result.evaluation_start:%Y-%m-%d %H:%M}",
        hours=CONFIG.cooldown_hours,
    )
)
