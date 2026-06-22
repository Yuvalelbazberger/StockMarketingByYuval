import unittest

import pandas as pd

from src.analysis.generate_insights import build_insight


class GenerateInsightsTests(unittest.TestCase):
    def test_builds_insight_when_optional_values_are_missing(self):
        row = pd.Series(
            {
                "ticker": "TEST",
                "trend": "sideways",
                "signal": "neutral",
                "close": 100.0,
            }
        )

        insight = build_insight(row)

        self.assertIn("TEST is currently moving sideways", insight)
        self.assertIn("20-period return: unknown", insight)


if __name__ == "__main__":
    unittest.main()
