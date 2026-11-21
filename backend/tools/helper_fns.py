from __future__ import annotations
from datetime import date, datetime, timedelta
from pathlib import Path
from sqlalchemy import select, func, desc
from backend.database import AsyncSessionLocal
from backend.models import Customer, Product, Order, OrderItem

REVENUE_STATUSES = ("completed", "returned", "cancelled")

def revenue_filter():
    return func.lower(Order.status).in_(REVENUE_STATUSES)

def parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    supported_date_formats = [
        "%Y-%m-%d",  # 2026-02-01
        "%d-%m-%Y",  # 01-02-2026
        "%d/%m/%Y",  # 01/02/2026
        "%Y/%m/%d",  # 2026/02/01
    ]

    for date_format in supported_date_formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    raise ValueError(
        f"Invalid date format: {value}. "
        "Use DD-MM-YYYY or YYYY-MM-DD."
    )

# for date range
def date_range(period, start, end):

    # Convert the provided dates into date objects.
    start = parse_date(start)
    end = parse_date(end)

    # Get today's date.
    today = date.today()

    # CUSTOM DATE RANGE
    if start is not None or end is not None:

        if start is None or end is None:
            raise ValueError("Both start and end dates are required.")

        if start > end:
            raise ValueError("Start date cannot be after end date.")

        return start, end, "custom"

    period = (period or "last_30_days").lower().strip()

    if period == "today":
        return today, today, period

    elif period.startswith("last_") and period.endswith("_days"):

        try:
            number_of_days = int(period.split("_")[1])
        except ValueError:
            raise ValueError(f"Invalid period: {period}")

        if number_of_days <= 0:
            raise ValueError("Number of days must be greater than zero.")

        start_date = today - timedelta(days=number_of_days - 1)

        return start_date, today, period

    elif period == "this_month":
        first_day = today.replace(day=1)
        return first_day, today, period

    elif period == "last_month":
        last_day_previous_month = today.replace(day=1) - timedelta(days=1)
        first_day_previous_month = last_day_previous_month.replace(day=1)

        return first_day_previous_month, last_day_previous_month, period

    elif period == "this_year":
        return date(today.year, 1, 1), today, period

    elif period == "last_12_months":
        month_index = today.year * 12 + today.month - 1 - 11
        year, month_zero = divmod(month_index, 12)
        first_day = date(year, month_zero + 1, 1)

        return first_day, today, period

    elif period == "all_time":
        return None, None, period

    else:
        raise ValueError(f"Unsupported period: {period}")

def date_conditions(start, end):

    conditions = []

    if start is not None:
        conditions.append(Order.order_date >= start)
    if end is not None:
        conditions.append(Order.order_date <= end)

    return conditions

def format_inr(number: float) -> str:
    """
    Formats a number into comma system (1750000 -> 17,50,000)
    """
    n_int = int(round(number))
    s = str(n_int)
    if len(s) <= 3:
        return s

    last_three = s[-3:]
    remaining = s[:-3]
    parts = []
    while len(remaining) > 2:
        parts.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        parts.insert(0, remaining)
    return ",".join(parts) + "," + last_three

