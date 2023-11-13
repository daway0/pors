import datetime
from calendar import monthrange


def first_and_last_day_date(
    month: int, year: int
) -> tuple[datetime.date, datetime.date]:
    """
    این تابع یک ابکجت از روز اول و روز اخر تاریخ وارد شده
    بر می‌گرداند.

    ورودی ها:
        year: سال
        month: ماه
    بازگشتی ها:
        first_day_date: ابجکت روز اول
        last_day_date: ابجکت روز اخر

    """
    _, last_day = monthrange(year, month)
    first_day_date = datetime.date(year, month, 1)
    last_day_date = datetime.date(year, month, last_day)
    return first_day_date, last_day_date


def get_weekend_holidays(year: int, month: int) -> list[datetime.date]:
    """
    این تابع مسئولیت حساب کردن تعطیلات اخر هفته را دارد.

    ورودی ها:
        year: سال
        month: ماه
    بازگشتی ها:
        holidays: لیستی از تعطیلات اخر خفته
    """
    _, last_day_of_month = monthrange(year, month)
    holidays = []
    for daynum in range(1, last_day_of_month + 1):
        daynum_date = datetime.date(year, month, daynum)
        if daynum_date.weekday() in (3, 4):
            holidays.append(daynum_date)
    return holidays
