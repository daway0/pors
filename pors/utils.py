import json
import re

import jdatetime
from persiantools.jdatetime import JalaliDate, timedelta

from .config import ORDER_REGISTRATION_CLOSED_IN


def first_and_last_day_date(
    month: int, year: int
) -> tuple[jdatetime.date, jdatetime.date]:
    """
    این تابع یک ابکجت دیت جلالی از روز اول و روز اخر تاریخ وارد شده
    بر می‌گرداند.

    ورودی ها:
        year: سال
        month: ماه
    بازگشتی ها:
        jalali_first_day_date: ابجکت روز اول
        jalali_last_day_date: ابجکت روز اخر

    """

    # Todo convert year and month to gro
    last_day_of_month = JalaliDate.days_in_month(month, year)
    first_day_date = (
        jdatetime.date(year, month, 1).strftime("%Y-%m-%d").replace("-", "/")
    )
    last_day_date = (
        jdatetime.date(year, month, last_day_of_month)
        .strftime("%Y-%m-%d")
        .replace("-", "/")
    )
    return str(first_day_date), str(last_day_date)


def get_weekend_holidays(year: int, month: int) -> list[jdatetime.date]:
    """
    این تابع مسئولیت حساب کردن تعطیلات اخر هفته را دارد.

    ورودی ها:
        year: سال
        month: ماه
    بازگشتی ها:
        holidays: لیستی از تعطیلات اخر خفته
    """

    # Todo get last day of month in jalali date
    last_day_of_month = JalaliDate.days_in_month(month, year)
    holidays = []
    for daynum in range(1, last_day_of_month + 1):
        daynum_date = jdatetime.date(year, month, daynum)
        if daynum_date.weekday() in (6, 5):
            holidays.append(daynum_date.strftime("%Y/%m/%d").replace("-", "/"))
    return holidays


def get_current_date() -> tuple[int, int, int]:
    now = jdatetime.datetime.now()
    return now.year, now.month, now.day


def get_first_orderable_date() -> tuple[int, int, int]:
    now = jdatetime.datetime.now()

    if now.hour > ORDER_REGISTRATION_CLOSED_IN:
        now += timedelta(days=2)
    else:
        now += timedelta(days=1)
    return now.year, now.month, now.day

def replace_hyphens_from_date(*dates: str):
    if len(dates) == 1:
        return dates[0].replace("-", "/")
    new_date = []
    for date in dates:
        new_date.append(date.replace("-", "/"))
    return new_date


def split_dates(dates, mode: str):
    new_dates = []

    if mode == "day":
        if not isinstance(dates, list):
            return int(dates.split("/")[2])
        for date in dates:
            new_dates.append(int(date.split("/")[2]))
        return new_dates
    elif mode == "month":
        if not isinstance(dates, list):
            return int(dates.split("/")[1])
        for date in dates:
            new_dates.append(int(date.split("/")[1]))
        return new_dates
    elif mode == "year":
        if not isinstance(dates, list):
            return int(dates.split("/")[0])
        for date in dates:
            new_dates.append(int(date.split("/")[0]))
        return new_dates


def split_json_dates(dates: str):
    dates = json.loads(dates)
    for obj in dates:
        obj["day"] = int(obj["day"].split("/")[2])
    return dates


def validate_date(date: str):
    pattern = r"^\d{4}\/\d{2}\/\d{2}$"
    if not isinstance(date, str):
        return None
    if "-" in date:
        date = date.replace("-", "/")
    if re.match(pattern, date):
        return date
    else:
        return None
