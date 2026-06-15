import time
from datetime import datetime

import yfinance as yf

from src.utils.config import (
    TICKERS,
    RAW_PRICES_PATH,
    INGESTION_LOG_PATH,
)


UPDATE_EVERY_SECONDS = 300


def fetch_market_data():
    print(f"[{datetime.now()}] Fetching market data...")

    data = yf.download(
        tickers=TICKERS,
        period="5d",
        interval="5m",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )

    if data.empty:
        print("No data returned from yfinance")
        return

    RAW_PRICES_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(RAW_PRICES_PATH)

    INGESTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INGESTION_LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(
            f"{datetime.now()}, tickers={len(TICKERS)}, rows={len(data)}\n"
        )

    print(f"Updated {len(TICKERS)} tickers")
    print(f"Saved to: {RAW_PRICES_PATH}")


def main():
    while True:
        try:
            fetch_market_data()
        except Exception as error:
            print(f"Error while updating data: {error}")

        print(f"Waiting {UPDATE_EVERY_SECONDS} seconds...\n")
        time.sleep(UPDATE_EVERY_SECONDS)


if __name__ == "__main__":
    main()