import pandas as pd
from datetime import datetime

from db import engine


def _to_number(value):
    return pd.to_numeric(value, errors="coerce")


def _to_serializable_number(value):
    if pd.isna(value):
        return None
    return float(value)


def _criterion_result(actual_value, threshold, operator, is_met):
    return {
        "actual_value": _to_serializable_number(actual_value),
        "threshold": _to_serializable_number(threshold),
        "operator": operator,
        "score": 10 if is_met else 0,
    }


def _score_stock(stock):
    roe = _to_number(stock.get("roe"))
    roce = _to_number(stock.get("roce"))
    roe_3yrs = _to_number(stock.get("roe_3yrs"))
    roce_n_1_year = _to_number(stock.get("roce_n_1_year"))
    roce_n_2_year = _to_number(stock.get("roce_n_2_year"))
    roce_n_3_year = _to_number(stock.get("roce_n_3_year"))
    debt_to_equity = _to_number(stock.get("debt_to_equity"))
    sales_growth_3yrs = _to_number(stock.get("sales_growth_3yrs"))
    profit_growth_3yrs = _to_number(stock.get("profit_growth_3yrs"))
    stockprice_cagr_3yrs = _to_number(stock.get("stockprice_cagr_3yrs"))
    pe_ratio = _to_number(stock.get("pe_ratio"))

    eps_avg_3yrs = _to_number(
        (
            (stock.get("eps_n_1_year") or 0)
            + (stock.get("eps_n_2_year") or 0)
            + (stock.get("eps_n_3_year") or 0)
        )
        / 3
    )
    pe_threshold = 2 * eps_avg_3yrs

    promoter_current = _to_number(stock.get("promoter_current"))
    
    promoter_historical_quarters = [
        _to_number(stock.get("promoter_n_1_quarter")),
        _to_number(stock.get("promoter_n_2_quarter")),
        _to_number(stock.get("promoter_n_3_quarter")),
        _to_number(stock.get("promoter_n_4_quarter")),
        _to_number(stock.get("promoter_n_5_quarter")),
        _to_number(stock.get("promoter_n_6_quarter")),
        _to_number(stock.get("promoter_n_7_quarter")),
        _to_number(stock.get("promoter_n_8_quarter")),
        _to_number(stock.get("promoter_n_9_quarter")),
        _to_number(stock.get("promoter_n_10_quarter")),
        _to_number(stock.get("promoter_n_11_quarter")),
    ]
    
    valid_historical = [val for val in promoter_historical_quarters if not pd.isna(val)]
    
    if pd.isna(promoter_current) or not valid_historical:
        promoter_holding_drop = None
    else:
        max_historical = max(valid_historical)
        promoter_holding_drop = max_historical - promoter_current

    valid_roce_years = [r for r in [roce_n_1_year, roce_n_2_year, roce_n_3_year] if pd.notna(r)]
    roce_3yr_avg = sum(valid_roce_years) / len(valid_roce_years) if valid_roce_years else None
    
    category_scores = {
        "roe": _criterion_result(roe, 15, ">", roe > 15),
        "roce": _criterion_result(roce, 15, ">", roce > 15),
        "roe_3yrs": _criterion_result(roe_3yrs, 20, ">", roe_3yrs > 20),
        "roce_3yr_consistency": _criterion_result(
            roce_3yr_avg,
            15,
            ">",
            pd.notna(roce_3yr_avg) and roce_3yr_avg > 15,
        ),
        "debt_to_equity": _criterion_result(debt_to_equity, 1, "<", debt_to_equity < 1),
        "sales_growth_3yrs": _criterion_result(
            sales_growth_3yrs, 10, ">", sales_growth_3yrs > 10
        ),
        "profit_growth_3yrs": _criterion_result(
            profit_growth_3yrs, 12, ">", profit_growth_3yrs > 12
        ),
        "stockprice_cagr_3yrs": _criterion_result(
            stockprice_cagr_3yrs, 10, ">", stockprice_cagr_3yrs > 10
        ),
        "pe_vs_eps_3yrs_avg": _criterion_result(
            pe_ratio,
            pe_threshold,
            "<",
            pe_ratio < pe_threshold,
        ),
        "pledged_promoter_holding": _criterion_result(
            promoter_holding_drop,
            10,
            "<",
            promoter_holding_drop is not None and promoter_holding_drop < 10,
        ),
    }

    total_score = sum(criteria["score"] for criteria in category_scores.values())

    return {"total_score": total_score, "category_scores": category_scores}


def _latest_close_by_symbol():
    query = """
    SELECT s.symbol, l.close
    FROM (SELECT DISTINCT symbol FROM price_data) s
    CROSS JOIN LATERAL (
        SELECT close
        FROM price_data
        WHERE symbol = s.symbol
        ORDER BY date DESC
        LIMIT 1
    ) l
    """
    df = pd.read_sql(query, engine)

    latest_close = {}
    for _, row in df.iterrows():
        symbol = row.get("symbol")
        if symbol:
            latest_close[symbol] = _to_serializable_number(row.get("close"))

    return latest_close


