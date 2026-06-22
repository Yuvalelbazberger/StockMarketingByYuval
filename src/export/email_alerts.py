import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from html import escape
from zoneinfo import ZoneInfo

import pandas as pd

from src.analysis.generate_alerts import STOCK_ALERTS_PATH
from src.analysis.generate_executive_summary import EXECUTIVE_SUMMARY_PATH


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
DASHBOARD_URL = os.getenv(
    "LOOKER_DASHBOARD_URL",
    "https://datastudio.google.com/reporting/b3cd37f3-cda8-4080-8140-994c881a8d9e",
)
NEW_YORK = ZoneInfo("America/New_York")
REPORT_WINDOW_LABELS = {
    "pre_market": "Pre-Market Brief",
    "market_open": "Market Open Update",
    "after_close": "Closing Bell Summary",
    "on_demand": "On-Demand Market Brief",
}


def _summary_value(summary, name, default):
    if summary is None or summary.empty or name not in summary.columns:
        return default
    value = summary.iloc[0][name]
    return default if pd.isna(value) else value


def _report_context():
    window = os.getenv("REPORT_WINDOW", "on_demand")
    label = REPORT_WINDOW_LABELS.get(window, "Market Update")
    generated = datetime.now(NEW_YORK).strftime("%Y-%m-%d %H:%M ET")
    return window, label, generated


def _plain_text_body(alerts, summary, alert_date, report_label, generated_at):
    market_regime = _summary_value(summary, "market_regime", "Market update")
    lines = [
        f"MARKETPULSE {report_label.upper()}",
        f"Market data through: {alert_date}",
        f"Report generated: {generated_at}",
        "",
        "EXECUTIVE SNAPSHOT",
        f"Market regime: {market_regime}",
        f"Market breadth: {_summary_value(summary, 'market_breadth_pct', 'N/A')}%",
        f"Watchlist stocks: {_summary_value(summary, 'watchlist_count', 'N/A')}",
        f"High-risk stocks: {_summary_value(summary, 'high_risk_count', 'N/A')}",
        "",
        str(_summary_value(summary, "executive_summary", "")),
        "",
        "BUSINESS IMPLICATIONS",
        str(_summary_value(summary, "business_implications", "Review the latest signals.")),
        "",
        f"Top opportunities: {_summary_value(summary, 'top_opportunities', 'N/A')}",
        f"Key risks: {_summary_value(summary, 'key_risks', 'N/A')}",
        "",
        f"ACTIVE ALERTS ({len(alerts)})",
    ]
    if alerts.empty:
        lines.append("- No active alerts in this update.")
    else:
        for row in alerts.itertuples(index=False):
            ticker_label = getattr(row, "ticker_display", row.ticker)
            lines.append(
                f"- {ticker_label}: {row.alert_type} | close {row.close:.2f} | "
                f"RSI {row.rsi_14:.1f} | daily change {row.daily_change_pct:+.2f}%"
            )
    lines.extend(
        [
            "",
            f"Dashboard: {DASHBOARD_URL}",
            "",
            "This automated analysis is for informational purposes only and is not financial advice.",
        ]
    )
    return "\n".join(lines)


