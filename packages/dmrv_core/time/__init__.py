"""Time calculations, fractional years, and calendar vintage allocation."""
from __future__ import annotations

import datetime
from typing import Dict, Union


def to_date(d: Union[str, datetime.date, datetime.datetime]) -> datetime.date:
    if isinstance(d, datetime.datetime):
        return d.date()
    if isinstance(d, datetime.date):
        return d
    return datetime.date.fromisoformat(str(d))


def fractional_years(
    start_date: Union[str, datetime.date],
    end_date: Union[str, datetime.date],
    method: str = "days_365_25",
) -> float:
    """Calculate elapsed time interval T in years.
    Default method: days / 365.25.
    month_based: months/12 (approximate).
    """
    d1 = to_date(start_date)
    d2 = to_date(end_date)
    if d2 < d1:
        raise ValueError(f"End date {d2} cannot be before start date {d1}")

    days = (d2 - d1).days
    if method == "days_365_25":
        return days / 365.25
    elif method == "month_based":
        total_months = (d2.year - d1.year) * 12 + (d2.month - d1.month) + (d2.day - d1.day) / 30.4375
        return total_months / 12.0
    else:
        raise ValueError(f"Unknown fractional year method: {method}")


def allocate_to_calendar_vintages(
    start_date: Union[str, datetime.date],
    end_date: Union[str, datetime.date],
    total_amount: float,
) -> Dict[int, float]:
    """Allocate an emission or removal amount pro-rata across calendar year vintages by days (inclusive)."""
    d1 = to_date(start_date)
    d2 = to_date(end_date)
    if d2 < d1:
        raise ValueError(f"End date {d2} cannot be before start date {d1}")

    # Inclusive days: e.g. 2025-07-01 to 2026-06-30
    total_days = (d2 - d1).days + 1
    if total_days <= 0:
        return {d1.year: total_amount}

    allocation: Dict[int, float] = {}
    current_year = d1.year
    while current_year <= d2.year:
        year_start = max(d1, datetime.date(current_year, 1, 1))
        year_end = min(d2, datetime.date(current_year, 12, 31))
        days_in_year = (year_end - year_start).days + 1

        fraction = days_in_year / total_days
        allocation[current_year] = total_amount * fraction
        current_year += 1

    return allocation


__all__ = ["fractional_years", "allocate_to_calendar_vintages", "to_date"]
