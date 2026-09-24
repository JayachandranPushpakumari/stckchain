import pandas as pd

from services import bullish_patterns


def test_scan_requires_score_above_60_and_returns_pattern_matches(monkeypatch):
    candidates = pd.DataFrame([{"symbol": "MATCH", "total_score": 75}, {"symbol": "NONE", "total_score": 65}])
    prices = pd.DataFrame([{
        "date": pd.Timestamp("2026-01-01"), "open": 100.0, "high": 102.0,
        "low": 99.0, "close": 101.0, "volume": 200_000,
    }])
    calls = iter([candidates, prices, prices])
    monkeypatch.setattr(pd, "read_sql", lambda *args, **kwargs: next(calls).copy())
    pattern_calls = {"count": 0}
    def detect(frame):
        pattern_calls["count"] += 1
        return [{"label": "Flat Base", "reason": "Flat base matched"}] if pattern_calls["count"] == 1 else []
    monkeypatch.setattr(bullish_patterns, "detect_bullish_patterns", detect)
    result = bullish_patterns.scan_bullish_patterns()
    assert result["fundamental_candidates"] == 2
    assert result["matched_stocks"] == 1
    assert result["stocks"][0]["patterns"] == ["Flat Base"]
