import pandas as pd

from services import bullish_structures


def test_structure_requires_sufficient_history():
    prices = pd.DataFrame([{
        "date": pd.Timestamp("2026-01-01"), "open": 100.0, "high": 102.0,
        "low": 99.0, "close": 101.0, "volume": 200_000,
    }])
    assert bullish_structures.detect_bullish_structure(prices) is None


def test_scan_uses_fundamental_candidates_and_returns_matches(monkeypatch):
    prices = pd.DataFrame([
        {"symbol": symbol, "total_score": score, "date": pd.Timestamp("2026-01-01"), "open": 100.0,
         "high": 102.0, "low": 99.0, "close": 101.0, "volume": 200_000}
        for symbol, score in (("MATCH", 75), ("NONE", 65))
    ])
    monkeypatch.setattr(pd, "read_sql", lambda *args, **kwargs: prices.copy())
    structure_calls = {"count": 0}

    def detect(frame):
        structure_calls["count"] += 1
        if structure_calls["count"] == 1:
            return {"structure_label": "Horizontal Range Support", "risk_reward": 2.5, "band_position": 20.0}
        return None

    monkeypatch.setattr(bullish_structures, "detect_bullish_structure", detect)
    result = bullish_structures.scan_bullish_structures()
    assert result["fundamental_candidates"] == 2
    assert result["matched_stocks"] == 1
    assert result["stocks"][0]["symbol"] == "MATCH"
    assert result["stocks"][0]["fundamental_score"] == 75
