import unittest

import pandas as pd

from src.analysis.ticker_metadata import add_ticker_metadata


class TickerMetadataTests(unittest.TestCase):
    def test_adds_sector_and_clean_display_label(self):
        data = pd.DataFrame({"ticker": ["AAPL", "UNKNOWN"]})
        metadata = pd.DataFrame(
            {
                "ticker": ["AAPL"],
                "sector": ["Technology"],
                "company_name": ["Apple Inc."],
            }
        )

        result = add_ticker_metadata(data, metadata).set_index("ticker")

        self.assertEqual(result.loc["AAPL", "sector"], "Technology")
        self.assertEqual(result.loc["AAPL", "company_name"], "Apple Inc.")
        self.assertEqual(
            result.loc["AAPL", "ticker_display"], "AAPL (Technology)"
        )
        self.assertEqual(result.loc["UNKNOWN", "sector"], "Unclassified")
        self.assertEqual(result.loc["UNKNOWN", "company_name"], "UNKNOWN")
        self.assertEqual(
            result.loc["UNKNOWN", "ticker_display"],
            "UNKNOWN (Unclassified)",
        )


if __name__ == "__main__":
    unittest.main()
