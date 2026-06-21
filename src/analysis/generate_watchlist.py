import numpy as np
import pandas as pd


TOP_OPPORTUNITIES_LIMIT = 10


def _percentile_score(series, higher_is_better=True):
    numeric = pd.to_numeric(series, errors="coerce")
    score = numeric.rank(pct=True, method="average")
    if not higher_is_better:
        score = 1 - score
    return score.fillna(0)


def _watchlist_reason(row):
    categories = []
    if row["top_opportunity"]:
        categories.append("top opportunity")
    if row["high_momentum"]:
        categories.append("high momentum")
    if not categories:
        return ""

    return (
        f"{', '.join(categories)}; 5-day return {row['return_5'] * 100:+.2f}%; "
        f"20-day return {row['return_20'] * 100:+.2f}%; "
        f"RSI {row['rsi_14']:.1f}"
    )


def add_watchlist_columns(dataframe, top_limit=TOP_OPPORTUNITIES_LIMIT):
    dataframe = dataframe.copy()

    dataframe["opportunity_score"] = (
        _percentile_score(dataframe["return_5"]) * 35
        + _percentile_score(dataframe["return_20"]) * 35
        + _percentile_score(dataframe["volume_ratio"]) * 20
        + _percentile_score(dataframe["volatility_20"], higher_is_better=False) * 10
    ).round(1)

    top_candidates = dataframe[
        (dataframe["trend"] == "uptrend")
        & (dataframe["return_5"] > 0)
        & (dataframe["return_20"] > 0)
        & dataframe["rsi_14"].between(45, 70, inclusive="both")
    ].sort_values(
        ["opportunity_score", "ticker"],
        ascending=[False, True],
    )
    top_tickers = set(top_candidates.head(top_limit)["ticker"])

    dataframe["top_opportunity"] = dataframe["ticker"].isin(top_tickers)
    dataframe["high_momentum"] = (
        (dataframe["trend"] == "uptrend")
        & (dataframe["return_5"] >= 0.03)
        & (dataframe["return_20"] >= 0.05)
        & dataframe["rsi_14"].between(50, 80, inclusive="both")
    )
    dataframe["watchlist_member"] = (
        dataframe["top_opportunity"] | dataframe["high_momentum"]
    )

    dataframe["watchlist_category"] = np.select(
        [
            dataframe["top_opportunity"] & dataframe["high_momentum"],
            dataframe["top_opportunity"],
            dataframe["high_momentum"],
        ],
        [
            "Top Opportunity, High Momentum",
            "Top Opportunity",
            "High Momentum",
        ],
        default="",
    )

    dataframe["watchlist_rank"] = pd.Series(pd.NA, index=dataframe.index, dtype="Int64")
    watchlist_order = dataframe.loc[dataframe["watchlist_member"]].sort_values(
        ["opportunity_score", "ticker"],
        ascending=[False, True],
    )
    dataframe.loc[watchlist_order.index, "watchlist_rank"] = range(
        1, len(watchlist_order) + 1
    )
    dataframe["watchlist_reason"] = dataframe.apply(_watchlist_reason, axis=1)

    return dataframe
