import pandas as pd
from src.common_types import SYMBOLS


class RepositoryInterface:
    def __init__(self, folder) -> None:
        self.folder = folder
        self.data_mapping = {
            "positioning": pd.DataFrame,
            "IV": pd.DataFrame,
            "finviz_earnings": pd.DataFrame,
            "stock_fundamentals": pd.DataFrame,
            "greeks": pd.DataFrame,
        }
        self.historical_mapping = {symbol: f"candles/{symbol}" for symbol in SYMBOLS}

    def fetch(self, data_source: str) -> pd.DataFrame:
        print("data_source", data_source, self.folder)
        if data_source in self.data_mapping:
            df = pd.read_csv(f"{self.folder}/{data_source}.csv")
            return df
        elif data_source in self.historical_mapping:
            data_path = self.historical_mapping[data_source]
            df = pd.read_csv(f"{data_path}.csv")
            return df
        raise ValueError(f"Data source not implemented {data_source}")

    def update(self, data_source: str, df: pd.DataFrame) -> None:
        print("update", f"{self.folder}/{data_source}")
        df.to_csv(f"{self.folder}/{data_source}.csv")