def _html_body(alerts, summary, alert_date, report_label, generated_at):
    market_regime = escape(str(_summary_value(summary, "market_regime", "Market Update")))
    breadth = escape(str(_summary_value(summary, "market_breadth_pct", "N/A")))
    watchlist_count = escape(str(_summary_value(summary, "watchlist_count", "N/A")))
    high_risk_count = escape(str(_summary_value(summary, "high_risk_count", "N/A")))
    executive_summary = escape(str(_summary_value(summary, "executive_summary", "")))
    implications = escape(
        str(_summary_value(summary, "business_implications", "Review the latest signals."))
    )
    recommended_actions = escape(
        str(_summary_value(summary, "recommended_actions", "Monitor the next market update."))
    )
    top_opportunities = escape(
        str(_summary_value(summary, "top_opportunities", "No qualifying stocks"))
    )
    key_risks = escape(str(_summary_value(summary, "key_risks", "No qualifying stocks")))

    alert_rows = []
    for index, row in enumerate(alerts.itertuples(index=False)):
        ticker_label = getattr(row, "ticker_display", row.ticker)
        background = "#ffffff" if index % 2 == 0 else "#f8fafc"
        move_color = "#047857" if row.daily_change_pct >= 0 else "#b91c1c"
        alert_rows.append(
            f"""
            <tr style="background:{background};">
              <td style="padding:12px;border-bottom:1px solid #e2e8f0;font-weight:700;">{escape(str(ticker_label))}</td>
              <td style="padding:12px;border-bottom:1px solid #e2e8f0;">{escape(str(row.alert_type).replace('_', ' ').title())}</td>
              <td style="padding:12px;border-bottom:1px solid #e2e8f0;text-align:right;">{row.close:,.2f}</td>
              <td style="padding:12px;border-bottom:1px solid #e2e8f0;text-align:right;color:{move_color};font-weight:700;">{row.daily_change_pct:+.2f}%</td>
              <td style="padding:12px;border-bottom:1px solid #e2e8f0;text-align:right;">{row.rsi_14:.1f}</td>
            </tr>
            """
        )

    if not alert_rows:
        alert_rows.append(
            "<tr><td colspan=\"5\" style=\"padding:18px;text-align:center;"
            "color:#64748b;\">No active alerts in this update.</td></tr>"
        )

    return f"""<!doctype html>
<html>
  <body style="margin:0;background:#f1f5f9;font-family:Arial,sans-serif;color:#0f172a;">
    <div style="max-width:760px;margin:0 auto;padding:24px 12px;">
      <div style="background:#0f172a;color:#ffffff;padding:28px 32px;border-radius:14px 14px 0 0;">
        <div style="font-size:12px;letter-spacing:1.8px;color:#7dd3fc;font-weight:700;">MARKETPULSE</div>
        <h1 style="margin:8px 0 4px;font-size:26px;">{escape(report_label)}</h1>
        <div style="color:#cbd5e1;font-size:14px;">Market data through {escape(alert_date)} &nbsp;|&nbsp; Generated {escape(generated_at)}</div>
      </div>

      <div style="background:#ffffff;padding:28px 32px;">
        <h2 style="margin:0 0 16px;font-size:18px;">Executive Snapshot</h2>
        <table role="presentation" style="width:100%;border-collapse:separate;border-spacing:8px;">
          <tr>
            <td style="background:#eff6ff;padding:16px;border-radius:10px;width:25%;"><div style="font-size:11px;color:#64748b;">MARKET REGIME</div><div style="font-size:18px;font-weight:700;margin-top:5px;">{market_regime}</div></td>
            <td style="background:#ecfdf5;padding:16px;border-radius:10px;width:25%;"><div style="font-size:11px;color:#64748b;">BREADTH</div><div style="font-size:18px;font-weight:700;margin-top:5px;">{breadth}%</div></td>
            <td style="background:#fffbeb;padding:16px;border-radius:10px;width:25%;"><div style="font-size:11px;color:#64748b;">WATCHLIST</div><div style="font-size:18px;font-weight:700;margin-top:5px;">{watchlist_count}</div></td>
            <td style="background:#fef2f2;padding:16px;border-radius:10px;width:25%;"><div style="font-size:11px;color:#64748b;">HIGH RISK</div><div style="font-size:18px;font-weight:700;margin-top:5px;">{high_risk_count}</div></td>
          </tr>
        </table>

        <p style="font-size:15px;line-height:1.6;margin:20px 0;">{executive_summary}</p>

        <div style="border-left:4px solid #0ea5e9;background:#f0f9ff;padding:16px 18px;margin:18px 0;">
          <div style="font-size:12px;font-weight:700;color:#0369a1;margin-bottom:6px;">BUSINESS IMPLICATIONS</div>
          <div style="font-size:14px;line-height:1.55;">{implications}</div>
        </div>

        <table role="presentation" style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr><td style="padding:12px;background:#f8fafc;font-weight:700;width:180px;">Top Opportunities</td><td style="padding:12px;background:#f8fafc;">{top_opportunities}</td></tr>
          <tr><td style="padding:12px;font-weight:700;">Key Risks</td><td style="padding:12px;">{key_risks}</td></tr>
          <tr><td style="padding:12px;background:#f8fafc;font-weight:700;">Recommended Review</td><td style="padding:12px;background:#f8fafc;">{recommended_actions}</td></tr>
        </table>

        <h2 style="margin:28px 0 12px;font-size:18px;">Active Alerts <span style="color:#64748b;font-weight:400;">({len(alerts)})</span></h2>
        <div style="overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead><tr style="background:#e2e8f0;"><th style="padding:11px;text-align:left;">Ticker</th><th style="padding:11px;text-align:left;">Trigger</th><th style="padding:11px;text-align:right;">Close</th><th style="padding:11px;text-align:right;">Daily Move</th><th style="padding:11px;text-align:right;">RSI</th></tr></thead>
            <tbody>{''.join(alert_rows)}</tbody>
          </table>
        </div>

        <div style="text-align:center;margin:28px 0 8px;">
          <a href="{escape(DASHBOARD_URL)}" style="display:inline-block;background:#0284c7;color:#ffffff;text-decoration:none;padding:13px 24px;border-radius:8px;font-weight:700;">Open Market Dashboard</a>
        </div>
      </div>

      <div style="background:#e2e8f0;color:#64748b;padding:16px 24px;border-radius:0 0 14px 14px;text-align:center;font-size:11px;line-height:1.5;">
        Automated analytical report for informational purposes only. This is not financial advice.
      </div>
    </div>
  </body>
</html>"""


def build_alert_email(alerts, sender, recipients, summary=None):
    if alerts.empty:
        alert_date = str(_summary_value(summary, "analysis_date", "No current data"))
    else:
        alert_date = pd.to_datetime(alerts["datetime"]).max().strftime("%Y-%m-%d")
    market_regime = _summary_value(summary, "market_regime", "Market Update")
    _, report_label, generated_at = _report_context()

    message = EmailMessage()
    message["Subject"] = (
        f"MarketPulse {report_label} | {market_regime} | "
        f"Data {alert_date}"
    )
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(
        _plain_text_body(
            alerts,
            summary,
            alert_date,
            report_label,
            generated_at,
        )
    )
    message.add_alternative(
        _html_body(
            alerts,
            summary,
            alert_date,
            report_label,
            generated_at,
        ),
        subtype="html",
    )
    return message


def send_alert_email():
    if not STOCK_ALERTS_PATH.exists():
        print(f"Email alerts skipped: missing {STOCK_ALERTS_PATH}")
        return False

    alerts = pd.read_csv(STOCK_ALERTS_PATH)
    summary = (
        pd.read_csv(EXECUTIVE_SUMMARY_PATH)
        if EXECUTIVE_SUMMARY_PATH.exists()
        else None
    )

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
    message = build_alert_email(alerts, username, recipients, summary=summary)

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(username, password)
        smtp.send_message(message)

    print(f"Sent market brief with {len(alerts)} alerts to {', '.join(recipients)}")
    return True


if __name__ == "__main__":
    send_alert_email()
