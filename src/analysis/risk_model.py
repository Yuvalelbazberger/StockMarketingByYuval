import numpy as np
import pandas as pd


def _percentile(series):
    return pd.to_numeric(series, errors="coerce").rank(pct=True).fillna(0.5)


def _risk_reason(row):
    reasons = []
    if row["trend"] == "downtrend":
        reasons.append("downtrend")
    if row["rsi_14"] > 70:
        reasons.append("overbought RSI")
    elif row["rsi_14"] < 30:
        reasons.append("oversold RSI")
    if row["volatility_percentile"] >= 0.75:
        reasons.append("elevated volatility")
    if abs(row["return_5"]) >= 0.08:
        reasons.append("large 5-day move")
    return ", ".join(reasons) if reasons else "balanced technical risk"


def add_risk_columns(dataframe):
    dataframe = dataframe.copy()

    dataframe["volatility_percentile"] = _percentile(dataframe["volatility_20"])
    move_percentile = _percentile(dataframe["return_5"].abs())
    rsi_extremity = (
        (pd.to_numeric(dataframe["rsi_14"], errors="coerce") - 50).abs() / 50
    ).clip(0, 1).fillna(0.5)
    trend_risk = dataframe["trend"].map(
        {"uptrend": 0.0, "sideways": 0.35, "downtrend": 1.0}
    ).fillna(0.5)

    dataframe["risk_score"] = (
        dataframe["volatility_percentile"] * 40
        + rsi_extremity * 25
        + trend_risk * 20
        + move_percentile * 15
    ).round(1)
    dataframe["risk_level"] = pd.cut(
        dataframe["risk_score"],
        bins=[-np.inf, 35, 65, np.inf],
        labels=["Low", "Medium", "High"],
        right=False,
    ).astype(str)
    dataframe["risk_reason"] = dataframe.apply(_risk_reason, axis=1)

    return dataframe.drop(columns=["volatility_percentile"])
