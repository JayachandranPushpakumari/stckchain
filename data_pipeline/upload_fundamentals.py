import pandas as pd
from db import engine

# Read Excel
df = pd.read_excel("fundamentals.xlsx")

# -----------------------------
# CLEAN COLUMN NAMES
# -----------------------------
df.columns = df.columns.str.strip().str.lower()

# Rename columns (using lowercase keys since we already lowercased all columns)
df.rename(columns={
    "stockname": "symbol",
    "marketcap": "market_cap",
    "currentprice": "current_price",
    "stockpe": "pe_ratio",
    "dividendyield": "dividend_yield",
    "roce": "roce",
    "roe": "roe",
    "facevalue": "face_value",
    "compoundsalesgrowth10years": "sales_growth_10yrs",
    "compoundsalesgrowth5years": "sales_growth_5yrs",
    "compoundsalesgrowth3years": "sales_growth_3yrs",
    "compoundsalesgrowthttmyears": "sales_growth_ttm",
    "compoundprofitgrowth10years": "profit_growth_10yrs",
    "compoundprofitgrowth5years": "profit_growth_5yrs",
    "compoundprofitgrowth3years": "profit_growth_3yrs",
    "compoundprofitgrowthttmyears": "profit_growth_ttm",
    "stockprizecagr10years": "stockprice_cagr_10yrs",
    "stockprizecagr5years": "stockprice_cagr_5yrs",
    "stockprizecagr3years": "stockprice_cagr_3yrs",
    "stockprizecagrttmyears": "stockprice_cagr_ttm",
    "returnonequity10years": "roe_10yrs",
    "returnonequity5years": "roe_5yrs",
    "returnonequity3years": "roe_3yrs",
    "returnonequityttmyears": "roe_ttmyrs",
    "promotersn": "promoter_current",
    "promotersn1": "promoter_n_1_quarter",
    "promotersn2": "promoter_n_2_quarter",
    "promotersn3": "promoter_n_3_quarter",
    "promotersn4": "promoter_n_4_quarter",
    "promotersn5": "promoter_n_5_quarter",
    "promotersn6": "promoter_n_6_quarter",
    "promotersn7": "promoter_n_7_quarter",
    "promotersn8": "promoter_n_8_quarter",
    "promotersn9": "promoter_n_9_quarter",
    "promotersn10": "promoter_n_10_quarter",
    "promotersn11": "promoter_n_11_quarter",
    "fiisn": "fii_current",
    "fiisn1": "fii_n_1_quarter",
    "fiisn2": "fii_n_2_quarter",
    "fiisn3": "fii_n_3_quarter",
    "fiisn4": "fii_n_4_quarter",
    "fiisn5": "fii_n_5_quarter",
    "fiisn6": "fii_n_6_quarter",
    "fiisn7": "fii_n_7_quarter",
    "fiisn8": "fii_n_8_quarter",
    "fiisn9": "fii_n_9_quarter",
    "fiisn10": "fii_n_10_quarter",
    "fiisn11": "fii_n_11_quarter",
    "diisn": "dii_current",
    "diisn1": "dii_n_1_quarter",
    "diisn2": "dii_n_2_quarter",
    "diisn3": "dii_n_3_quarter",
    "diisn4": "dii_n_4_quarter",
    "diisn5": "dii_n_5_quarter",
    "diisn6": "dii_n_6_quarter",
    "diisn7": "dii_n_7_quarter",
    "diisn8": "dii_n_8_quarter",
    "diisn9": "dii_n_9_quarter",
    "diisn10": "dii_n_10_quarter",
    "diisn11": "dii_n_11_quarter",
    "rocen": "roce_current_year",
    "rocen1": "roce_n_1_year",
    "rocen2": "roce_n_2_year",
    "rocen3": "roce_n_3_year",
    "rocen4": "roce_n_4_year",
    "rocen5": "roce_n_5_year",
    "rocen6": "roce_n_6_year",
    "rocen7": "roce_n_7_year",
    "rocen8": "roce_n_8_year",
    "rocen9": "roce_n_9_year",
    "rocen10": "roce_n_10_year",
    "rocen11": "roce_n_11_year",
    "dividendn": "dividend_current_year",
    "dividendn1": "dividend_n_1_year",
    "dividendn2": "dividend_n_2_year",
    "dividendn3": "dividend_n_3_year",
    "dividendn4": "dividend_n_4_year",
    "dividendn5": "dividend_n_5_year",
    "dividendn6": "dividend_n_6_year",
    "dividendn7": "dividend_n_7_year",
    "dividendn8": "dividend_n_8_year",
    "dividendn9": "dividend_n_9_year",
    "dividendn10": "dividend_n_10_year",
    "dividendn11": "dividend_n_11_year",
    "epsn": "eps_current_year",
    "epsn1": "eps_n_1_year",
    "epsn2": "eps_n_2_year",
    "epsn3": "eps_n_3_year",
    "epsn4": "eps_n_4_year",
    "epsn5": "eps_n_5_year",
    "epsn6": "eps_n_6_year",
    "epsn7": "eps_n_7_year",
    "epsn8": "eps_n_8_year",
    "epsn9": "eps_n_9_year",
    "epsn10": "eps_n_10_year",
    "epsn11": "eps_n_11_year",
    "netprofitn": "net_profit_current_year",
    "netprofitn1": "net_profit_n_1_year",
    "netprofitn2": "net_profit_n_2_year",
    "netprofitn3": "net_profit_n_3_year",
    "netprofitn4": "net_profit_n_4_year",
    "netprofitn5": "net_profit_n_5_year",
    "netprofitn6": "net_profit_n_6_year",
    "netprofitn7": "net_profit_n_7_year",
    "netprofitn8": "net_profit_n_8_year",
    "netprofitn9": "net_profit_n_9_year",
    "netprofitn10": "net_profit_n_10_year",
    "netprofitn11": "net_profit_n_11_year",
    "opmn": "opm_current_year",
    "opmn1": "opm_n_1_year",
    "opmn2": "opm_n_2_year",
    "opmn3": "opm_n_3_year",
    "opmn4": "opm_n_4_year",
    "opmn5": "opm_n_5_year",
    "opmn6": "opm_n_6_year",
    "opmn7": "opm_n_7_year",
    "opmn8": "opm_n_8_year",
    "opmn9": "opm_n_9_year",
    "opmn10": "opm_n_10_year",
    "opmn11": "opm_n_11_year",
    "opn": "operating_profit_current_year",
    "opn1": "operating_profit_n_1_year",
    "opn2": "operating_profit_n_2_year",
    "opn3": "operating_profit_n_3_year",
    "opn4": "operating_profit_n_4_year",
    "opn5": "operating_profit_n_5_year",
    "opn6": "operating_profit_n_6_year",
    "opn7": "operating_profit_n_7_year",
    "opn8": "operating_profit_n_8_year",
    "opn9": "operating_profit_n_9_year",
    "opn10": "operating_profit_n_10_year",
    "opn11": "operating_profit_n_11_year",
    "epsq": "eps_current_quarter",
    "epsq1": "eps_n_1_quarter",
    "epsq2": "eps_n_2_quarter",
    "epsq3": "eps_n_3_quarter",
    "epsq4": "eps_n_4_quarter",
    "epsq5": "eps_n_5_quarter",
    "epsq6": "eps_n_6_quarter",
    "epsq7": "eps_n_7_quarter",
    "epsq8": "eps_n_8_quarter",
    "epsq9": "eps_n_9_quarter",
    "epsq10": "eps_n_10_quarter",
    "epsq11": "eps_n_11_quarter",
    "epsq12": "eps_n_12_quarter",
    "netprofitq": "net_profit_current_quarter",
    "netprofitq1": "net_profit_n_1_quarter",
    "netprofitq2": "net_profit_n_2_quarter",
    "netprofitq3": "net_profit_n_3_quarter",
    "netprofitq4": "net_profit_n_4_quarter",
    "netprofitq5": "net_profit_n_5_quarter",
    "netprofitq6": "net_profit_n_6_quarter",
    "netprofitq7": "net_profit_n_7_quarter",
    "netprofitq8": "net_profit_n_8_quarter",
    "netprofitq9": "net_profit_n_9_quarter",
    "netprofitq10": "net_profit_n_10_quarter",
    "netprofitq11": "net_profit_n_11_quarter",
    "netprofitq12": "net_profit_n_12_quarter",
    "opmq": "opm_current_quarter",
    "opmq1": "opm_n_1_quarter",
    "opmq2": "opm_n_2_quarter",
    "opmq3": "opm_n_3_quarter",
    "opmq4": "opm_n_4_quarter",
    "opmq5": "opm_n_5_quarter",
    "opmq6": "opm_n_6_quarter",
    "opmq7": "opm_n_7_quarter",
    "opmq8": "opm_n_8_quarter",
    "opmq9": "opm_n_9_quarter",
    "opmq10": "opm_n_10_quarter",
    "opmq11": "opm_n_11_quarter",
    "opmq12": "opm_n_12_quarter",
    "opq": "operating_profit_current_quarter",
    "opq1": "operating_profit_n_1_quarter",
    "opq2": "operating_profit_n_2_quarter",
    "opq3": "operating_profit_n_3_quarter",
    "opq4": "operating_profit_n_4_quarter",
    "opq5": "operating_profit_n_5_quarter",
    "opq6": "operating_profit_n_6_quarter",
    "opq7": "operating_profit_n_7_quarter",
    "opq8": "operating_profit_n_8_quarter",
    "opq9": "operating_profit_n_9_quarter",
    "opq10": "operating_profit_n_10_quarter",
    "opq11": "operating_profit_n_11_quarter",
    "opq12": "operating_profit_n_12_quarter",
    "debttoequity": "debt_to_equity"
}, inplace=True)

