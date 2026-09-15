import pandas as pd


def breakout_strategy(df):

    trades = []

    df["ma20"] = df["close"].rolling(20).mean()
    df["ma50"] = df["close"].rolling(50).mean()
    df["avg_volume_20"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["avg_volume_20"]
    df["high_20"] = df["high"].rolling(20).max()
    
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    
    plus_dm = df["high"].diff()
    minus_dm = -df["low"].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    plus_dm[(plus_dm < minus_dm)] = 0
    minus_dm[(minus_dm < plus_dm)] = 0
    
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    df["adx"] = dx.rolling(14).mean()

    buy_signal = (
        # Trend
        (df["ma20"] > df["ma50"]) &
        # Momentum
        (df["rsi"] > 60) &
        # Breakout
        (df["close"] > df["high_20"].shift(1)) &
        # Volume confirmation
        (df["volume_ratio"] > 2) &
        # Strong trend only
        (df["adx"] > 20)
    )

    for i in range(50, len(df) - 90):

        bullish = buy_signal.iloc[i]

        if bullish:

            entry_price = df["close"].iloc[i]
            entry_date = str(df.index[i])
            
            atr_value = atr.iloc[i]
            # stop_loss_price = entry_price - (2 * atr_value)
            stop_loss_price = entry_price * 0.70
            max_holding_days = 180
            
            exit_price = None
            exit_date = None
            exit_reason = "max_holding"
            
            for j in range(i + 1, min(i + max_holding_days + 1, len(df))):
                current_price = df["close"].iloc[j]
                
                if current_price <= stop_loss_price:
                    exit_price = stop_loss_price
                    exit_date = str(df.index[j])
                    exit_reason = "stop_loss"
                    break
            
            if exit_price is None:
                exit_price = df["close"].iloc[min(i + max_holding_days, len(df) - 1)]
                exit_date = str(df.index[min(i + max_holding_days, len(df) - 1)])

            trade_return = (
                (exit_price - entry_price)
                / entry_price
            ) * 100

            trades.append({
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "return": float(trade_return),
                "exit_reason": exit_reason
            })

    return trades