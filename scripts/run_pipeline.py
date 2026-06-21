from src.ingestion.fetch_market_data import main as fetch_market_data
from src.analysis.technical_indicators import main as calculate_indicators
from src.analysis.generate_alerts import main as generate_alerts
from src.analysis.generate_insights import main as generate_insights
from src.export.google_sheets_export import upload_to_google_sheets


def main():
    print("Step 1: Fetching market data...")
    fetch_market_data()

    print("Step 2: Calculating technical indicators...")
    calculate_indicators()

    print("Step 3: Generating alerts...")
    generate_alerts()

    print("Step 4: Generating insights...")
    generate_insights()

    print("Step 5: Uploading to Google Sheets...")
    upload_to_google_sheets()

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
