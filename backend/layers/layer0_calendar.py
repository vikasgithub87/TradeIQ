"""
layer0_calendar.py — NSE trading calendar, RBI dates, Budget days
Covers 2025 and 2026. Update annually.
"""
import datetime
from typing import Optional

# ── NSE Trading Holidays 2025 ─────────────────────────────────────────────────
NSE_HOLIDAYS_2025 = {
    "2025-01-26": "Republic Day",
    "2025-02-26": "Mahashivratri",
    "2025-03-14": "Holi",
    "2025-03-31": "Id-Ul-Fitr (Ramadan Eid)",
    "2025-04-10": "Shri Ram Navami",
    "2025-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2025-04-18": "Good Friday",
    "2025-05-01": "Maharashtra Day",
    "2025-08-15": "Independence Day",
    "2025-08-27": "Ganesh Chaturthi",
    "2025-10-02": "Mahatma Gandhi Jayanti",
    "2025-10-20": "Diwali Laxmi Pujan (Muhurat Trading)",
    "2025-10-21": "Diwali Balipratipada",
    "2025-11-05": "Prakash Gurpurb Sri Guru Nanak Dev",
    "2025-12-25": "Christmas",
}

# ── NSE Trading Holidays 2026 ─────────────────────────────────────────────────
NSE_HOLIDAYS_2026 = {
    "2026-01-26": "Republic Day",
    "2026-03-03": "Mahashivratri",
    "2026-03-20": "Holi",
    "2026-04-02": "Shri Ram Navami",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-08-15": "Independence Day",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-11-14": "Diwali Laxmi Pujan",
    "2026-12-25": "Christmas",
}

# ── RBI Monetary Policy Committee Meeting Dates ───────────────────────────────
# These are announcement days — highest rate-decision volatility
RBI_POLICY_DATES_2025 = [
    "2025-02-07",  # Feb MPC announcement
    "2025-04-09",  # Apr MPC announcement
    "2025-06-06",  # Jun MPC announcement
    "2025-08-08",  # Aug MPC announcement
    "2025-10-08",  # Oct MPC announcement
    "2025-12-05",  # Dec MPC announcement
]

RBI_POLICY_DATES_2026 = [
    "2026-02-06",  # Feb MPC announcement
    "2026-04-09",  # Apr MPC announcement
    "2026-06-05",  # Jun MPC announcement
    "2026-08-07",  # Aug MPC announcement
    "2026-10-09",  # Oct MPC announcement
    "2026-12-04",  # Dec MPC announcement
]

# ── Union Budget Dates ────────────────────────────────────────────────────────
# Feb 1 is standard Union Budget day — most volatile day of year
BUDGET_DATES = [
    "2025-02-01",  # Union Budget 2025-26
    "2026-02-01",  # Union Budget 2026-27 (expected)
]

# ── F&O Expiry Logic ──────────────────────────────────────────────────────────
def get_monthly_expiry(year: int, month: int) -> datetime.date:
    """
    Return the last Thursday of the given month.
    NSE monthly F&O contracts expire on the last Thursday.
    If last Thursday is a holiday, expiry moves to previous Wednesday.
    """
    all_holidays = {**NSE_HOLIDAYS_2025, **NSE_HOLIDAYS_2026}
    # Find last day of month
    if month == 12:
        last_day = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    # Walk back to find last Thursday (weekday 3)
    day = last_day
    while day.weekday() != 3:
        day -= datetime.timedelta(days=1)
    # If that Thursday is a holiday, move to Wednesday
    while day.strftime("%Y-%m-%d") in all_holidays:
        day -= datetime.timedelta(days=1)
    return day

def get_weekly_expiry(date: datetime.date) -> datetime.date:
    """
    Return the Thursday of the current week.
    Weekly Bank Nifty and Nifty options expire every Thursday.
    """
    days_ahead = 3 - date.weekday()  # Thursday = weekday 3
    if days_ahead < 0:
        days_ahead += 7
    return date + datetime.timedelta(days=days_ahead)

def check_calendar(date_str: str) -> dict:
    """
    Check all calendar flags for a given date string (YYYY-MM-DD).
    Returns a dict with all calendar-related flags.
    """
    all_holidays = {**NSE_HOLIDAYS_2025, **NSE_HOLIDAYS_2026}
    all_rbi      = RBI_POLICY_DATES_2025 + RBI_POLICY_DATES_2026
    all_budgets  = BUDGET_DATES

    try:
        date = datetime.date.fromisoformat(date_str)
    except ValueError:
        date = datetime.date.today()

    # Basic flags
    is_weekend     = date.weekday() >= 5
    is_nse_holiday = date_str in all_holidays
    market_open    = not is_weekend and not is_nse_holiday
    holiday_name   = all_holidays.get(date_str, "")

    # RBI and budget
    is_rbi_day    = date_str in all_rbi
    is_budget_day = date_str in all_budgets

    # F&O expiry
    monthly_expiry = get_monthly_expiry(date.year, date.month)
    weekly_expiry  = get_weekly_expiry(date)
    is_monthly_expiry = date == monthly_expiry
    is_weekly_expiry  = date == weekly_expiry
    is_expiry_day     = is_monthly_expiry or is_weekly_expiry

    # Days to next expiry
    days_to_expiry = (monthly_expiry - date).days
    if days_to_expiry < 0:
        # Already past this month's expiry — get next month's
        if date.month == 12:
            next_expiry = get_monthly_expiry(date.year + 1, 1)
        else:
            next_expiry = get_monthly_expiry(date.year, date.month + 1)
        days_to_expiry = (next_expiry - date).days

    return {
        "date":               date_str,
        "market_open":        market_open,
        "is_weekend":         is_weekend,
        "is_nse_holiday":     is_nse_holiday,
        "holiday_name":       holiday_name,
        "is_rbi_day":         is_rbi_day,
        "is_budget_day":      is_budget_day,
        "is_expiry_day":      is_expiry_day,
        "is_monthly_expiry":  is_monthly_expiry,
        "is_weekly_expiry":   is_weekly_expiry,
        "days_to_expiry":     days_to_expiry,
        "monthly_expiry_date": monthly_expiry.strftime("%Y-%m-%d"),
    }
