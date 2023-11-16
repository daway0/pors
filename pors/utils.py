import datetime
from calendar import monthrange

from jdatetime import GregorianToJalali
from jdatetime import datetime as jdatetime


def first_and_last_day_date(
    month: int, year: int
) -> tuple[datetime.date, datetime.date]:
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

    #Todo convert year and month to gro
    _, last_day = monthrange(year, month)
    first_day_date = datetime.date(year, month, 1)
    last_day_date = datetime.date(year, month, last_day)
    jalali_first_day_date = (
        jdatetime.fromgregorian(
            year=first_day_date.year,
            month=first_day_date.month,
            day=first_day_date.day,
        )
        .strftime("%Y-%m-%d")
        .replace("-", "/")
    )
    jalali_last_day_date = (
        jdatetime.fromgregorian(
            year=last_day_date.year,
            month=last_day_date.month,
            day=last_day_date.day,
        )
        .strftime("%Y-%m-%d")
        .replace("-", "/")
    )
    return str(jalali_first_day_date), str(jalali_last_day_date)


def get_weekend_holidays(year: int, month: int) -> list[datetime.date]:
    """
    این تابع مسئولیت حساب کردن تعطیلات اخر هفته را دارد.

    ورودی ها:
        year: سال
        month: ماه
    بازگشتی ها:
        holidays: لیستی از تعطیلات اخر خفته
    """

    #Todo get last day of month in jalali date
    _, last_day_of_month = monthrange(year, month)
    holidays = []
    for daynum in range(1, last_day_of_month + 1):
        daynum_date = datetime.date(year, month, daynum)
        if daynum_date.weekday() in (3, 4):
            holidays.append(daynum_date)
    return holidays


def get_current_date() -> int:
    now = jdatetime.now()
    return now.year, now.month, now.day
