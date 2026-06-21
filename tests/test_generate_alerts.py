import unittest

import pandas as pd

from src.analysis.generate_alerts import add_alert_columns


class GenerateAlertsTests(unittest.TestCase):
    def test_combines_rsi_and_daily_move_alerts(self):
        data = pd.DataFrame(
            [
                {"ticker": "HIGH", "rsi_14": 71.0, "return_1": 0.06},
                {"ticker": "LOW", "rsi_14": 29.0, "return_1": -0.051},
            ]
        )

        result = add_alert_columns(data).set_index("ticker")

        self.assertEqual(result.loc["HIGH", "alert_type"], "RSI_OVERBOUGHT, DAILY_MOVE")
        self.assertEqual(result.loc["LOW", "alert_type"], "RSI_OVERSOLD, DAILY_MOVE")
        self.assertAlmostEqual(result.loc["HIGH", "daily_change_pct"], 6.0)
        self.assertTrue(result.loc["HIGH", "alert_active"])

    def test_threshold_values_do_not_trigger(self):
        data = pd.DataFrame(
            [
                {"ticker": "UPPER", "rsi_14": 70.0, "return_1": 0.05},
                {"ticker": "LOWER", "rsi_14": 30.0, "return_1": -0.05},
            ]
        )

        result = add_alert_columns(data)

        self.assertFalse(result["alert_active"].any())
        self.assertTrue((result["alert_type"] == "").all())


if __name__ == "__main__":
    unittest.main()
