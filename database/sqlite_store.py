from __future__ import annotations

from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

DB_PATH = Path(__file__).resolve().parents[1] / "outputs" / "commodity_platform.db"


def get_engine():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{DB_PATH}")


def save_dataframe(df: pd.DataFrame, table_name: str) -> None:
    engine = get_engine()
    df.to_sql(table_name, engine, if_exists="replace", index=False)


def load_dataframe(table_name: str) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql_table(table_name, engine)
