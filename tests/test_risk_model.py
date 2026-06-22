import unittest

import pandas as pd

from src.analysis.risk_model import add_risk_columns


class RiskModelTests(unittest.TestCase):
    def test_creates_low_medium_and_high_risk_levels(self):
        data = pd.DataFrame(
            [
                {
                    "ticker": "CALM",
                    "trend": "uptrend",
                    "return_5": 0.01,
                    "rsi_14": 50.0,
                    "volatility_20": 0.10,
                },
                {
                    "ticker": "MIXED",
                    "trend": "sideways",
                    "return_5": 0.04,
                    "rsi_14": 62.0,
                    "volatility_20": 0.35,
                },
                {
                    "ticker": "RISKY",
                    "trend": "downtrend",
                    "return_5": -0.12,
                    "rsi_14": 20.0,
                    "volatility_20": 0.80,
                },
            ]
        )

        result = add_risk_columns(data).set_index("ticker")

        self.assertEqual(result.loc["CALM", "risk_level"], "Low")
        self.assertEqual(result.loc["MIXED", "risk_level"], "Medium")
        self.assertEqual(result.loc["RISKY", "risk_level"], "High")
        self.assertIn("downtrend", result.loc["RISKY", "risk_reason"])
        self.assertGreater(result.loc["RISKY", "risk_score"], 65)
