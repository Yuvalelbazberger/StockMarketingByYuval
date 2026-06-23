import unittest

import pandas as pd

from src.analysis.market_movers import add_market_mover_columns


class MarketMoversTests(unittest.TestCase):
    def test_ranks_gainers_losers_and_unusual_volume(self):
        data = pd.DataFrame(
            [
                {"ticker": "BIGUP", "daily_change_pct": 6.0, "relative_volume_10d": 2.1},
                {"ticker": "SMALLUP", "daily_change_pct": 2.0, "relative_volume_10d": 0.9},
                {"ticker": "BIGDOWN", "daily_change_pct": -5.5, "relative_volume_10d": 1.8},
                {"ticker": "FLAT", "daily_change_pct": 0.0, "relative_volume_10d": 1.0},
            ]
        )

        result = add_market_mover_columns(data, top_limit=1).set_index("ticker")

        self.assertEqual(result.loc["BIGUP", "mover_direction"], "Gainer")
        self.assertEqual(result.loc["BIGUP", "gainer_rank"], 1)
        self.assertTrue(result.loc["BIGUP", "top_gainer"])
        self.assertTrue(result.loc["BIGUP", "unusual_volume"])
        self.assertEqual(
            result.loc["BIGUP", "market_mover_bucket"],
            "Top Gainer + Unusual Volume",
        )

        self.assertEqual(result.loc["BIGDOWN", "mover_direction"], "Loser")
        self.assertEqual(result.loc["BIGDOWN", "loser_rank"], 1)
        self.assertTrue(result.loc["BIGDOWN", "top_loser"])
        self.assertIn(
            "daily move -5.50%",
            result.loc["BIGDOWN", "market_mover_reason"],
        )

        self.assertEqual(result.loc["FLAT", "mover_direction"], "Flat")
        self.assertFalse(result.loc["FLAT", "market_mover"])


if __name__ == "__main__":
    unittest.main()
