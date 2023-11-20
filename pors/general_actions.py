import json

import jdatetime
from django.db.models import Count
from persiantools.jdatetime import JalaliDate

from .models import Holiday, ItemsOrdersPerDay
from .serializers import (
    DayWithMenuSerializer,
    GeneralCalendarSerializer,
    HolidaySerializer,
)
from .utils import (
    first_and_last_day_date,
    get_weekend_holidays,
    split_dates,
    split_json_dates,
)


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
    days_with_menu = ItemsOrdersPerDay.objects.filter(
        Date__range=(first_day_date, last_day_date)
    )
    days_with_menu_serializer = DayWithMenuSerializer(
        days_with_menu, many=True
    ).data
    splited_days_with_menu = split_json_dates(
        json.dumps(days_with_menu_serializer)
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
