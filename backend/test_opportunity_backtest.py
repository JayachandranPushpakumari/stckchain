import pandas as pd

from services.opportunity_backtest import _metrics, _regime_for_row, _simulate_trade


def test_regime_classification_matches_opportunity_rules():
    assert _regime_for_row(120, 110, 100, 60) == ("BULL", 10)
    assert _regime_for_row(105, 110, 100, 50) == ("NEUTRAL", 6)
    assert _regime_for_row(90, 100, 110, 38) == ("WEAK", 3)
    assert _regime_for_row(90, 100, 110, 30) == ("BEAR", 0)


def test_trade_enters_on_next_bar_and_stops_conservatively():
    prices = pd.DataFrame([
        {"date": pd.Timestamp("2025-01-01"), "open": 100, "high": 105, "low": 99, "close": 104},
        {"date": pd.Timestamp("2025-01-02"), "open": 104, "high": 110, "low": 95, "close": 108},
    ])
    trade = _simulate_trade(prices, 0, 103, 106, 96, 109, 112)
    assert trade["entry_date"] == pd.Timestamp("2025-01-02")
    assert trade["exit_reason"] == "STOP_LOSS"
    assert trade["target_1_hit"] is False


def test_trade_skips_gap_above_entry_range():
    prices = pd.DataFrame([
        {"date": pd.Timestamp("2025-01-01"), "open": 100, "high": 105, "low": 99, "close": 104},
        {"date": pd.Timestamp("2025-01-02"), "open": 108, "high": 110, "low": 107, "close": 109},
    ])
    assert _simulate_trade(prices, 0, 103, 106, 96, 109, 112) is None


def test_metrics_include_targets_stops_mfe_and_mae():
    metrics = _metrics([
        {"return_pct": 6, "target_1_hit": True, "target_2_hit": True, "stop_hit": False, "exit_reason": "TARGET_2", "mfe_pct": 7, "mae_pct": -1},
        {"return_pct": -3, "target_1_hit": False, "target_2_hit": False, "stop_hit": True, "exit_reason": "STOP_LOSS", "mfe_pct": 1, "mae_pct": -4},
    ])
    assert metrics["total_trades"] == 2
    assert metrics["win_rate"] == 50
    assert metrics["target_1_rate"] == 50
    assert metrics["stop_loss_rate"] == 50
    assert metrics["avg_mfe"] == 4
    assert metrics["avg_mae"] == -2.5
