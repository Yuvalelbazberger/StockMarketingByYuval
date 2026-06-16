from datetime import datetime, timezone
from typing import List, Optional, Tuple

import pandas as pd
import yfinance as yf

from src.utils.config import (
    DATA_SOURCE,
    END_DATE,
    INGESTION_LOG_PATH,
    RAW_DATA_DIR,
    RAW_PRICES_PATH,
    START_DATE,
    TICKERS,
)


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

OUTPUT_COLUMNS = [
    "date",
    "ticker",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "source",
    "ingested_at_utc",
]


def _normalize_yfinance_columns(data: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes yfinance output columns.

    yfinance can sometimes return regular columns and sometimes MultiIndex columns.
    This function makes the structure predictable.
    """
    if not isinstance(data.columns, pd.MultiIndex):
        return data

    for level in range(data.columns.nlevels):
        labels = set(data.columns.get_level_values(level))
        if {"Open", "High", "Low", "Close", "Volume"}.issubset(labels):
            data = data.copy()
            data.columns = data.columns.get_level_values(level)
            return data

    raise ValueError("Could not normalize yfinance MultiIndex columns.")


def fetch_single_ticker(
    ticker: str,
    start_date: str,
    end_date: Optional[str] = None,
) -> Tuple[pd.DataFrame, dict]:
    """
    Downloads historical OHLCV data for a single ticker.

    Returns:
        - cleaned long-format DataFrame
        - ingestion log dictionary
    """
    ingested_at = datetime.now(timezone.utc).isoformat()

    try:
        raw_data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            auto_adjust=False,
            actions=False,
            progress=False,
            threads=False,
        )

        if raw_data.empty:
            raise ValueError(f"No data returned for ticker: {ticker}")

        raw_data = _normalize_yfinance_columns(raw_data)

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in raw_data.columns]
        if missing_columns:
            raise ValueError(f"Missing columns for {ticker}: {missing_columns}")

        df = raw_data.reset_index()

        df = df.rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )

        if "date" not in df.columns:
            first_column = df.columns[0]
            df = df.rename(columns={first_column: "date"})

        df["ticker"] = ticker
        df["source"] = DATA_SOURCE
        df["ingested_at_utc"] = ingested_at

        df = df[OUTPUT_COLUMNS]

        df["date"] = pd.to_datetime(df["date"]).dt.date

        numeric_columns = ["open", "high", "low", "close", "adj_close", "volume"]
        for column in numeric_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

        log_record = {
            "ticker": ticker,
            "status": "success",
            "rows_downloaded": len(df),
            "min_date": df["date"].min(),
            "max_date": df["date"].max(),
            "error": None,
            "ingested_at_utc": ingested_at,
        }

        return df, log_record

    except Exception as error:
        log_record = {
            "ticker": ticker,
            "status": "failed",
            "rows_downloaded": 0,
            "min_date": None,
            "max_date": None,
            "error": str(error),
            "ingested_at_utc": ingested_at,
        }

        return pd.DataFrame(columns=OUTPUT_COLUMNS), log_record


def run_market_data_ingestion(
    tickers: List[str],
    start_date: str,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Runs the full Stage 1 ingestion process:
    1. Downloads market data for each ticker
    2. Combines all ticker data into one table
    3. Saves the result as Parquet
    4. Saves an ingestion log as CSV
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_dataframes = []
    ingestion_logs = []

    print("Starting market data ingestion...")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date if end_date else 'latest available'}")
    print("-" * 60)

    for ticker in tickers:
        print(f"Fetching {ticker}...")

        ticker_df, log_record = fetch_single_ticker(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )

        ingestion_logs.append(log_record)

        if log_record["status"] == "success":
            all_dataframes.append(ticker_df)
            print(f"Success: {ticker} | rows: {log_record['rows_downloaded']}")
        else:
            print(f"Failed: {ticker} | error: {log_record['error']}")

    if not all_dataframes:
        raise RuntimeError("No market data was downloaded. Check tickers or connection.")

    final_df = pd.concat(all_dataframes, ignore_index=True)
    final_df = final_df.sort_values(["ticker", "date"]).reset_index(drop=True)

    ingestion_log_df = pd.DataFrame(ingestion_logs)

    final_df.to_parquet(RAW_PRICES_PATH, index=False)
    ingestion_log_df.to_csv(INGESTION_LOG_PATH, index=False)

    print("-" * 60)
    print("Ingestion completed.")
    print(f"Rows saved: {len(final_df):,}")
    print(f"Tickers saved: {final_df['ticker'].nunique()}")
    print(f"Raw prices path: {RAW_PRICES_PATH}")
    print(f"Ingestion log path: {INGESTION_LOG_PATH}")

    return final_df


def main():
    return run_market_data_ingestion(
        tickers=TICKERS,
        start_date=START_DATE,
        end_date=END_DATE,
    )


if __name__ == "__main__":
    main()
