import unittest

import pandas as pd

from src.analysis.generate_watchlist import add_watchlist_columns


class GenerateWatchlistTests(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame(
            [
                {
                    "ticker": "LEADER",
                    "trend": "uptrend",
                    "return_5": 0.08,
                    "return_20": 0.15,
                    "rsi_14": 65.0,
                    "volume_ratio": 1.8,
                    "volatility_20": 0.25,
                },
                {
                    "ticker": "STEADY",
                    "trend": "uptrend",
                    "return_5": 0.02,
                    "return_20": 0.08,
                    "rsi_14": 55.0,
                    "volume_ratio": 1.1,
                    "volatility_20": 0.20,
                },
                {
                    "ticker": "HOT",
                    "trend": "uptrend",
                    "return_5": 0.06,
                    "return_20": 0.12,
                    "rsi_14": 75.0,
                    "volume_ratio": 1.4,
                    "volatility_20": 0.40,
                },
                {
                    "ticker": "WEAK",
                    "trend": "downtrend",
                    "return_5": -0.04,
                    "return_20": -0.10,
                    "rsi_14": 28.0,
                    "volume_ratio": 1.5,
                    "volatility_20": 0.60,
                },
            ]
        )

    def test_builds_both_watchlist_categories(self):
        result = add_watchlist_columns(self.data, top_limit=1).set_index("ticker")

        self.assertTrue(result.loc["LEADER", "top_opportunity"])
        self.assertTrue(result.loc["LEADER", "high_momentum"])
        self.assertEqual(
            result.loc["LEADER", "watchlist_category"],
            "Top Opportunity, High Momentum",
        )
        self.assertTrue(result.loc["HOT", "high_momentum"])
        self.assertFalse(result.loc["HOT", "top_opportunity"])
        self.assertFalse(result.loc["WEAK", "watchlist_member"])

    def test_ranks_watchlist_by_opportunity_score(self):
        result = add_watchlist_columns(self.data, top_limit=1).set_index("ticker")

        self.assertEqual(result.loc["LEADER", "watchlist_rank"], 1)
        self.assertIn("5-day return +8.00%", result.loc["LEADER", "watchlist_reason"])
        self.assertEqual(result.loc["WEAK", "watchlist_reason"], "")


if __name__ == "__main__":
    unittest.main()
