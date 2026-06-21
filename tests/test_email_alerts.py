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

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_builds_readable_alert_email(self):
        alerts = pd.read_csv(self.alerts_path)

        message = email_alerts.build_alert_email(
            alerts,
            "sender@example.com",
            ["recipient@example.com"],
        )

        self.assertIn("1 signals for 2026-06-18", message["Subject"])
        self.assertIn("AAPL: RSI_OVERBOUGHT, DAILY_MOVE", message.get_content())
        self.assertIn("daily change +6.25%", message.get_content())

    def test_sends_email_with_configured_smtp(self):
        smtp = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp

        with (
            patch.object(email_alerts, "STOCK_ALERTS_PATH", self.alerts_path),
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