# -----------------------------
# OPTIONAL CLEANING
# -----------------------------

def clean_numeric_value(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return val
    val_str = str(val).strip()
    val_str = val_str.replace(',', '')
    val_str = val_str.replace('%', '')
    if val_str == '' or val_str == '-':
        return None
    try:
        return float(val_str)
    except:
        return None

numeric_cols = [
    'market_cap', 'current_price', 'pe_ratio', 'dividend_yield', 'roce', 'roe', 'face_value',
    'sales_growth_10yrs', 'sales_growth_5yrs', 'sales_growth_3yrs', 'sales_growth_ttm',
    'profit_growth_10yrs', 'profit_growth_5yrs', 'profit_growth_3yrs', 'profit_growth_ttm',
    'stockprice_cagr_10yrs', 'stockprice_cagr_5yrs', 'stockprice_cagr_3yrs', 'stockprice_cagr_ttm',
    'roe_10yrs', 'roe_5yrs', 'roe_3yrs', 'roe_ttmyrs',
    'promoter_current', 'promoter_n_1_quarter', 'promoter_n_2_quarter', 'promoter_n_3_quarter',
    'promoter_n_4_quarter', 'promoter_n_5_quarter', 'promoter_n_6_quarter', 'promoter_n_7_quarter',
    'promoter_n_8_quarter', 'promoter_n_9_quarter', 'promoter_n_10_quarter', 'promoter_n_11_quarter',
    'fii_current', 'fii_n_1_quarter', 'fii_n_2_quarter', 'fii_n_3_quarter',
    'fii_n_4_quarter', 'fii_n_5_quarter', 'fii_n_6_quarter', 'fii_n_7_quarter',
    'fii_n_8_quarter', 'fii_n_9_quarter', 'fii_n_10_quarter', 'fii_n_11_quarter',
    'dii_current', 'dii_n_1_quarter', 'dii_n_2_quarter', 'dii_n_3_quarter',
    'dii_n_4_quarter', 'dii_n_5_quarter', 'dii_n_6_quarter', 'dii_n_7_quarter',
    'dii_n_8_quarter', 'dii_n_9_quarter', 'dii_n_10_quarter', 'dii_n_11_quarter',
    'roce_current_year', 'roce_n_1_year', 'roce_n_2_year', 'roce_n_3_year',
    'roce_n_4_year', 'roce_n_5_year', 'roce_n_6_year', 'roce_n_7_year',
    'roce_n_8_year', 'roce_n_9_year', 'roce_n_10_year', 'roce_n_11_year',
    'dividend_current_year', 'dividend_n_1_year', 'dividend_n_2_year', 'dividend_n_3_year',
    'dividend_n_4_year', 'dividend_n_5_year', 'dividend_n_6_year', 'dividend_n_7_year',
    'dividend_n_8_year', 'dividend_n_9_year', 'dividend_n_10_year', 'dividend_n_11_year',
    'opm_current_year', 'opm_n_1_year', 'opm_n_2_year', 'opm_n_3_year',
    'opm_n_4_year', 'opm_n_5_year', 'opm_n_6_year', 'opm_n_7_year',
    'opm_n_8_year', 'opm_n_9_year', 'opm_n_10_year', 'opm_n_11_year',
    'opm_current_quarter', 'opm_n_1_quarter', 'opm_n_2_quarter', 'opm_n_3_quarter',
    'opm_n_4_quarter', 'opm_n_5_quarter', 'opm_n_6_quarter', 'opm_n_7_quarter',
    'opm_n_8_quarter', 'opm_n_9_quarter', 'opm_n_10_quarter', 'opm_n_11_quarter', 'opm_n_12_quarter',
    'net_profit_current_year', 'net_profit_n_1_year', 'net_profit_n_2_year', 'net_profit_n_3_year',
    'net_profit_n_4_year', 'net_profit_n_5_year', 'net_profit_n_6_year', 'net_profit_n_7_year',
    'net_profit_n_8_year', 'net_profit_n_9_year', 'net_profit_n_10_year', 'net_profit_n_11_year',
    'operating_profit_current_year', 'operating_profit_n_1_year', 'operating_profit_n_2_year', 'operating_profit_n_3_year',
    'operating_profit_n_4_year', 'operating_profit_n_5_year', 'operating_profit_n_6_year', 'operating_profit_n_7_year',
    'operating_profit_n_8_year', 'operating_profit_n_9_year', 'operating_profit_n_10_year', 'operating_profit_n_11_year',
    'eps_current_year', 'eps_n_1_year', 'eps_n_2_year', 'eps_n_3_year', 'eps_n_4_year', 'eps_n_5_year',
    'eps_n_6_year', 'eps_n_7_year', 'eps_n_8_year', 'eps_n_9_year', 'eps_n_10_year', 'eps_n_11_year',
    'net_profit_current_quarter', 'net_profit_n_1_quarter', 'net_profit_n_2_quarter', 'net_profit_n_3_quarter',
    'net_profit_n_4_quarter', 'net_profit_n_5_quarter', 'net_profit_n_6_quarter', 'net_profit_n_7_quarter',
    'net_profit_n_8_quarter', 'net_profit_n_9_quarter', 'net_profit_n_10_quarter', 'net_profit_n_11_quarter', 'net_profit_n_12_quarter',
    'operating_profit_current_quarter', 'operating_profit_n_1_quarter', 'operating_profit_n_2_quarter', 'operating_profit_n_3_quarter',
    'operating_profit_n_4_quarter', 'operating_profit_n_5_quarter', 'operating_profit_n_6_quarter', 'operating_profit_n_7_quarter',
    'operating_profit_n_8_quarter', 'operating_profit_n_9_quarter', 'operating_profit_n_10_quarter', 'operating_profit_n_11_quarter', 'operating_profit_n_12_quarter',
    'eps_current_quarter', 'eps_n_1_quarter', 'eps_n_2_quarter', 'eps_n_3_quarter', 'eps_n_4_quarter', 'eps_n_5_quarter',
    'eps_n_6_quarter', 'eps_n_7_quarter', 'eps_n_8_quarter', 'eps_n_9_quarter', 'eps_n_10_quarter', 'eps_n_11_quarter', 'eps_n_12_quarter'
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = df[col].apply(clean_numeric_value)

# Remove duplicate symbols (keep last occurrence)
duplicates_before = len(df)
df = df.drop_duplicates(subset=['symbol'], keep='last')
duplicates_removed = duplicates_before - len(df)
if duplicates_removed > 0:
    print(f"Removed {duplicates_removed} duplicate symbol(s)")

# Add report date
df["report_date"] = pd.to_datetime("2026-05-08")

# -----------------------------
# INSERT INTO POSTGRES
# -----------------------------
from sqlalchemy import text

report_date = df['report_date'].iloc[0]

with engine.begin() as conn:
    result = conn.execute(text("DELETE FROM fundamentals WHERE report_date = :report_date"), {"report_date": report_date})
    print(f"Deleted {result.rowcount} existing records for {report_date}")
    df.to_sql('fundamentals', conn, if_exists='append', index=False, method='multi')

print(" Fundamentals uploaded successfully!")