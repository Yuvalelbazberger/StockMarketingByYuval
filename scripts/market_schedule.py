import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas_market_calendars as mcal


NEW_YORK = ZoneInfo("America/New_York")
NYSE = mcal.get_calendar("NYSE")


def _scheduled_utc(now_utc, cron_expression):
    fields = cron_expression.split()
    if len(fields) < 2:
        raise ValueError(f"Invalid cron expression: {cron_expression}")
    minute, hour = int(fields[0]), int(fields[1])
    return now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)


def determine_market_window(event_name, cron_expression="", now_utc=None):
    if event_name != "schedule":
        return True, "on_demand"

    now_utc = now_utc or datetime.now(timezone.utc)
    market_date = now_utc.astimezone(NEW_YORK).date()
    schedule = NYSE.schedule(start_date=market_date, end_date=market_date)
    if schedule.empty:
        return False, "market_closed"

    market_open = schedule.iloc[0]["market_open"].to_pydatetime()
    market_close = schedule.iloc[0]["market_close"].to_pydatetime()
    scheduled = _scheduled_utc(now_utc, cron_expression)
    windows = {
        "pre_market": market_open - timedelta(minutes=30),
        "market_open": market_open + timedelta(minutes=5),
        "after_close": market_close + timedelta(minutes=15),
    }

    for name, target in windows.items():
        if scheduled.hour == target.hour and scheduled.minute == target.minute:
            return True, name
    return False, "dst_candidate_skipped"


def main():
    should_run, report_window = determine_market_window(
        event_name=os.getenv("EVENT_NAME", "workflow_dispatch"),
        cron_expression=os.getenv("SCHEDULE_EXPRESSION", ""),
    )
    print(f"should_run={str(should_run).lower()}")
    print(f"report_window={report_window}")


if __name__ == "__main__":
    main()
