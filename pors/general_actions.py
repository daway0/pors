import datetime
from calendar import monthrange

from .models import DailyMenuItem, Holiday, Order
from .serializers import (
    DaysWithMenuSerializer,
    GeneralCalendarSerializer,
    HolidaySerializer,
)
from .utils import first_and_last_day_date, get_weekend_holidays


def get_general_calendar(year: int, month: int, personnel: str):
    _, last_day = monthrange(year, month)
    first_day_week_num = datetime.datetime(year, month, 1).weekday()
    first_day_date, last_day_date = first_and_last_day_date(month, year)
    holidays = Holiday.objects.filter(
        HolidayDate__range=(first_day_date, last_day_date)
    )
    weekend_holidays = get_weekend_holidays(year, month)
    holidays_serializer = HolidaySerializer(holidays, many=True)
    holidays_serializer = holidays_serializer.data
    holidays_serializer += weekend_holidays
    holidays_serializer.sort()
    days_with_menu = (
        DailyMenuItem.objects.filter(
            AvailableDate__range=(first_day_date, last_day_date)
        )
        .values("AvailableDate")
        .distinct()
    )
    days_with_menu_serializer = DaysWithMenuSerializer(days_with_menu).data
    ordered_days = Order.objects.filter(
        DeliveryDate__range=(first_day_date, last_day_date),
        Personnel=personnel,
    ).values("DeliveryDate")
    days_list = [date["DeliveryDate"] for date in ordered_days]
    general_calendar_serializer = GeneralCalendarSerializer(
        data={
            "year": year,
            "month": month,
            "firstDayOfWeek": first_day_week_num,
            "lastDayOfWeek": last_day,
            "holidays": holidays_serializer,
            "daysWithMenu": days_with_menu_serializer.values(),
            "orderedDays": days_list,
        }
    ).initial_data
    return general_calendar_serializer
