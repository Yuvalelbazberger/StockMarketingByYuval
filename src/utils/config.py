from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
STAGING_DATA_DIR = DATA_DIR / "staging"
MARTS_DATA_DIR = DATA_DIR / "marts"

RAW_PRICES_PATH = RAW_DATA_DIR / "market_prices.parquet"
INGESTION_LOG_PATH = RAW_DATA_DIR / "ingestion_log.csv"


# Market data settings
TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMD",
    "TSLA",
    "META",
    "GOOGL",
    "SPY",
    "QQQ",
]

START_DATE = "2020-01-01"
END_DATE = None  # None means up to the latest available trading day

DATA_SOURCE = "yfinance"