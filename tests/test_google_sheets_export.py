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

        self.credentials = MagicMock()
        self.credentials.service_account_email = "dashboard@example.iam.gserviceaccount.com"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upload_clears_and_updates_sheet(self):
        service = MagicMock()

        with (
            patch.object(google_sheets_export, "LOOKER_EXPORT_PATH", self.export_path),
            patch.object(
                google_sheets_export,
                "load_credentials",
                return_value=self.credentials,
            ),
            patch.object(google_sheets_export, "build", return_value=service),
        ):
            google_sheets_export.upload_to_google_sheets()

        values = service.spreadsheets.return_value.values.return_value
        values.clear.assert_called_once()
        values.update.assert_called_once()

    def test_403_explains_how_to_grant_access(self):
        response = MagicMock(status=403, reason="Forbidden")
        error = HttpError(response, b'{"error": {"message": "Forbidden"}}')
        service = MagicMock()
        service.spreadsheets.return_value.values.return_value.clear.return_value.execute.side_effect = error

        with (
            patch.object(google_sheets_export, "LOOKER_EXPORT_PATH", self.export_path),
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
