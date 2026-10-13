"""English and Simplified Chinese display text for the dashboard."""

from __future__ import annotations


TEXT = {
    "en": {
        "app_title": "BTC Regime Terminal",
        "app_caption": "7-state Gaussian HMM · 8-factor confirmation · 2.5× simulated leverage",
        "controls": "Controls",
        "chart_window": "Chart window",
        "days": "{value} days",
        "refresh": "Refresh Yahoo data",
        "research_only": "Research/backtest only. No brokerage connection and no live order execution.",
        "execution_assumption": "Signals are confirmed at the hourly close and executed at the next hourly open; fees and slippage are excluded.",
        "loading": "Loading closed BTC-USD candles and running the causal walk-forward HMM…",
        "load_error": "Unable to load the dashboard: {error}",
        "refresh_success": "A new closed-candle snapshot was saved. Old history remains locked.",
        "current_signal": "SIMULATED POSITION",
        "market_regime": "MARKET REGIME · STATE {state}",
        "next_action": "NEXT ACTION",
        "action_enter": "ENTER NEXT OPEN",
        "action_exit": "EXIT NEXT OPEN",
        "action_hold": "HOLD",
        "action_wait": "WAIT",
        "what_it_tells": "What this model is telling you",
        "meaning_enter": "The latest closed candle is classified as Bull Run and {count}/8 confirmations passed. The strategy may enter at the next hourly open.",
        "meaning_exit": "The latest closed candle is Bear / Crash while the simulation is long. The strategy exits at the next hourly open.",
        "meaning_hold": "The simulation is already long and no Bear / Crash exit signal is present, so it keeps holding.",
        "meaning_wait": "The strategy is in cash. The latest state and confirmations do not satisfy the Bull Run plus 7/8 entry gate.",
        "walk_forward_note": "Historical metrics are walk-forward only: 180 days of trailing training, retrained every 30 days, with no future candles used for past decisions.",
        "model_asof": "Active walk-forward model trained through {trained}; latest classified closed candle {observed} UTC.",
        "snapshot": "Locked data snapshot: {name}",
        "total_return": "Total return",
        "final_equity": "Equity ${value:,.0f}",
        "alpha": "Alpha vs buy & hold",
        "buy_hold_short": "B&H {value}",
        "win_rate": "Win rate",
        "closed_trades": "{value} closed trades",
        "max_drawdown": "Max drawdown",
        "confirmations_tab": "Confirmations",
        "trade_log_tab": "Trade log",
        "hmm_states_tab": "HMM states",
        "confirmations_passed": "{value}/8 confirmations passed",
        "no_closed_trades": "No closed trades in the selected history.",
        "condition": "Condition",
        "status": "Status",
        "pass": "PASS",
        "fail": "FAIL",
        "state_label": "Label",
        "state": "State",
        "mean_return": "Mean return",
        "mean_range": "Mean range",
        "observations": "Observations",
        "not_available": "n/a",
        "footer": "Closed-candle data: {start} to {end} UTC · {rows:,} hourly candles · walk-forward evaluation starts {evaluation} UTC · {hours}h cooldown",
        "market_chart_title": "BTC-USD · Hourly regime map",
        "entry": "Entry",
        "exit": "Exit",
        "equity_chart_title": "Equity curve",
        "strategy": "Strategy",
        "buy_hold": "Buy & hold",
        "account_value": "Account value (USD)",
    },
    "zh": {
        "app_title": "BTC 市场状态交易终端",
        "app_caption": "7 状态高斯 HMM · 8 条件确认 · 2.5 倍模拟杠杆",
        "controls": "控制面板",
        "chart_window": "图表时间范围",
        "days": "{value} 天",
        "refresh": "刷新 Yahoo 数据",
        "research_only": "仅用于研究和回测，不连接券商或交易所，也不会执行真实订单。",
        "execution_assumption": "成交假设：小时 K 线收盘后确认信号，下一根小时 K 线开盘成交；未计入手续费和滑点。",
        "loading": "正在加载已收盘的 BTC-USD K 线并运行因果 walk-forward HMM…",
        "load_error": "无法加载仪表盘：{error}",
        "refresh_success": "新的已收盘数据快照已保存，旧历史数据保持锁定。",
        "current_signal": "回测模拟持仓",
        "market_regime": "市场状态 · 状态 {state}",
        "next_action": "下一步动作",
        "action_enter": "下一小时开盘进场",
        "action_exit": "下一小时开盘平仓",
        "action_hold": "继续持有",
        "action_wait": "继续等待",
        "what_it_tells": "这个模型现在告诉你什么",
        "meaning_enter": "最新一根已收盘 K 线被识别为强势牛市，并且通过 {count}/8 项确认条件；策略允许在下一小时开盘进场。",
        "meaning_exit": "最新一根已收盘 K 线进入熊市 / 暴跌状态，并且模拟账户正在持仓；策略将在下一小时开盘平仓。",
        "meaning_hold": "模拟账户已经持仓，目前没有出现熊市 / 暴跌退出信号，因此继续持有。",
        "meaning_wait": "策略当前空仓；最新市场状态和确认条件还没有同时满足“强势牛市 + 至少 7/8 项”的进场门槛。",
        "walk_forward_note": "历史指标只使用 walk-forward 结果：每次用此前 180 天训练，每 30 天重新训练；过去的决策不会使用未来 K 线。",
        "model_asof": "当前 walk-forward 模型训练数据截至 {trained}；最新识别的是 {observed} UTC 已收盘 K 线。",
        "snapshot": "锁定数据快照：{name}",
        "total_return": "总收益",
        "final_equity": "账户权益 ${value:,.0f}",
        "alpha": "相对买入并持有的超额收益",
        "buy_hold_short": "买入并持有 {value}",
        "win_rate": "胜率",
        "closed_trades": "{value} 笔已平仓交易",
        "max_drawdown": "最大回撤",
        "confirmations_tab": "确认条件",
        "trade_log_tab": "交易日志",
        "hmm_states_tab": "HMM 状态",
        "confirmations_passed": "8 项条件中通过 {value} 项",
        "no_closed_trades": "所选历史区间内没有已平仓交易。",
        "condition": "条件",
        "status": "结果",
        "pass": "通过",
        "fail": "未通过",
        "state_label": "状态标签",
        "state": "状态编号",
        "mean_return": "平均收益",
        "mean_range": "平均振幅",
        "observations": "样本数",
        "not_available": "无数据",
        "footer": "已收盘数据：{start} 至 {end} UTC · {rows:,} 根小时 K 线 · walk-forward 评估从 {evaluation} UTC 开始 · 冷却 {hours} 小时",
        "market_chart_title": "BTC-USD · 小时级市场状态图",
        "entry": "进场",
        "exit": "平仓",
        "equity_chart_title": "账户权益曲线",
        "strategy": "策略",
        "buy_hold": "买入并持有",
        "account_value": "账户价值（美元）",
    },
}


