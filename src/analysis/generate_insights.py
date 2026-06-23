import numpy as np
import pandas as pd

from src.analysis.generate_alerts import add_alert_columns
from src.analysis.generate_executive_summary import KPI_COLUMNS, save_executive_summary
from src.analysis.generate_watchlist import add_watchlist_columns
from src.analysis.market_movers import add_market_mover_columns
from src.analysis.risk_model import add_risk_columns
from src.analysis.ticker_metadata import add_ticker_metadata
from src.utils.config import MARTS_DATA_DIR


STOCK_FEATURES_PATH = MARTS_DATA_DIR / "stock_features.parquet"
STOCK_INSIGHTS_PATH = MARTS_DATA_DIR / "stock_insights.csv"
TABLEAU_EXPORT_PATH = MARTS_DATA_DIR / "tableau_stock_dashboard.csv"
STOCK_WATCHLIST_PATH = MARTS_DATA_DIR / "stock_watchlist.csv"


def format_pct(value):
    if pd.isna(value):
        return "unknown"
    return f"{value * 100:.2f}%"


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
    latest = add_ticker_metadata(latest)
    latest = add_alert_columns(latest)
    latest = add_watchlist_columns(latest)
    latest = add_risk_columns(latest)
    latest = add_market_mover_columns(latest)

    latest["insight"] = latest.apply(build_insight, axis=1)

    latest["return_5_pct"] = latest["return_5"] * 100
    latest["return_20_pct"] = latest["return_20"] * 100
    latest["last_updated"] = pd.to_datetime(latest["datetime"])
    summary = save_executive_summary(latest)
    for column in KPI_COLUMNS:
        latest[column] = summary.iloc[0][column]

    output_columns = [
        "last_updated",
        "ticker",
        "ticker_display",
        "sector",
        "company_name",
        "close",
        "daily_change_pct",
        "abs_daily_change_pct",
        "return_5_pct",
        "return_20_pct",
        "ma_20",
        "ma_50",
        "volatility_20",
        "rsi_14",
        "volume",
        "volume_ratio",
        "relative_volume_10d",
        "trend",
        "signal",
        "mover_direction",
        "mover_rank",
        "gainer_rank",
        "loser_rank",
        "top_gainer",
        "top_loser",
        "unusual_volume",
        "market_mover",
        "market_mover_bucket",
        "market_mover_reason",
        "risk_level",
        "risk_score",
        "risk_reason",
        "alert_active",
        "alert_type",
        "alert_message",
        "watchlist_member",
        "watchlist_category",
        "watchlist_rank",
        "opportunity_score",
        "top_opportunity",
        "high_momentum",
        "watchlist_reason",
        *KPI_COLUMNS,
        "insight",
    ]

    insights = latest[output_columns].sort_values(["risk_level", "ticker"])

    MARTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    insights.to_csv(STOCK_INSIGHTS_PATH, index=False)
    insights.to_csv(TABLEAU_EXPORT_PATH, index=False)
    watchlist = insights.loc[insights["watchlist_member"]].sort_values(
        ["watchlist_rank", "ticker"]
    )
    watchlist.to_csv(STOCK_WATCHLIST_PATH, index=False)

    print(f"Created insights for {len(insights)} tickers")
    print(f"Saved insights to: {STOCK_INSIGHTS_PATH}")
    print(f"Saved Tableau export to: {TABLEAU_EXPORT_PATH}")
    print(f"Saved watchlist to: {STOCK_WATCHLIST_PATH}")
    print(
        f"Watchlist: {len(watchlist)} stocks, "
        f"{int(watchlist['top_opportunity'].sum())} top opportunities, "
        f"{int(watchlist['high_momentum'].sum())} high momentum"
    )

    print("\nPreview:")
    print(
        insights[
            [
                "ticker",
                "trend",
                "signal",
                "risk_level",
                "watchlist_category",
                "insight",
            ]
        ]
    )


if __name__ == "__main__":
    main()
