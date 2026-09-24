import numpy as np
import pandas as pd

from services.chart_patterns import PATTERN_LABELS, detect_bullish_patterns


def test_all_supported_patterns_are_registered():
    assert set(PATTERN_LABELS) == {
        "FLAT_BASE", "VCP", "ASCENDING_TRIANGLE", "CUP_WITH_HANDLE", "BULL_FLAG", "DOUBLE_BOTTOM",
    }


def test_flat_base_breakout_is_detected():
    rows = 100
    close = np.full(rows, 100.0)
    high = np.full(rows, 102.0)
    low = np.full(rows, 96.0)
    close[-1] = 104.0
    high[-1] = 105.0
    frame = pd.DataFrame({
        "open": close,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.full(rows, 200_000),
    })
    matches = detect_bullish_patterns(frame)
    assert "FLAT_BASE" in {match["code"] for match in matches}


def test_unstructured_deep_range_is_rejected():
    rows = 100
    values = np.resize(np.array([70.0, 130.0, 80.0, 120.0]), rows)
    frame = pd.DataFrame({
        "open": values,
        "high": values + 5,
        "low": values - 5,
        "close": values,
        "volume": np.full(rows, 200_000),
    })
    assert detect_bullish_patterns(frame) == []
