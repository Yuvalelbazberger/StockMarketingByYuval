import unittest

import pandas as pd

from src.analysis.generate_executive_summary import build_executive_summary


class ExecutiveSummaryTests(unittest.TestCase):
    def test_builds_kpis_and_business_summary(self):
        data = pd.DataFrame(
            [
                {
                    "last_updated": "2026-06-22",
                    "ticker": "LEADER",
                    "return_5": 0.08,
                    "return_20": 0.12,
                    "trend": "uptrend",
                    "alert_active": True,
                    "watchlist_member": True,
                    "top_opportunity": True,
                    "high_momentum": True,
                    "watchlist_rank": 1,
                    "risk_level": "Low",
                    "risk_score": 20.0,
                },
                {
                    "last_updated": "2026-06-22",
                    "ticker": "RISKY",
                    "return_5": -0.10,
                    "return_20": -0.15,
                    "trend": "downtrend",
                    "alert_active": True,
                    "watchlist_member": False,
                    "top_opportunity": False,
                    "high_momentum": False,
                    "watchlist_rank": pd.NA,
                    "risk_level": "High",
                    "risk_score": 90.0,
                },
            ]
        )

        summary = build_executive_summary(data).iloc[0]

        self.assertEqual(summary["analysis_date"], "2026-06-22")
        self.assertEqual(summary["tracked_stocks"], 2)
        self.assertEqual(summary["active_alerts_count"], 2)
        self.assertEqual(summary["market_regime"], "Mixed")
        self.assertEqual(summary["top_opportunities"], "LEADER")
        self.assertEqual(summary["key_risks"], "RISKY")
        self.assertIn("50.0%", summary["executive_summary"])


if __name__ == "__main__":
    unittest.main()
