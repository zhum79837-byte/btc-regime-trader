from i18n import localize_confirmation, localize_position, localize_regime, tr


def test_chinese_localization_covers_dynamic_strategy_labels():
    assert tr("zh", "total_return") == "总收益"
    assert localize_position("Long", "zh") == "做多"
    assert localize_position("Cash", "zh") == "空仓"
    assert localize_regime("Bull Run", "zh") == "强势牛市"
    assert localize_regime("Bear / Crash", "zh") == "熊市 / 暴跌"
    assert localize_regime("Neutral 4", "zh") == "中性状态 4"
    assert localize_confirmation("MACD > Signal", "zh") == "MACD > 信号线"


def test_english_version_preserves_original_internal_labels():
    assert tr("en", "total_return") == "Total return"
    assert localize_position("Long", "en") == "LONG"
    assert localize_regime("Bull Run", "en") == "Bull Run"
    assert localize_confirmation("MACD > Signal", "en") == "MACD > Signal"

