from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKey, Integer, JSON, MetaData, Numeric, String, Table, Text, UniqueConstraint, Index

metadata = MetaData()

Table(
    "stocks", metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(20)),
    Column("name", Text),
)
Table(
    "stocks2", metadata,
    Column("id", Integer, primary_key=True),
    Column("stock_name", String(255), nullable=False),
    Column("symbol", String(50), nullable=False, unique=True),
)
Table(
    "stocklist", metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(20), unique=True),
)
Table(
    "price_data", metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(20)),
    Column("date", Date),
    Column("open", Float),
    Column("high", Float),
    Column("low", Float),
    Column("close", Float),
    Column("volume", BigInteger),
    UniqueConstraint("symbol", "date", name="unique_stock_date"),
)

fundamental_columns = [
    Column("id", Integer, primary_key=True),
    Column("symbol", String(50)),
    Column("report_date", Date),
]
fundamental_metric_names = [
    "market_cap", "current_price", "pe_ratio", "dividend_yield", "roce", "roe", "face_value",
    *[f"sales_growth_{period}" for period in ("10yrs", "5yrs", "3yrs", "ttm")],
    *[f"profit_growth_{period}" for period in ("10yrs", "5yrs", "3yrs", "ttm")],
    *[f"stockprice_cagr_{period}" for period in ("10yrs", "5yrs", "3yrs", "ttm")],
    *[f"roe_{period}" for period in ("10yrs", "5yrs", "3yrs", "ttmyrs")],
    "debt_to_equity",
]
for prefix in ("promoter", "fii", "dii"):
    fundamental_metric_names.extend([f"{prefix}_current", *[f"{prefix}_n_{year}_quarter" for year in range(1, 12)]])
for prefix in ("roce", "dividend", "eps", "net_profit", "opm", "operating_profit"):
    fundamental_metric_names.extend([f"{prefix}_current_year", *[f"{prefix}_n_{year}_year" for year in range(1, 12)]])
for prefix in ("eps", "net_profit", "opm", "operating_profit"):
    fundamental_metric_names.extend([f"{prefix}_current_quarter", *[f"{prefix}_n_{quarter}_quarter" for quarter in range(1, 13)]])
for name in dict.fromkeys(fundamental_metric_names):
    column_type = BigInteger if name == "market_cap" else Float
    fundamental_columns.append(Column(name, column_type))
fundamentals = Table(
    "fundamentals", metadata,
    *fundamental_columns,
    UniqueConstraint("symbol", "report_date", name="fundamentals_symbol_report_date_key"),
)

score_columns = [
    Column("id", Integer, primary_key=True),
    Column("symbol", String(50), nullable=False),
    Column("latest_close", Numeric(10, 2)),
    Column("total_score", Integer, nullable=False),
]
score_names = (
    "roe", "roce", "roe_3yrs", "roce_3yr_consistency", "debt_to_equity",
    "sales_growth_3yrs", "profit_growth_3yrs", "stockprice_cagr_3yrs",
    "pe_vs_eps_3yrs_avg", "pledged_promoter_holding",
)
for name in score_names:
    score_columns.extend([
        Column(f"{name}_actual", Numeric(10, 2)),
        Column(f"{name}_threshold", Numeric(10, 2)),
        Column(f"{name}_score", Integer),
    ])
score_columns.append(Column("screened_at", DateTime))
fundamental_scores = Table(
    "fundamental_scores", metadata,
    *score_columns,
    UniqueConstraint("symbol", "screened_at", name="fundamental_scores_symbol_screened_at_key"),
)
Index("idx_fundamental_scores_symbol", fundamental_scores.c.symbol)
Index("idx_fundamental_scores_screened_at", fundamental_scores.c.screened_at.desc())
Index("idx_fundamental_scores_total_score", fundamental_scores.c.total_score.desc())

Table("sectors", metadata, Column("symbol", Text), Column("sector", Text))
Table(
    "sector_strength_history", metadata,
    Column("id", Integer, primary_key=True),
    Column("snapshot_date", Date),
    Column("sector", String(100)),
    Column("strength", Numeric),
)
Table("relative_strength", metadata, Column("symbol", Text), Column("rs_score", Float))
Table("sector_strength", metadata, Column("sector", Text), Column("strength", Float), Column("pct_positive", Float), Column("stock_count", BigInteger))
Table("sector_leaders", metadata, Column("symbol", Text), Column("rs_score", Float), Column("sector", Text), Column("rank", Float))
Table(
    "breakout_results", metadata,
    Column("symbol", Text), Column("close", Float), Column("rsi", Float), Column("volume_ratio", Float),
    Column("ma20", Float), Column("ma50", Float), Column("high_20", Float), Column("adx", Float), Column("signal", Text),
)
Table(
    "backtest_results", metadata,
    Column("total_trades", BigInteger), Column("win_rate", Float), Column("avg_return", Float),
    Column("profit_factor", Float), Column("max_drawdown", Float), Column("cagr", Float), Column("symbol", Text),
)
opportunity_runs = Table(
    "opportunity_runs", metadata,
    Column("id", Integer, primary_key=True),
    Column("setup_type", String(30), nullable=False),
    Column("market_regime", String(20), nullable=False),
    Column("stage_counts", JSON, nullable=False),
    Column("minimum_score", Numeric(5, 2), nullable=False),
    Column("generated_at", DateTime(timezone=True), nullable=False),
)
Table(
    "opportunities", metadata,
    Column("id", Integer, primary_key=True),
    Column("run_id", Integer, ForeignKey(opportunity_runs.c.id, ondelete="CASCADE"), nullable=False),
    Column("symbol", String(50), nullable=False),
    Column("setup_type", String(30), nullable=False),
    Column("status", String(30), nullable=False),
    Column("rank", Integer, nullable=False),
    Column("score", Numeric(5, 2), nullable=False),
    Column("current_price", Numeric(14, 2), nullable=False),
    Column("entry_low", Numeric(14, 2), nullable=False),
    Column("entry_high", Numeric(14, 2), nullable=False),
    Column("target_1", Numeric(14, 2), nullable=False),
    Column("target_2", Numeric(14, 2), nullable=False),
    Column("stop_loss", Numeric(14, 2), nullable=False),
    Column("risk_reward", Numeric(6, 2), nullable=False),
    Column("fundamental_score", Numeric(5, 2), nullable=False),
    Column("technical_score", Numeric(5, 2), nullable=False),
    Column("momentum_score", Numeric(5, 2), nullable=False),
    Column("liquidity_score", Numeric(5, 2), nullable=False),
    Column("regime_score", Numeric(5, 2), nullable=False),
    Column("risk_reward_score", Numeric(5, 2), nullable=False),
    Column("market_regime", String(20), nullable=False),
    Column("reasons", JSON, nullable=False),
    UniqueConstraint("run_id", "symbol", name="opportunities_run_symbol_key"),
)
Index("idx_opportunities_run_rank", metadata.tables["opportunities"].c.run_id, metadata.tables["opportunities"].c.rank)
Index("idx_opportunities_symbol", metadata.tables["opportunities"].c.symbol)
