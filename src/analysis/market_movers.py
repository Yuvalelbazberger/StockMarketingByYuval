import numpy as np
import pandas as pd


TOP_MOVERS_LIMIT = 15
UNUSUAL_VOLUME_THRESHOLD = 1.5


def _rank_subset(values, mask, ascending):
    ranks = pd.Series(pd.NA, index=values.index, dtype="Int64")
    ranked = values.loc[mask].rank(method="first", ascending=ascending)
    ranks.loc[mask] = ranked.astype("Int64")
    return ranks


def add_market_mover_columns(
    dataframe,
    top_limit=TOP_MOVERS_LIMIT,
    unusual_volume_threshold=UNUSUAL_VOLUME_THRESHOLD,
):
    dataframe = dataframe.copy()

    dataframe["relative_volume_10d"] = pd.to_numeric(
        dataframe.get("relative_volume_10d", dataframe.get("volume_ratio")),
        errors="coerce",
    )
    dataframe["daily_change_pct"] = pd.to_numeric(
        dataframe.get("daily_change_pct"),
        errors="coerce",
    )
    dataframe["abs_daily_change_pct"] = dataframe["daily_change_pct"].abs()

    dataframe["mover_direction"] = np.select(
        [
            dataframe["daily_change_pct"] > 0,
            dataframe["daily_change_pct"] < 0,
        ],
        ["Gainer", "Loser"],
        default="Flat",
    )

    gainer_mask = dataframe["daily_change_pct"] > 0
    loser_mask = dataframe["daily_change_pct"] < 0
    dataframe["gainer_rank"] = _rank_subset(
        dataframe["daily_change_pct"],
        gainer_mask,
        ascending=False,
    )
    dataframe["loser_rank"] = _rank_subset(
        dataframe["daily_change_pct"],
        loser_mask,
        ascending=True,
    )
    dataframe["mover_rank"] = dataframe["abs_daily_change_pct"].rank(
        method="first",
        ascending=False,
    ).astype("Int64")

    dataframe["top_gainer"] = gainer_mask & (dataframe["gainer_rank"] <= top_limit)
    dataframe["top_loser"] = loser_mask & (dataframe["loser_rank"] <= top_limit)
    dataframe["unusual_volume"] = (
        dataframe["relative_volume_10d"] >= unusual_volume_threshold
    )
    dataframe["market_mover"] = (
        dataframe["top_gainer"]
        | dataframe["top_loser"]
        | dataframe["unusual_volume"]
    )

    dataframe["market_mover_bucket"] = np.select(
        [
            dataframe["top_gainer"] & dataframe["unusual_volume"],
            dataframe["top_loser"] & dataframe["unusual_volume"],
            dataframe["top_gainer"],
            dataframe["top_loser"],
            dataframe["unusual_volume"],
        ],
        [
            "Top Gainer + Unusual Volume",
            "Top Loser + Unusual Volume",
            "Top Gainer",
            "Top Loser",
            "Unusual Volume",
        ],
        default="Normal",
    )

    dataframe["market_mover_reason"] = dataframe.apply(_market_mover_reason, axis=1)
    return dataframe


def _market_mover_reason(row):
    if not row.get("market_mover", False):
        return ""

    reasons = [row["market_mover_bucket"]]
    if pd.notna(row.get("daily_change_pct")):
        reasons.append(f"daily move {row['daily_change_pct']:+.2f}%")
    if pd.notna(row.get("relative_volume_10d")):
        reasons.append(f"relative volume {row['relative_volume_10d']:.2f}x")
    return "; ".join(reasons)
