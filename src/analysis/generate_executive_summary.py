from datetime import datetime, timezone

import pandas as pd

from src.utils.config import MARTS_DATA_DIR


EXECUTIVE_SUMMARY_PATH = MARTS_DATA_DIR / "executive_summary.csv"

KPI_COLUMNS = [
    "tracked_stocks",
    "active_alerts_count",
    "watchlist_count",
    "top_opportunities_count",
    "high_momentum_count",
    "uptrend_count",
    "downtrend_count",
    "high_risk_count",
    "market_breadth_pct",
    "market_regime",
    "executive_summary",
]


def _ticker_list(dataframe, limit=5):
    return ", ".join(dataframe.head(limit)["ticker"].astype(str)) or "No qualifying stocks"


def _stock_count(count, description):
    verb = "is" if count == 1 else "are"
    noun = "stock" if count == 1 else "stocks"
    return f"{count} {noun} {verb} {description}"


def build_executive_summary(insights):
    if insights.empty:
        raise ValueError("Cannot build an executive summary from an empty dataset.")

    analysis_date = pd.to_datetime(insights["last_updated"]).max().date().isoformat()
    tracked_stocks = int(len(insights))
    positive_20 = int((insights["return_20"] > 0).sum())
    market_breadth_pct = round(positive_20 / tracked_stocks * 100, 1)

    if market_breadth_pct >= 60:
        market_regime = "Broad Strength"
        business_implications = (
            "Momentum is supported by broad participation, but extended names still "
            "require risk controls."
        )
    elif market_breadth_pct <= 40:
        market_regime = "Defensive"
        business_implications = (
            "Participation is narrow; prioritize resilience and verify reversals before "
            "treating them as durable opportunities."
        )
    else:
        market_regime = "Mixed"
        business_implications = (
            "Leadership is selective, so stock-level signals matter more than the broad "
            "market direction."
        )

    top_opportunities = insights.loc[insights["top_opportunity"]].sort_values(
        ["watchlist_rank", "ticker"]
    )
    high_risk = insights.loc[insights["risk_level"] == "High"].sort_values(
        ["risk_score", "ticker"], ascending=[False, True]
    )

    counts = {
        "tracked_stocks": tracked_stocks,
        "active_alerts_count": int(insights["alert_active"].sum()),
        "watchlist_count": int(insights["watchlist_member"].sum()),
        "top_opportunities_count": int(insights["top_opportunity"].sum()),
        "high_momentum_count": int(insights["high_momentum"].sum()),
        "uptrend_count": int((insights["trend"] == "uptrend").sum()),
        "downtrend_count": int((insights["trend"] == "downtrend").sum()),
        "high_risk_count": int((insights["risk_level"] == "High").sum()),
    }
    executive_summary = (
        f"{market_regime} market: {market_breadth_pct:.1f}% of tracked stocks have a "
        f"positive 20-day return. "
        f"{_stock_count(counts['uptrend_count'], 'in an uptrend')}, "
        f"{_stock_count(counts['watchlist_count'], 'on the watchlist')}, and "
        f"{_stock_count(counts['high_risk_count'], 'high risk')}."
    )

    summary = {
        "analysis_date": analysis_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        **counts,
        "market_breadth_pct": market_breadth_pct,
        "avg_return_5_pct": round(float(insights["return_5"].mean() * 100), 2),
        "avg_return_20_pct": round(float(insights["return_20"].mean() * 100), 2),
        "market_regime": market_regime,
        "top_opportunities": _ticker_list(top_opportunities),
        "key_risks": _ticker_list(high_risk),
        "executive_summary": executive_summary,
        "business_implications": business_implications,
        "recommended_actions": (
            "Review watchlist leaders, monitor high-risk names, and validate signals "
            "against the next market update."
        ),
    }
    return pd.DataFrame([summary])


def save_executive_summary(insights):
    summary = build_executive_summary(insights)
    MARTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(EXECUTIVE_SUMMARY_PATH, index=False)
    return summary
