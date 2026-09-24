import numpy as np
import pandas as pd


PATTERN_LABELS = {
    "FLAT_BASE": "Flat Base",
    "VCP": "Volatility Contraction",
    "ASCENDING_TRIANGLE": "Ascending Triangle",
    "CUP_WITH_HANDLE": "Cup with Handle",
    "BULL_FLAG": "Bull Flag",
    "DOUBLE_BOTTOM": "Double Bottom",
}


def _slope(values):
    series = np.asarray(values, dtype=float)
    return float(np.polyfit(np.arange(len(series)), series, 1)[0]) if len(series) > 1 else 0.0


def _depth(frame):
    high = float(frame["high"].max())
    low = float(frame["low"].min())
    return (high - low) / high if high > 0 else 1.0


def _is_fresh_breakout(clean, level, max_age_sessions):
    if max_age_sessions is None:
        return True, None
    closes = pd.to_numeric(clean["close"], errors="coerce")
    last_index = len(clean) - 1
    for i in range(last_index - 1, -1, -1):
        if closes.iloc[i] <= level:
            age = last_index - (i + 1)
            return age <= max_age_sessions, age
    return False, None


def _flat_base(history, close):
    base = history.tail(40)
    resistance = float(base["high"].max())
    touches = int((base["high"] >= resistance * 0.98).sum())
    matched = len(base) == 40 and _depth(base) <= 0.15 and touches >= 2 and close > resistance
    return matched, f"40-session flat base broke above resistance {resistance:.2f}", resistance


def _vcp(history, close):
    base = history.tail(60)
    if len(base) < 60:
        return False, "", None
    contractions = [_depth(base.iloc[start:start + 20]) for start in (0, 20, 40)]
    resistance = float(base["high"].max())
    matched = contractions[0] > contractions[1] > contractions[2] and contractions[2] <= 0.12 and close > resistance
    return matched, f"Volatility contracted from {contractions[0] * 100:.1f}% to {contractions[2] * 100:.1f}% before breakout", resistance


def _ascending_triangle(history, close):
    base = history.tail(40)
    if len(base) < 40:
        return False, "", None
    resistance = float(base["high"].quantile(0.9))
    high_dispersion = float(base["high"].tail(20).std() / resistance) if resistance > 0 else 1.0
    low_slope = _slope(base["low"]) / float(base["low"].mean())
    matched = high_dispersion <= 0.035 and low_slope >= 0.001 and close > resistance
    return matched, f"Rising lows broke ascending-triangle resistance {resistance:.2f}", resistance


def _cup_with_handle(history, close):
    base = history.tail(90)
    if len(base) < 90:
        return False, "", None
    cup = base.iloc[:75]
    handle = base.iloc[75:]
    left_rim = float(cup.iloc[:20]["high"].max())
    right_rim = float(cup.iloc[-20:]["high"].max())
    bottom = float(cup.iloc[20:60]["low"].min())
    rim = min(left_rim, right_rim)
    cup_depth = (max(left_rim, right_rim) - bottom) / max(left_rim, right_rim)
    rims_aligned = abs(left_rim - right_rim) / max(left_rim, right_rim) <= 0.08
    matched = rims_aligned and 0.12 <= cup_depth <= 0.40 and _depth(handle) <= 0.12 and close > rim
    return matched, f"Cup-and-handle pivot {rim:.2f} cleared after a {cup_depth * 100:.1f}% cup", rim


def _bull_flag(history, close):
    base = history.tail(35)
    if len(base) < 35:
        return False, "", None
    pole = base.iloc[:20]
    flag = base.iloc[20:]
    pole_gain = float(pole["close"].iloc[-1] / pole["close"].iloc[0] - 1)
    flag_resistance = float(flag["high"].max())
    flag_slope = _slope(flag["close"])
    matched = pole_gain >= 0.15 and _depth(flag) <= 0.15 and flag_slope <= 0 and close > flag_resistance
    return matched, f"Bull flag followed a {pole_gain * 100:.1f}% advance and cleared {flag_resistance:.2f}", flag_resistance


def _double_bottom(history, close):
    base = history.tail(80).reset_index(drop=True)
    if len(base) < 80:
        return False, "", None
    first_half = base.iloc[:40]
    second_half = base.iloc[40:]
    first_index = int(first_half["low"].idxmin())
    second_index = int(second_half["low"].idxmin())
    first_low = float(base.loc[first_index, "low"])
    second_low = float(base.loc[second_index, "low"])
    neckline = float(base.loc[first_index:second_index, "high"].max())
    lows_aligned = abs(first_low - second_low) / max(first_low, second_low) <= 0.05
    rebound = neckline / min(first_low, second_low) - 1
    matched = second_index - first_index >= 15 and lows_aligned and rebound >= 0.08 and close > neckline
    return matched, f"Double bottom cleared neckline {neckline:.2f} after two aligned lows", neckline


def detect_bullish_patterns(prices, max_breakout_age_sessions=None):
    clean = prices.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    if len(clean) < 91:
        return []
    history = clean.iloc[:-1]
    close = float(clean.iloc[-1]["close"])
    detectors = (
        ("FLAT_BASE", _flat_base),
        ("VCP", _vcp),
        ("ASCENDING_TRIANGLE", _ascending_triangle),
        ("CUP_WITH_HANDLE", _cup_with_handle),
        ("BULL_FLAG", _bull_flag),
        ("DOUBLE_BOTTOM", _double_bottom),
    )
    matches = []
    for code, detector in detectors:
        matched, reason, level = detector(history, close)
        if matched:
            fresh, age = _is_fresh_breakout(clean, level, max_breakout_age_sessions)
            if fresh:
                matches.append({"code": code, "label": PATTERN_LABELS[code], "reason": reason, "level": level, "breakout_age_sessions": age})
    return matches
