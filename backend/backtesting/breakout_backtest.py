from backtest_metrics import calculate_metrics

trade_returns = [5, -2, 10, -3, 4, 8]

metrics = calculate_metrics(trade_returns)

print(metrics)