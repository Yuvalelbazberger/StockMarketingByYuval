import pandas as pd

from src.utils.config import TICKERS_PATH


def load_ticker_metadata(path=TICKERS_PATH):
    metadata = pd.read_csv(path)
    required_columns = {"ticker", "sector"}
    missing = required_columns.difference(metadata.columns)
    if missing:
        raise ValueError(
            "Ticker metadata is missing required columns: "
            + ", ".join(sorted(missing))
        )

    metadata = metadata[["ticker", "sector"]].copy()
    metadata["ticker"] = metadata["ticker"].astype(str).str.strip().str.upper()
    metadata["sector"] = metadata["sector"].fillna("Unclassified").astype(str).str.strip()
    metadata.loc[metadata["sector"] == "", "sector"] = "Unclassified"
    return metadata.drop_duplicates("ticker", keep="last")


def add_ticker_metadata(dataframe, metadata=None):
    dataframe = dataframe.copy()
    metadata = load_ticker_metadata() if metadata is None else metadata.copy()

    existing_columns = [
        column for column in ["sector", "ticker_display"] if column in dataframe.columns
    ]
    if existing_columns:
        dataframe = dataframe.drop(columns=existing_columns)

    dataframe = dataframe.merge(metadata[["ticker", "sector"]], on="ticker", how="left")
    dataframe["sector"] = dataframe["sector"].fillna("Unclassified")
    dataframe["ticker_display"] = (
        dataframe["ticker"].astype(str) + " (" + dataframe["sector"] + ")"
    )
    return dataframe
