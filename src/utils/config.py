from pathlib import Path
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
INPUT_DATA_DIR = DATA_DIR / "input"
RAW_DATA_DIR = DATA_DIR / "raw"
STAGING_DATA_DIR = DATA_DIR / "staging"
MARTS_DATA_DIR = DATA_DIR / "marts"

TICKERS_PATH = INPUT_DATA_DIR / "tickers.csv"
RAW_PRICES_PATH = RAW_DATA_DIR / "market_prices.parquet"
INGESTION_LOG_PATH = RAW_DATA_DIR / "ingestion_log.csv"


# Market data settings
def load_tickers():
    if not TICKERS_PATH.exists():
        raise FileNotFoundError(
            f"Missing tickers file: {TICKERS_PATH}. "
            "Create data/input/tickers.csv with a ticker column."
        )

    tickers_df = pd.read_csv(TICKERS_PATH)

    if "ticker" not in tickers_df.columns:
        raise ValueError("tickers.csv must contain a column named 'ticker'.")

    tickers = (
        tickers_df["ticker"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
        .tolist()
    )

    if not tickers:
        raise ValueError("tickers.csv is empty. Add at least one ticker.")

    return tickers


TICKERS = load_tickers()

START_DATE = "2020-01-01"
END_DATE = None  # None means up to the latest available trading day

DATA_SOURCE = "yfinance"

INPUT_DATA_DIR = DATA_DIR / "input"
TICKERS_PATH = INPUT_DATA_DIR / "tickers.csv"