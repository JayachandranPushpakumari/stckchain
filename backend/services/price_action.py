def is_breakout(df):

    latest = df.iloc[-1]

    previous_20_high = df["high"].rolling(20).max().iloc[-2]

    return latest["close"] > previous_20_high