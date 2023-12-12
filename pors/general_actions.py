import json

import jdatetime
from django.db.models import Sum
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


class GeneralCalendar:
    """
    This class is responsible for generating general calendar
    for both admin and non admin users.

    Args:
        year: Requested year.
        month: Requested month.
    """

    def __init__(self, year: int, month: int) -> None:
        self.year = year
        self.month = month

    def get_calendar(self):
        """
        Returning the general calendar serilized data.
        """

        return GeneralCalendarSerializer(
            data={
                "year": self.year,
                "month": self.month,
                "firstDayOfWeek": self._get_first_day_of_week(),
                "lastDayOfMonth": self._get_last_day_of_month(),
                "holidays": self._get_holidays(),
            }
        ).initial_data

    def _get_last_day_of_month(self) -> int:
        last_day = JalaliDate.days_in_month(self.month, self.year)
        return last_day

    def _get_first_day_of_week(self) -> int:
        first_day_week_num = jdatetime.datetime(
            self.year, self.month, 1
        ).weekday()

        # increasing by 1 since the value starts from 0
        return first_day_week_num + 1

    def _get_first_and_last_day_of_month(self) -> tuple[int, int]:
        first_day_date, last_day_date = first_and_last_day_date(
            self.month, self.year
        )
        return first_day_date, last_day_date

    def _get_holidays(self):
        """
        Fetching holidays from database,
        Then calculating weekend holidays and packing them into unique list.
        """

        first_day, last_day = self._get_first_and_last_day_of_month()
        weekend_holidays = get_weekend_holidays(self.year, self.month)
        holidays = Holiday.objects.filter(
            HolidayDate__range=(first_day, last_day)
        )
        holidays_serializer = HolidaySerializer(holidays).data

        # Unpacking dict into list
        listed_holidays_serializer: list = holidays_serializer["holidays"]
        listed_holidays_serializer += weekend_holidays
        listed_holidays_serializer.sort()
        splited_holidays = split_dates(listed_holidays_serializer, mode="day")

        # Making it a set due to removing duplicate.
        return set(splited_holidays)
