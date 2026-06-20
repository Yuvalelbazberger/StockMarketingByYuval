import json
import os
from pathlib import Path

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.config import MARTS_DATA_DIR


LOOKER_EXPORT_PATH = MARTS_DATA_DIR / "tableau_stock_dashboard.csv"

SERVICE_ACCOUNT_FILE = Path("secrets/google_service_account.json")

SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID") or "1Bc_uMtB-hSLzinsDJmL-_Kp8qiXTaj2HBnB2ZJjI-aY"

SHEET_NAME = "dashboard_data"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def prepare_dataframe_for_sheets(df):
    df = df.copy()

    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.strftime("%Y-%m-%d %H:%M:%S")

    df = df.replace([float("inf"), float("-inf")], "")
    df = df.fillna("")

    return df


def load_credentials():
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        try:
            service_account_info = json.loads(service_account_json)
        except json.JSONDecodeError as error:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON. "
                "Store the complete service-account JSON as the GitHub secret value."
            ) from error

        return Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
        )

    if not SERVICE_ACCOUNT_FILE.exists():
        raise FileNotFoundError(
            f"Missing service account file: {SERVICE_ACCOUNT_FILE}"
        )

    return Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )


def permission_error(credentials):
    service_account_email = getattr(credentials, "service_account_email", "unknown")
    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"

    return PermissionError(
        "Google Sheets denied access. Share the spreadsheet with "
        f"{service_account_email} as an Editor, and verify that GOOGLE_SHEET_ID "
        f"points to the same spreadsheet: {spreadsheet_url}"
    )


def upload_to_google_sheets():
    if not LOOKER_EXPORT_PATH.exists():
        raise FileNotFoundError(
            f"Missing file: {LOOKER_EXPORT_PATH}. "
            "Run python -m src.analysis.generate_insights first."
        )

    df = pd.read_csv(LOOKER_EXPORT_PATH)
    df = prepare_dataframe_for_sheets(df)

    values = [df.columns.tolist()] + df.values.tolist()

    credentials = load_credentials()

    service = build("sheets", "v4", credentials=credentials)
    sheet = service.spreadsheets()

    try:
        sheet.values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:Z",
        ).execute()

        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body={"values": values},
        ).execute()
    except HttpError as error:
        if error.resp.status == 403:
            raise permission_error(credentials) from error
        raise

    print(f"Uploaded {len(df)} rows to Google Sheets")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"Sheet name: {SHEET_NAME}")


if __name__ == "__main__":
    upload_to_google_sheets()
