from pathlib import Path

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from src.utils.config import MARTS_DATA_DIR


LOOKER_EXPORT_PATH = MARTS_DATA_DIR / "tableau_stock_dashboard.csv"

SERVICE_ACCOUNT_FILE = Path("secrets/google_service_account.json")

SPREADSHEET_ID = "1Bc_uMtB-hSLzinsDJmL-_Kp8qiXTaj2HBnB2ZJjI-aY"

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


def upload_to_google_sheets():
    if not LOOKER_EXPORT_PATH.exists():
        raise FileNotFoundError(
            f"Missing file: {LOOKER_EXPORT_PATH}. "
            "Run python -m src.analysis.generate_insights first."
        )

    if not SERVICE_ACCOUNT_FILE.exists():
        raise FileNotFoundError(
            f"Missing service account file: {SERVICE_ACCOUNT_FILE}"
        )

    df = pd.read_csv(LOOKER_EXPORT_PATH)
    df = prepare_dataframe_for_sheets(df)

    values = [df.columns.tolist()] + df.values.tolist()

    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )

    service = build("sheets", "v4", credentials=credentials)
    sheet = service.spreadsheets()

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

    print(f"Uploaded {len(df)} rows to Google Sheets")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"Sheet name: {SHEET_NAME}")


if __name__ == "__main__":
    upload_to_google_sheets()