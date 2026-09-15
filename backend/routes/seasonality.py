from fastapi import APIRouter
import pandas as pd

from services.seasonality import seasonal_stock_records

router = APIRouter()

def dataframe_to_json_records(df: pd.DataFrame):
    cleaned_df = df.replace([float("inf"), float("-inf")], pd.NA)
    cleaned_df = cleaned_df.astype(object).where(pd.notna(cleaned_df), None)
    return cleaned_df.to_dict(orient="records")

@router.get("/seasonality/{month}")
def get_seasonality(month: int):

    return dataframe_to_json_records(pd.DataFrame(seasonal_stock_records(month)))
