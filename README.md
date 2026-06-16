# Stock Market Intelligence Platform

A Python-based market intelligence project that collects stock market data, calculates technical indicators, generates stock insights, and exports the final dataset to Google Sheets for visualization in Looker Studio.

## Project Overview

This project analyzes selected stocks using market data from Yahoo Finance through `yfinance`.

The pipeline includes:

1. Fetch stock market data
2. Save raw price data
3. Calculate technical indicators
4. Generate stock insights
5. Export results to Google Sheets
6. Visualize the data in Looker Studio

## Tech Stack

- Python
- pandas
- yfinance
- Google Sheets API
- Looker Studio
- Git / GitHub

## Project Structure

```text
market-intelligence-platform/
├── data/
│   ├── raw/
│   └── marts/
├── secrets/
├── scripts/
├── src/
│   ├── ingestion/
│   ├── analysis/
│   ├── export/
│   └── utils/
├── requirements.txt
├── .gitignore
└── README.md

Main Features
Downloads stock market data from Yahoo Finance
Supports multiple stock tickers
Calculates:Moving averages
Returns
Volatility
RSI
Trend signals

Generates English insights for each stock
Exports dashboard-ready data to Google Sheets
Connects with Looker Studio for visualization
How To Run
Activate the virtual environment:
source .venv/bin/activate
Run the pipeline:
python -m src.ingestion.fetch_market_data
python -m src.analysis.technical_indicators
python -m src.analysis.generate_insights
python -m src.export.google_sheets_export
Output Files
Raw market data:
data/raw/market_prices.parquet
Technical indicators:
data/marts/stock_features.parquet
Looker Studio export:
data/marts/tableau_stock_dashboard.csv
Looker Studio
The final dataset is uploaded to Google Sheets and used as the data source for a Looker Studio dashboard.
Recommended dashboard components:
Stock returns by ticker
RSI by ticker
Risk level filter
Trend and signal table
Stock insight text table
Security Notes
The secrets/ folder contains private Google API credentials and should never be uploaded to GitHub.
Make sure .gitignore includes:
secrets/
.venv/
__pycache__/
*.pyc
data/raw/
data/marts/
.DS_Store
Disclaimer
This project is for educational and portfolio purposes only.
It is not financial advice and should not be used for real trading decisions.