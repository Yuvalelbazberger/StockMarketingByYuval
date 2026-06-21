import numpy as np
import pandas as pd

from src.analysis.generate_alerts import add_alert_columns
from src.utils.config import MARTS_DATA_DIR


STOCK_FEATURES_PATH = MARTS_DATA_DIR / "stock_features.parquet"
STOCK_INSIGHTS_PATH = MARTS_DATA_DIR / "stock_insights.csv"
TABLEAU_EXPORT_PATH = MARTS_DATA_DIR / "tableau_stock_dashboard.csv"


def format_pct(value):
    if pd.isna(value):
        return "unknown"
    return f"{value * 100:.2f}%"


def classify_risk(row):
    volatility = row.get("volatility_20", np.nan)
    rsi = row.get("rsi_14", np.nan)
    signal = row.get("signal", "neutral")

    if signal in ["negative_momentum", "overbought"] or volatility > 0.55:
        return "High"
    if signal in ["positive_momentum", "oversold"] or volatility < 0.25:
        return "Medium"
    return "Medium"


def build_insight(row):
    ticker = row["ticker"]
    trend = row["trend"]
    signal = row["signal"]

    close = row["close"]
    return_5 = row.get("return_5", np.nan)
    return_20 = row.get("return_20", np.nan)
    rsi = row.get("rsi_14", np.nan)
    volume_ratio = row.get("volume_ratio", np.nan)

    if trend == "uptrend" and signal == "positive_momentum":
        conclusion = (
            f"{ticker} is showing positive momentum. "
            f"The stock is trading in an uptrend, with a recent 5-period return of {format_pct(return_5)}."
        )
    elif trend == "uptrend" and signal == "overbought":
        conclusion = (
            f"{ticker} is in an uptrend, but the RSI is elevated. "
            f"This may indicate short-term overbought conditions and possible pullback risk."
        )
    elif trend == "downtrend" and signal == "negative_momentum":
        conclusion = (
            f"{ticker} is showing negative momentum. "
            f"The stock is trading below key moving averages, suggesting short-term weakness."
        )
    elif signal == "oversold":
        conclusion = (
            f"{ticker} appears oversold based on RSI. "
            f"This may indicate selling pressure, but also a potential reversal watchlist candidate."
        )
    elif trend == "sideways":
        conclusion = (
            f"{ticker} is currently moving sideways. "
            f"There is no clear directional trend based on the current moving-average structure."
        )
    else:
        conclusion = (
            f"{ticker} has a neutral technical profile. "
            f"No strong trend or momentum signal is currently detected."
        )

    extra = (
        f" Latest close: {close:.2f}. "
        f"20-period return: {format_pct(return_20)}. "
    )

    if not pd.isna(rsi):
        extra += f"RSI: {rsi:.1f}. "

    if not pd.isna(volume_ratio):
        extra += f"Volume is {volume_ratio:.2f}x its recent average."

    return conclusion + extra


def main():
    features = pd.read_parquet(STOCK_FEATURES_PATH)

    latest = (
        features
        .sort_values("datetime")
        .groupby("ticker", as_index=False)
        .tail(1)
        .copy()
    )
    latest = add_alert_columns(latest)

    latest["risk_level"] = latest.apply(classify_risk, axis=1)
    latest["insight"] = latest.apply(build_insight, axis=1)

    latest["return_5_pct"] = latest["return_5"] * 100
    latest["return_20_pct"] = latest["return_20"] * 100
    latest["last_updated"] = pd.to_datetime(latest["datetime"])

    output_columns = [
        "last_updated",
        "ticker",
        "close",
        "daily_change_pct",
        "return_5_pct",
        "return_20_pct",
        "ma_20",
        "ma_50",
        "volatility_20",
        "rsi_14",
        "volume",
        "volume_ratio",
        "trend",
        "signal",
        "risk_level",
        "alert_active",
        "alert_type",
        "alert_message",
        "insight",
    ]

    insights = latest[output_columns].sort_values(["risk_level", "ticker"])

    MARTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    insights.to_csv(STOCK_INSIGHTS_PATH, index=False)
    insights.to_csv(TABLEAU_EXPORT_PATH, index=False)

    print(f"Created insights for {len(insights)} tickers")
    print(f"Saved insights to: {STOCK_INSIGHTS_PATH}")
    print(f"Saved Tableau export to: {TABLEAU_EXPORT_PATH}")

    print("\nPreview:")
    print(insights[["ticker", "trend", "signal", "risk_level", "insight"]])


if __name__ == "__main__":
    main()
