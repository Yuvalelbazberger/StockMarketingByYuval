import os
import smtplib
from email.message import EmailMessage

import pandas as pd

from src.analysis.generate_alerts import STOCK_ALERTS_PATH


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))


def build_alert_email(alerts, sender, recipients):
    alert_date = pd.to_datetime(alerts["datetime"]).max().strftime("%Y-%m-%d")
    subject = f"Market alerts: {len(alerts)} signals for {alert_date}"

    lines = [
        f"{len(alerts)} market alerts were detected for {alert_date}:",
        "",
    ]
    for row in alerts.itertuples(index=False):
        lines.append(
            f"{row.ticker}: {row.alert_type} | close {row.close:.2f} | "
            f"RSI {row.rsi_14:.1f} | daily change {row.daily_change_pct:+.2f}%"
        )

    lines.extend(
        [
            "",
            "This automated message is for informational purposes only and is not financial advice.",
        ]
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content("\n".join(lines))
    return message


def send_alert_email():
    if not STOCK_ALERTS_PATH.exists():
        print(f"Email alerts skipped: missing {STOCK_ALERTS_PATH}")
        return False

    alerts = pd.read_csv(STOCK_ALERTS_PATH)
    if alerts.empty:
        print("Email alerts skipped: no active alerts")
        return False

    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    recipient_value = os.getenv("ALERT_EMAIL_TO") or username

    if not username or not password or not recipient_value:
        print(
            "Email alerts skipped: configure SMTP_USERNAME, SMTP_PASSWORD, "
            "and ALERT_EMAIL_TO in GitHub Actions"
        )
        return False

    recipients = [
        address.strip()
        for address in recipient_value.split(",")
        if address.strip()
    ]
    message = build_alert_email(alerts, username, recipients)

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(username, password)
        smtp.send_message(message)

    print(f"Sent {len(alerts)} alerts to {', '.join(recipients)}")
    return True


if __name__ == "__main__":
    send_alert_email()
