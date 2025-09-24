import pandas as pd
from typing import List, Dict, Any

def delete_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    return df.drop(columns=cols, errors="ignore")

def delete_rows(df: pd.DataFrame, index_list: List[int]) -> pd.DataFrame:
    return df.drop(index=index_list, errors="ignore").reset_index(drop=True)

def fillna(df: pd.DataFrame, strategy: str = "value", value: Any = None) -> pd.DataFrame:
    if strategy == "median":
        return df.fillna(df.median(numeric_only=True))
    if strategy == "mean":
        return df.fillna(df.mean(numeric_only=True))
    if strategy == "mode":
        return df.fillna(df.mode().iloc[0])
    return df.fillna(value)

def filter_df(df: pd.DataFrame, query_str: str) -> pd.DataFrame:
    if not query_str:
        return df
    try:
        return df.query(query_str, engine="python")
    except Exception:
        # mantém dataset se query inválida
        return df

def rename_columns(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    return df.rename(columns=mapping)

def convert_dtypes_safely(df: pd.DataFrame) -> pd.DataFrame:
    try:
        return df.convert_dtypes()
    except Exception:
        return df
