import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from src.export import email_alerts


class EmailAlertsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.alerts_path = Path(self.temp_dir.name) / "stock_alerts.csv"
        pd.DataFrame(
            [
                {
                    "datetime": "2026-06-18",
                    "ticker": "AAPL",
                    "close": 200.0,
                    "daily_change_pct": 6.25,
                    "rsi_14": 72.0,
                    "alert_type": "RSI_OVERBOUGHT, DAILY_MOVE",
                    "alert_message": "AAPL alert",
                }
            ]
        ).to_csv(self.alerts_path, index=False)
        self.summary_path = Path(self.temp_dir.name) / "executive_summary.csv"
        pd.DataFrame(
            [
                {
                    "market_regime": "Mixed",
                    "market_breadth_pct": 52.5,
                    "watchlist_count": 17,
                    "high_risk_count": 8,
                    "executive_summary": "Leadership is selective.",
                    "business_implications": "Focus on stock-level signals.",
                    "top_opportunities": "AMD, ARM",
                    "key_risks": "PLTR, WDAY",
                    "recommended_actions": "Review leaders and risks.",
                }
            ]
        ).to_csv(self.summary_path, index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_builds_readable_alert_email(self):
        alerts = pd.read_csv(self.alerts_path)
        summary = pd.read_csv(self.summary_path)

        message = email_alerts.build_alert_email(
            alerts,
            "sender@example.com",
            ["recipient@example.com"],
            summary=summary,
        )

        self.assertIn("MarketPulse Daily Brief | Mixed", message["Subject"])
        plain = message.get_body(preferencelist=("plain",)).get_content()
        html = message.get_body(preferencelist=("html",)).get_content()
        self.assertIn("AAPL: RSI_OVERBOUGHT, DAILY_MOVE", plain)
        self.assertIn("daily change +6.25%", plain)
        self.assertIn("Executive Snapshot", html)
        self.assertIn("Top Opportunities", html)
        self.assertIn("AMD, ARM", html)
        self.assertIn("Open Market Dashboard", html)

    def test_sends_email_with_configured_smtp(self):
        smtp = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp

        with (
            patch.object(email_alerts, "STOCK_ALERTS_PATH", self.alerts_path),
            patch.object(
                email_alerts,
                "EXECUTIVE_SUMMARY_PATH",
                self.summary_path,
            ),
            patch.object(email_alerts.smtplib, "SMTP_SSL", return_value=smtp_context),
            patch.dict(
                os.environ,
                {
                    "SMTP_USERNAME": "sender@example.com",
                    "SMTP_PASSWORD": "app-password",
                    "ALERT_EMAIL_TO": "recipient@example.com",
                },
                clear=False,
            ),
        ):
            sent = email_alerts.send_alert_email()

        self.assertTrue(sent)
        smtp.login.assert_called_once_with("sender@example.com", "app-password")
        smtp.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
