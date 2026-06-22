import unittest
from datetime import datetime, timezone

from scripts.market_schedule import determine_market_window


class MarketScheduleTests(unittest.TestCase):
    def test_resolves_summer_market_windows(self):
        now = datetime(2026, 6, 22, 13, 0, tzinfo=timezone.utc)

        self.assertEqual(
            determine_market_window("schedule", "0 13 * * 1-5", now),
            (True, "pre_market"),
        )
        self.assertEqual(
            determine_market_window("schedule", "35 13 * * 1-5", now),
            (True, "market_open"),
        )
        self.assertEqual(
            determine_market_window("schedule", "15 20 * * 1-5", now),
            (True, "after_close"),
        )

    def test_skips_dst_candidate_at_the_wrong_utc_hour(self):
        now = datetime(2026, 6, 22, 14, 0, tzinfo=timezone.utc)

        self.assertEqual(
            determine_market_window("schedule", "0 14 * * 1-5", now),
            (False, "dst_candidate_skipped"),
        )

    def test_skips_nyse_holiday(self):
        now = datetime(2026, 6, 19, 13, 0, tzinfo=timezone.utc)

        self.assertEqual(
            determine_market_window("schedule", "0 13 * * 1-5", now),
            (False, "market_closed"),
        )

    def test_push_and_manual_runs_are_always_allowed(self):
        self.assertEqual(
            determine_market_window("push"),
            (True, "on_demand"),
        )


if __name__ == "__main__":
    unittest.main()