CONFIRMATION_LABELS = {
    "RSI < 90": "RSI < 90",
    "Momentum > 1%": "动量 > 1%",
    "Volatility < 6%": "波动率 < 6%",
    "Volume > SMA20": "成交量 > 20 周期均量",
    "ADX > 25": "ADX > 25",
    "Price > EMA50": "价格 > EMA 50",
    "Price > EMA200": "价格 > EMA 200",
    "MACD > Signal": "MACD > 信号线",
}


TRADE_COLUMN_LABELS = {
    "Entry Time": "进场时间",
    "Exit Time": "平仓时间",
    "Entry Price": "进场价格",
    "Exit Price": "平仓价格",
    "Entry Confirmations": "进场确认数",
    "Exit Regime": "平仓时市场状态",
    "Exit Reason": "平仓原因",
    "Unlevered Return": "未加杠杆收益",
    "Leveraged Return": "加杠杆收益",
    "PnL": "盈亏",
    "Capital After": "平仓后资金",
    "Holding Hours": "持仓小时数",
}


def tr(locale: str, key: str, **values: object) -> str:
    """Return localized text, falling back to English for unknown locales."""
    language = locale if locale in TEXT else "en"
    return TEXT[language][key].format(**values)


def localize_position(position: str, locale: str) -> str:
    if locale != "zh":
        return position.upper()
    return {"Long": "做多", "Cash": "空仓"}.get(position, position)


def localize_regime(regime: str, locale: str) -> str:
    if locale != "zh":
        return regime
    if regime == "Bull Run":
        return "强势牛市"
    if regime == "Bear / Crash":
        return "熊市 / 暴跌"
    if regime.startswith("Neutral "):
        return f"中性状态 {regime.removeprefix('Neutral ')}"
    return regime


def localize_confirmation(condition: str, locale: str) -> str:
    return CONFIRMATION_LABELS.get(condition, condition) if locale == "zh" else condition


def localize_exit_reason(reason: str, locale: str) -> str:
    if locale == "zh" and reason == "Bear / Crash regime":
        return "进入熊市 / 暴跌状态"
    return reason
