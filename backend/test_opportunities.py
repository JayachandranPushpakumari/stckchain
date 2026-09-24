import pandas as pd

from services import opportunities


def indicator_frame():
    rows = 250
    frame = pd.DataFrame({
        "open": [100.0] * rows,
        "high": [101.0] * rows,
        "low": [99.0] * rows,
        "close": [100.0] * rows,
        "volume": [200_000.0] * rows,
        "atr": [2.0] * rows,
        "ma20": [105.0] * rows,
        "ma50": [100.0] * rows,
        "rsi": [65.0] * rows,
        "volume_ratio": [2.5] * rows,
        "adx": [30.0] * rows,
        "high_20": [102.0] * rows,
    })
    frame.loc[rows - 1, "close"] = 104.0
    return frame


def test_build_opportunity_uses_atr_risk_structure(monkeypatch):
    frame = indicator_frame()
    monkeypatch.setattr(opportunities, "_price_history", lambda symbol: frame.copy())
    monkeypatch.setattr(opportunities, "calculate_indicators", lambda prices: prices)
    monkeypatch.setattr(opportunities, "detect_bullish_patterns", lambda prices: [{"label": "Flat Base", "reason": "Flat base breakout"}])
    regime = {"regime": "BULL", "score": 10, "reason": "Bull market"}
    result = opportunities._build_opportunity("TEST", 90, 90, 50_000_000, regime)
    assert result["entry_low"] == 104.0
    assert result["entry_high"] == 105.0
    assert result["stop_loss"] < result["entry_low"]
    assert result["target_1"] < result["target_2"]
    assert result["risk_reward"] == 2.0
    assert result["score"] >= 85
    assert result["status"] == "READY_FOR_REVIEW"


def test_non_bull_regime_does_not_block_pattern_opportunities(monkeypatch):
    universe = pd.DataFrame([{
        "symbol": "TEST", "data_quality_pass": True, "liquidity_pass": True,
        "fundamental_pass": True, "total_score": 90, "median_turnover": 50_000_000,
    }])
    monkeypatch.setattr(opportunities, "_eligible_universe", lambda: universe)
    monkeypatch.setattr(opportunities, "classify_market_regime", lambda: {"regime": "NEUTRAL", "score": 6})
    monkeypatch.setattr(opportunities, "_momentum_percentiles", lambda: {"TEST": 90})
    monkeypatch.setattr(opportunities, "_build_opportunity", lambda *args: {"symbol": "TEST", "score": 70})
    monkeypatch.setattr(pd, "read_sql", lambda *args, **kwargs: pd.DataFrame({"symbol": ["TEST"]}))
    result = opportunities.generate_breakout_opportunities(save_to_db=False)
    assert [item["symbol"] for item in result["opportunities"]] == ["TEST"]
    assert result["stage_counts"]["market_regime"] == 1
    assert result["stage_counts"]["chart_pattern"] == 1


def test_diagnostics_report_pattern_rejections(monkeypatch):
    candidates = pd.DataFrame([
        {"symbol": "PASS", "data_quality_pass": True, "liquidity_pass": True, "fundamental_pass": True, "total_score": 90, "median_turnover": 50_000_000},
        {"symbol": "FAIL", "data_quality_pass": True, "liquidity_pass": True, "fundamental_pass": True, "total_score": 90, "median_turnover": 50_000_000},
    ])
    monkeypatch.setattr(opportunities, "_breakout_candidates", lambda: candidates)
    monkeypatch.setattr(opportunities, "classify_market_regime", lambda: {"regime": "BULL", "score": 10})
    monkeypatch.setattr(opportunities, "_momentum_percentiles", lambda: {"PASS": 90, "FAIL": 90})
    monkeypatch.setattr(opportunities, "_price_history", lambda symbol: indicator_frame().copy().assign(symbol=symbol))

    def mock_detect(prices):
        return [{"label": "Flat Base", "reason": "flat"}] if prices is not None and prices["symbol"].iloc[0] == "PASS" else []

    monkeypatch.setattr(opportunities, "detect_bullish_patterns", mock_detect)
    monkeypatch.setattr(opportunities, "_build_opportunity", lambda symbol, score, *args: {"symbol": symbol, "score": 90} if symbol == "PASS" else None)
    result = opportunities.diagnose_breakout_opportunities()
    assert result["candidate_count"] == 2
    assert result["published_count"] == 1
    by_symbol = {d["symbol"]: d for d in result["diagnostics"]}
    assert by_symbol["PASS"]["opportunity"] is not None
    assert by_symbol["FAIL"]["rejection_reason"] == "no_bullish_chart_pattern"


def test_high_confidence_results_are_ranked(monkeypatch):
    universe = pd.DataFrame([
        {"symbol": "A", "data_quality_pass": True, "liquidity_pass": True, "fundamental_pass": True, "total_score": 90, "median_turnover": 50_000_000},
        {"symbol": "B", "data_quality_pass": True, "liquidity_pass": True, "fundamental_pass": True, "total_score": 90, "median_turnover": 50_000_000},
    ])
    monkeypatch.setattr(opportunities, "_eligible_universe", lambda: universe)
    monkeypatch.setattr(opportunities, "classify_market_regime", lambda: {"regime": "BULL", "score": 10})
    monkeypatch.setattr(opportunities, "_momentum_percentiles", lambda: {"A": 90, "B": 90})
    monkeypatch.setattr(pd, "read_sql", lambda *args, **kwargs: pd.DataFrame({"symbol": ["A", "B"]}))
    monkeypatch.setattr(opportunities, "_build_opportunity", lambda symbol, *args: {"symbol": symbol, "score": 90 if symbol == "A" else 88})
    result = opportunities.generate_breakout_opportunities(save_to_db=False)
    assert [item["symbol"] for item in result["opportunities"]] == ["A", "B"]
    assert [item["rank"] for item in result["opportunities"]] == [1, 2]
    assert result["stage_counts"]["high_confidence"] == 2
