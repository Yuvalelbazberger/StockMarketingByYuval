import json
import os
from pathlib import Path

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.config import MARTS_DATA_DIR


LOOKER_EXPORT_PATH = MARTS_DATA_DIR / "tableau_stock_dashboard.csv"
EXECUTIVE_SUMMARY_PATH = MARTS_DATA_DIR / "executive_summary.csv"

SERVICE_ACCOUNT_FILE = Path("secrets/google_service_account.json")

SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID") or "1Bc_uMtB-hSLzinsDJmL-_Kp8qiXTaj2HBnB2ZJjI-aY"

SHEET_NAME = "dashboard_data"
SUMMARY_SHEET_NAME = "daily_executive_summary"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def prepare_dataframe_for_sheets(df):
    df = df.copy()

    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.strftime("%Y-%m-%d %H:%M:%S")

    df = df.replace([float("inf"), float("-inf")], "")
    df = df.fillna("")

    return df


def dataframe_values(dataframe):
    return json.loads(dataframe.to_json(orient="values", date_format="iso"))


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


def ensure_sheet_exists(service, sheet_name):
    spreadsheet = service.spreadsheets()
    metadata = spreadsheet.get(
        spreadsheetId=SPREADSHEET_ID,
        fields="sheets.properties.title",
    ).execute()
    titles = {
        item.get("properties", {}).get("title")
        for item in metadata.get("sheets", [])
    }
    if sheet_name in titles:
        return

    spreadsheet.batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]},
    ).execute()


def replace_dashboard_values(sheet, dataframe):
    values = [dataframe.columns.tolist()] + dataframe_values(dataframe)
    sheet.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:AZ",
    ).execute()
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()


def upsert_daily_summary(sheet, summary):
    summary = prepare_dataframe_for_sheets(summary)
    values_api = sheet.values()
    existing = values_api.get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SUMMARY_SHEET_NAME}!A:A",
    ).execute().get("values", [])
    analysis_date = str(summary.iloc[0]["analysis_date"])
    row_values = dataframe_values(summary)[0]

    matching_row = next(
        (
            index
            for index, row in enumerate(existing, start=1)
            if row and str(row[0]) == analysis_date
        ),
        None,
    )
    if matching_row:
        values_api.update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SUMMARY_SHEET_NAME}!A{matching_row}",
            valueInputOption="RAW",
            body={"values": [row_values]},
        ).execute()
        return "updated"

    if not existing:
        row_values = summary.columns.tolist()
        values_api.update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SUMMARY_SHEET_NAME}!A1",
            valueInputOption="RAW",
            body={"values": [row_values]},
        ).execute()

    values_api.append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SUMMARY_SHEET_NAME}!A:A",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row_values]},
    ).execute()
    return "appended"


def upload_to_google_sheets():
    if not LOOKER_EXPORT_PATH.exists():
        raise FileNotFoundError(
            f"Missing file: {LOOKER_EXPORT_PATH}. "
            "Run python -m src.analysis.generate_insights first."
        )
    if not EXECUTIVE_SUMMARY_PATH.exists():
        raise FileNotFoundError(
            f"Missing file: {EXECUTIVE_SUMMARY_PATH}. "
            "Run python -m src.analysis.generate_insights first."
        )

    df = pd.read_csv(LOOKER_EXPORT_PATH)
    df = prepare_dataframe_for_sheets(df)
    summary = pd.read_csv(EXECUTIVE_SUMMARY_PATH)

    credentials = load_credentials()

    service = build("sheets", "v4", credentials=credentials)
    sheet = service.spreadsheets()

    try:
        ensure_sheet_exists(service, SUMMARY_SHEET_NAME)
        replace_dashboard_values(sheet, df)
        summary_action = upsert_daily_summary(sheet, summary)
    except HttpError as error:
        if error.resp.status == 403:
            raise permission_error(credentials) from error
        raise

    print(f"Uploaded {len(df)} rows to Google Sheets")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"Sheet name: {SHEET_NAME}")
    print(
        f"Daily executive summary {summary_action} in sheet: "
        f"{SUMMARY_SHEET_NAME}"
    )


if __name__ == "__main__":
    upload_to_google_sheets()
