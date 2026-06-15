import numpy as np
import pandas as pd

from src.utils.config import RAW_PRICES_PATH, MARTS_DATA_DIR


STOCK_FEATURES_PATH = MARTS_DATA_DIR / "stock_features.parquet"


def calculate_rsi(close_prices, window=14):
    delta = close_prices.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.rolling(window).mean()
    avg_loss = losses.rolling(window).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def split_by_ticker(raw_data):
    if not isinstance(raw_data.columns, pd.MultiIndex):
        yield "UNKNOWN", raw_data
        return

    first_level = raw_data.columns.get_level_values(0)
    price_columns = {"Open", "High", "Low", "Close", "Volume"}

    if set(first_level).intersection(price_columns):
        tickers = raw_data.columns.get_level_values(1).unique()
        for ticker in tickers:
            yield ticker, raw_data.xs(ticker, level=1, axis=1)
    else:
        tickers = raw_data.columns.get_level_values(0).unique()
        for ticker in tickers:
            yield ticker, raw_data[ticker]


def analyze_ticker(ticker, prices):
    prices = prices.copy()

    if "Close" not in prices.columns:
        return pd.DataFrame()

    close = prices["Close"]
    volume = prices["Volume"] if "Volume" in prices.columns else pd.Series(index=prices.index)

    result = pd.DataFrame(index=prices.index)
    result["ticker"] = ticker
    result["close"] = close
    result["volume"] = volume

    result["return_1"] = close.pct_change()
    result["return_5"] = close.pct_change(5)
    result["return_20"] = close.pct_change(20)

    result["ma_20"] = close.rolling(20).mean()
    result["ma_50"] = close.rolling(50).mean()

    result["volatility_20"] = result["return_1"].rolling(20).std() * np.sqrt(252)
    result["rsi_14"] = calculate_rsi(close)

    result["volume_avg_20"] = volume.rolling(20).mean()
    result["volume_ratio"] = volume / result["volume_avg_20"]

    result["trend"] = np.select(
        [
            (result["close"] > result["ma_20"]) & (result["ma_20"] > result["ma_50"]),
            (result["close"] < result["ma_20"]) & (result["ma_20"] < result["ma_50"]),
        ],
        [
            "uptrend",
            "downtrend",
        ],
        default="sideways",
    )

    result["signal"] = np.select(
        [
            (result["trend"] == "uptrend") & (result["rsi_14"] < 70),
            (result["trend"] == "downtrend"),
            result["rsi_14"] > 70,
            result["rsi_14"] < 30,
        ],
        [
            "positive_momentum",
            "negative_momentum",
            "overbought",
            "oversold",
        ],
        default="neutral",
    )

    return result.reset_index(names="datetime")


def main():
    raw_data = pd.read_parquet(RAW_PRICES_PATH)

    all_features = []

    for ticker, ticker_prices in split_by_ticker(raw_data):
        features = analyze_ticker(ticker, ticker_prices)
        if not features.empty:
            all_features.append(features)

    if not all_features:
        raise ValueError("No features were created. Check the raw market data file.")

    stock_features = pd.concat(all_features, ignore_index=True)

    STOCK_FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
    stock_features.to_parquet(STOCK_FEATURES_PATH, index=False)

    print(f"Created features for {stock_features['ticker'].nunique()} tickers")
    print(f"Rows: {len(stock_features)}")
    print(f"Saved to: {STOCK_FEATURES_PATH}")

    latest = stock_features.sort_values("datetime").groupby("ticker").tail(1)
    print("\nLatest signals:")
    print(latest[["ticker", "close", "return_5", "rsi_14", "trend", "signal"]])


if __name__ == "__main__":
    main()