import jdatetime
from persiantools.jdatetime import JalaliDate

from .models import DailyMenuItem, Holiday
from .serializers import (
    DaysWithMenuSerializer,
    GeneralCalendarSerializer,
    HolidaySerializer,
)
from .utils import first_and_last_day_date, get_weekend_holidays, split_dates


def get_general_calendar(year: int, month: int):
    last_day = JalaliDate.days_in_month(month, year)
    first_day_week_num = jdatetime.datetime(year, month, 1).weekday()
    first_day_date, last_day_date = first_and_last_day_date(month, year)
    holidays = Holiday.objects.filter(
        HolidayDate__range=(first_day_date, last_day_date)
    )
    weekend_holidays = get_weekend_holidays(year, month)
    holidays_serializer = HolidaySerializer(holidays).data
    holidays_serializer = holidays_serializer["holidays"]
    holidays_serializer += weekend_holidays
    holidays_serializer.sort()
    splited_holidays = split_dates(holidays_serializer, mode="day")
    days_with_menu = (
        DailyMenuItem.objects.filter(
            AvailableDate__range=(first_day_date, last_day_date)
        )
        .values("AvailableDate")
        .distinct()
    )
    days_with_menu_serializer = DaysWithMenuSerializer(days_with_menu).data
    splited_days_with_menu = split_dates(
        days_with_menu_serializer["daysWithMenu"], "day"
    )
    general_calendar_serializer = GeneralCalendarSerializer(
        data={
            "year": year,
            "month": month,
            "firstDayOfWeek": first_day_week_num + 1,
            "lastDayOfMonth": last_day,
            "holidays": splited_holidays,
            "daysWithMenu": splited_days_with_menu,
        }
    ).initial_data
    return general_calendar_serializer
