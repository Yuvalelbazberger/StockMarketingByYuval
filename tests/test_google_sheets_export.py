import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from googleapiclient.errors import HttpError

from src.export import google_sheets_export


class GoogleSheetsExportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.export_path = Path(self.temp_dir.name) / "dashboard.csv"
        pd.DataFrame({"ticker": ["AAPL"], "signal": ["neutral"]}).to_csv(
            self.export_path,
            index=False,
        )
        self.summary_path = Path(self.temp_dir.name) / "executive_summary.csv"
        pd.DataFrame(
            [
                {
                    "analysis_date": "2026-06-22",
                    "tracked_stocks": 101,
                    "executive_summary": "Mixed market",
                }
            ]
        ).to_csv(self.summary_path, index=False)

        self.credentials = MagicMock()
        self.credentials.service_account_email = "dashboard@example.iam.gserviceaccount.com"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upload_clears_and_updates_sheet(self):
        service = MagicMock()
        service.spreadsheets.return_value.get.return_value.execute.return_value = {
            "sheets": [{"properties": {"title": "dashboard_data"}}]
        }
        values = service.spreadsheets.return_value.values.return_value
        values.get.return_value.execute.return_value = {"values": []}

        with (
            patch.object(google_sheets_export, "LOOKER_EXPORT_PATH", self.export_path),
            patch.object(
                google_sheets_export,
                "EXECUTIVE_SUMMARY_PATH",
                self.summary_path,
            ),
            patch.object(
                google_sheets_export,
                "load_credentials",
                return_value=self.credentials,
            ),
            patch.object(google_sheets_export, "build", return_value=service),
        ):
            google_sheets_export.upload_to_google_sheets()

        values.clear.assert_called_once()
        self.assertEqual(values.update.call_count, 2)
        values.append.assert_called_once()
        service.spreadsheets.return_value.batchUpdate.assert_called_once()

    def test_updates_existing_summary_for_the_same_date(self):
        service = MagicMock()
        service.spreadsheets.return_value.get.return_value.execute.return_value = {
            "sheets": [
                {"properties": {"title": "dashboard_data"}},
                {"properties": {"title": "daily_executive_summary"}},
            ]
        }
        values = service.spreadsheets.return_value.values.return_value
        values.get.return_value.execute.return_value = {
            "values": [["analysis_date"], ["2026-06-22"]]
        }

        with (
            patch.object(google_sheets_export, "LOOKER_EXPORT_PATH", self.export_path),
            patch.object(
                google_sheets_export,
                "EXECUTIVE_SUMMARY_PATH",
                self.summary_path,
            ),
            patch.object(
                google_sheets_export,
                "load_credentials",
                return_value=self.credentials,
            ),
            patch.object(google_sheets_export, "build", return_value=service),
        ):
            google_sheets_export.upload_to_google_sheets()

        self.assertEqual(values.update.call_count, 2)
        summary_update = values.update.call_args_list[1].kwargs
        self.assertEqual(summary_update["range"], "daily_executive_summary!A2")
        values.append.assert_not_called()
        service.spreadsheets.return_value.batchUpdate.assert_not_called()

    def test_403_explains_how_to_grant_access(self):
        response = MagicMock(status=403, reason="Forbidden")
        error = HttpError(response, b'{"error": {"message": "Forbidden"}}')
        service = MagicMock()
        service.spreadsheets.return_value.get.return_value.execute.return_value = {
            "sheets": [
                {"properties": {"title": "dashboard_data"}},
                {"properties": {"title": "daily_executive_summary"}},
            ]
        }
        service.spreadsheets.return_value.values.return_value.clear.return_value.execute.side_effect = error

        with (
            patch.object(google_sheets_export, "LOOKER_EXPORT_PATH", self.export_path),
            patch.object(
                google_sheets_export,
                "EXECUTIVE_SUMMARY_PATH",
                self.summary_path,
            ),
            patch.object(
                google_sheets_export,
                "load_credentials",
                return_value=self.credentials,
            ),
            patch.object(google_sheets_export, "build", return_value=service),
            self.assertRaisesRegex(
                PermissionError,
                "dashboard@example.iam.gserviceaccount.com as an Editor",
            ),
        ):
            google_sheets_export.upload_to_google_sheets()


if __name__ == "__main__":
    unittest.main()