def _sector_by_symbol():
    query = """
    SELECT symbol, sector
    FROM sectors
    """
    df = pd.read_sql(query, engine)

    sectors = {}
    for _, row in df.iterrows():
        symbol = row.get("symbol")
        if symbol:
            sectors[symbol] = row.get("sector")

    return sectors


def _save_fundamental_scores(symbols_data):
    if not symbols_data:
        return
    
    records = []
    screened_at = datetime.now()
    
    for item in symbols_data:
        category_scores = item["category_scores"]
        
        record = {
            "symbol": item["symbol"],
            "latest_close": item["latest_close"],
            "total_score": item["total_score"],
            "screened_at": screened_at,
            
            "roe_actual": category_scores["roe"]["actual_value"],
            "roe_threshold": category_scores["roe"]["threshold"],
            "roe_score": category_scores["roe"]["score"],
            
            "roce_actual": category_scores["roce"]["actual_value"],
            "roce_threshold": category_scores["roce"]["threshold"],
            "roce_score": category_scores["roce"]["score"],
            
            "roe_3yrs_actual": category_scores["roe_3yrs"]["actual_value"],
            "roe_3yrs_threshold": category_scores["roe_3yrs"]["threshold"],
            "roe_3yrs_score": category_scores["roe_3yrs"]["score"],
            
            "roce_3yr_consistency_actual": category_scores["roce_3yr_consistency"]["actual_value"],
            "roce_3yr_consistency_threshold": category_scores["roce_3yr_consistency"]["threshold"],
            "roce_3yr_consistency_score": category_scores["roce_3yr_consistency"]["score"],
            
            "debt_to_equity_actual": category_scores["debt_to_equity"]["actual_value"],
            "debt_to_equity_threshold": category_scores["debt_to_equity"]["threshold"],
            "debt_to_equity_score": category_scores["debt_to_equity"]["score"],
            
            "sales_growth_3yrs_actual": category_scores["sales_growth_3yrs"]["actual_value"],
            "sales_growth_3yrs_threshold": category_scores["sales_growth_3yrs"]["threshold"],
            "sales_growth_3yrs_score": category_scores["sales_growth_3yrs"]["score"],
            
            "profit_growth_3yrs_actual": category_scores["profit_growth_3yrs"]["actual_value"],
            "profit_growth_3yrs_threshold": category_scores["profit_growth_3yrs"]["threshold"],
            "profit_growth_3yrs_score": category_scores["profit_growth_3yrs"]["score"],
            
            "stockprice_cagr_3yrs_actual": category_scores["stockprice_cagr_3yrs"]["actual_value"],
            "stockprice_cagr_3yrs_threshold": category_scores["stockprice_cagr_3yrs"]["threshold"],
            "stockprice_cagr_3yrs_score": category_scores["stockprice_cagr_3yrs"]["score"],
            
            "pe_vs_eps_3yrs_avg_actual": category_scores["pe_vs_eps_3yrs_avg"]["actual_value"],
            "pe_vs_eps_3yrs_avg_threshold": category_scores["pe_vs_eps_3yrs_avg"]["threshold"],
            "pe_vs_eps_3yrs_avg_score": category_scores["pe_vs_eps_3yrs_avg"]["score"],
            
            "pledged_promoter_holding_actual": category_scores["pledged_promoter_holding"]["actual_value"],
            "pledged_promoter_holding_threshold": category_scores["pledged_promoter_holding"]["threshold"],
            "pledged_promoter_holding_score": category_scores["pledged_promoter_holding"]["score"],
        }
        records.append(record)
    
    df_to_save = pd.DataFrame(records)
    df_to_save = df_to_save.drop_duplicates(subset=["symbol"], keep="first")
    df_to_save.to_sql("fundamental_scores", engine, if_exists="append", index=False)


def calculate_fundamental_score(save_to_db=True):
    query = "SELECT * FROM fundamentals"
    df = pd.read_sql(query, engine)
    latest_close = _latest_close_by_symbol()
    sector_by_symbol = _sector_by_symbol()

    symbols = []
    for _, row in df.iterrows():
        stock = row.to_dict()
        symbol = stock.get("symbol")
        score_data = _score_stock(stock)
        if score_data["total_score"] >= 0:
            symbols.append(
                {
                    "symbol": symbol,
                    "sector": sector_by_symbol.get(symbol),
                    "latest_close": latest_close.get(symbol),
                    "total_score": score_data["total_score"],
                    "category_scores": score_data["category_scores"],
                }
            )
    
    if save_to_db and symbols:
        _save_fundamental_scores(symbols)

    return {"symbols": symbols}