import pandas as pd

from src.utils.config import MARTS_DATA_DIR


STOCK_FEATURES_PATH = MARTS_DATA_DIR / "stock_features.parquet"
STOCK_ALERTS_PATH = MARTS_DATA_DIR / "stock_alerts.csv"

RSI_OVERBOUGHT_THRESHOLD = 70
RSI_OVERSOLD_THRESHOLD = 30
DAILY_MOVE_THRESHOLD = 0.05


def alert_types_for_row(row):
    alert_types = []
    rsi = row.get("rsi_14")
    daily_return = row.get("return_1")

    if pd.notna(rsi) and rsi > RSI_OVERBOUGHT_THRESHOLD:
        alert_types.append("RSI_OVERBOUGHT")
    elif pd.notna(rsi) and rsi < RSI_OVERSOLD_THRESHOLD:
        alert_types.append("RSI_OVERSOLD")

    if pd.notna(daily_return) and abs(daily_return) > DAILY_MOVE_THRESHOLD:
        alert_types.append("DAILY_MOVE")

    return alert_types


def alert_message_for_row(row, alert_types):
    if not alert_types:
        return ""

    ticker = row["ticker"]
    details = []

    if "RSI_OVERBOUGHT" in alert_types:
        details.append(f"RSI is {row['rsi_14']:.1f}, above 70")
    if "RSI_OVERSOLD" in alert_types:
        details.append(f"RSI is {row['rsi_14']:.1f}, below 30")
    if "DAILY_MOVE" in alert_types:
        details.append(f"daily move is {row['return_1'] * 100:+.2f}%")

    return f"{ticker}: " + "; ".join(details)


def add_alert_columns(dataframe):
    dataframe = dataframe.copy()
    alert_types = dataframe.apply(alert_types_for_row, axis=1)

    dataframe["daily_change_pct"] = dataframe["return_1"] * 100
    dataframe["alert_active"] = alert_types.map(bool)
    dataframe["alert_type"] = alert_types.map(lambda values: ", ".join(values))
    dataframe["alert_message"] = [
        alert_message_for_row(row, types)
        for (_, row), types in zip(dataframe.iterrows(), alert_types)
    ]

    return dataframe


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

    alert_columns = [
        "datetime",
        "ticker",
        "close",
        "daily_change_pct",
        "rsi_14",
        "alert_type",
        "alert_message",
    ]
    alerts = latest.loc[latest["alert_active"], alert_columns].copy()

    MARTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    alerts.to_csv(STOCK_ALERTS_PATH, index=False)

    print(f"Created {len(alerts)} alerts for {alerts['ticker'].nunique()} tickers")
    print(f"Saved alerts to: {STOCK_ALERTS_PATH}")
    if not alerts.empty:
        print(alerts[["ticker", "alert_type", "alert_message"]].to_string(index=False))

    return alerts


if __name__ == "__main__":
    main()
