import codecs
import csv
import json
import re
from collections import namedtuple
from hashlib import sha256
from typing import Optional

import jdatetime
import pytz
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpResponse
from persiantools.jdatetime import JalaliDate

from . import models as m


def localnow() -> jdatetime.datetime:
    utc_now = jdatetime.datetime.now(tz=pytz.utc)
    local_timezone = pytz.timezone("Asia/Tehran")
    return utc_now.astimezone(local_timezone)


def get_user_minimal_info(user: m.User) -> dict:
    return {
        "fullname": user.FullName,
        "profile": user.Profile,
        "is_admin": user.IsAdmin,
    }


def get_str(date: jdatetime.date) -> str:
    """Converting a Jalali date object to a string
    yyyy/mm/dd
    """
    return date.strftime("%Y/%m/%d")


def first_and_last_day_date(month: int, year: int) -> tuple[str, str]:
    """This function returns a Jalali date object from the start and end
    dates provided
    """

    # Todo convert year and month to gro
    last_day_of_month = JalaliDate.days_in_month(month, year)
    first_day_date = get_str(jdatetime.date(year, month, 1))
    last_day_date = get_str(jdatetime.date(year, month, last_day_of_month))

    return first_day_date, last_day_date


def get_weekend_holidays(year: int, month: int) -> list[jdatetime.date]:
    """This function is responsible for calculating weekend holidays"""

    # Todo get last day of month in jalali date
    last_day_of_month = JalaliDate.days_in_month(month, year)
    holidays = []
    for daynum in range(1, last_day_of_month + 1):
        daynum_date = jdatetime.date(year, month, daynum)
        if daynum_date.weekday() in (6, 5):
            holidays.append(daynum_date.strftime("%Y/%m/%d").replace("-", "/"))
    return holidays


def get_current_date() -> tuple[int, int, int]:
    """Returning current date"""
    now = localnow()
    return now.year, now.month, now.day


def split_dates(dates, mode: str):
    """
    Splitting date and returning requested section based on mode.

    Args:
        dates: List of dates, or a single date to split.
        mode: The section, choose between `year`, `month` and `day`.

    Returns:
        List or single integer.
        int | list[int]
    """
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
    elif mode == "all":
        if not isinstance(dates, list):
            return (
                int(dates.split("/")[0]),
                int(dates.split("/")[1]),
                int(dates.split("/")[2]),
            )
        for date in dates:
            new_dates.append(
                (
                    int(dates.split("/")[0]),
                    int(dates.split("/")[1]),
                    int(dates.split("/")[2]),
                )
            )
        return new_dates


def split_json_dates(dates: str) -> dict[str, str]:
    """
    Splitting a json list of dates and generating a dict with day number.
    This function assumes that you have a `day` key in your json data that
    contains a VALID date

    Args:
        dates: serialized (json) data contains a `date` key.

    Returns:
        Deserialized data, date key will contain the number of day only.
    """

    dates = json.loads(dates)
    for obj in dates:
        obj["day"] = int(obj["day"].split("/")[2])
    return dates


def validate_date(date: str) -> Optional[str]:
    """
    Validating date value and format.
    Replacing "-" with "/" if the value is valid.

    Example:
        "1402/00/01" = valid
        "1402/0/1" = invalid, month and day section must have 2 integers.

    Args:
        date: the date for validation.

    Returns:
        date | None: date value or None if it was invalid.
    """

    pattern = r"^\d{4}\/\d{2}\/\d{2}$"
    if not isinstance(date, str):
        return None
    if "-" in date:
        date = date.replace("-", "/")
    if re.match(pattern, date):
        return date
    else:
        return None


def execute_raw_sql_with_params(query: str, params: tuple) -> list:
    """
    Executing raw queries via context manager

    Args:
        query: the raw query
        params: parameters used in query, avoiding sql injections

    Returns:
        result: the data retrieved by query
    """
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return result


def generate_csv(queryset: QuerySet):
    """
    This function generates a dynamic csv content based on
        the queryset data argument.

    Warnings:
        Please note that you have to customize your queryset via filter, values
            and other stuffs before using this function.
        All fields and values on received queryset will use in csv.

    Args:
        queryset: The queryset that you want to generate csv from it.

    Returns:
        str: csv content that generated from queryset.
    """
    response = HttpResponse(content_type="text/csv")
    response.write(codecs.BOM_UTF8)

    writer = csv.writer(response)

    headers_appended = False

    for obj in queryset:
        if isinstance(obj, dict):
            data = obj.values()
            if not headers_appended:
                writer.writerow(obj.keys())
                headers_appended = True
            writer.writerow(data)
        else:
            keys = []
            values = []
            for field in obj._meta.fields:
                keys.append(field.name)
                values.append(getattr(obj, field.name))

            if not headers_appended:
                writer.writerow(keys)
                headers_appended = True
            writer.writerow(values)

    return response


def validate_request_based_on_schema(
    schema: dict, data: dict
) -> tuple[str, int]:
    """
    This function is responsible for validating request data based on the
        provided schema.
    Validation is checked by both checking parameter names
        as well as their types.

    Args:
        schema (dict): Your prefered schema which you want
            to receive from requets
        data (dict): The request data.

    """

    schema_params = set(schema.keys())
    data_params = set(data.keys())
    diffs = schema_params.difference(data_params)
    if diffs:
        raise ValueError(f"{diffs} parameter(s) must specified.")

    for param in schema_params:
        if not isinstance(data.get(param), type(schema.get(param))):
            raise ValueError(f"Invalid {param} value.")


def get_specific_deadline(
    meal_type: m.Item.MealTypeChoices = None, weekday: int = None
):
    """
    Returning the submission's deadline based on the mealtype it has.
    Deadline is fetched from db based on the weekday.

    If meal_type parameter is not specified, will all deadlines available in
        Deadlines table.
    Args:
        meal_type: The submission's deadline.
        weekday: Number of weekday (due to dynamic deadline logic).

    Returns:
        Queryset of all deadlines | Days and hour value.
        Queryset | tuple[int, int]
    """

    if not meal_type and weekday:
        return m.Deadlines.objects.all()

    deadline = m.Deadlines.objects.get(MealType=meal_type, WeekDay=weekday)

    return deadline.Days, deadline.Hour


def generate_token_hash(
    personnel: str, full_name: str, random_bit: int
) -> str:
    packed_args = (
        personnel.encode()
        + full_name.encode()
        + bytes(str(random_bit), "utf-8")
    )
    return sha256(packed_args).hexdigest()


def get_personnel_from_token(token: str):
    return m.User.objects.filter(Token=token, IsActive=True).first()


def create_jdate_object(date: str) -> jdatetime.date:
    """
    Creating Jalali Date object from provided date.

    Args:
        date (str): The date you want to create object from.

    Returns:
        jdatetime.date
    """

    day = split_dates(date, "day")
    month = split_dates(date, "month")
    year = split_dates(date, "year")
    return jdatetime.date(year, month, day)


# For type annotation only
MealTypeDeadlines = dict[int, tuple[int, int], dict[int, tuple[int, int]]]


def get_deadlines(
    deadline: tuple,
) -> tuple[MealTypeDeadlines, MealTypeDeadlines]:
    """
    Fetching deadlines from database and forming 2 dicts from the data.
    Dicts are formed based on the meal type, one for each type.
    Dicts keys are the weekday nums, so we have 7 keys for each dict.

    Returns:
        tuple[MealTypeDeadlines, MealTypeDeadlines]:
        - MealTypeDeadlines: The dict that contains the day and hour deadline
            for each weekday number.

    Examples:
        breakfast_deadline[0] = (1, 12)
        Here the [0] means the first day of week (Shanbe / Saturday),
        and (1) is the Days deadline, (12) is Hour.

    """

    deadlines = m.Deadlines.objects.all()
    breakfast_deadlines = {}
    launch_deadlines = {}

    for row in deadlines:
        if row.MealType == m.MealTypeChoices.BREAKFAST:
            breakfast_deadlines[row.WeekDay] = deadline(row.Days, row.Hour)
        else:
            launch_deadlines[row.WeekDay] = deadline(row.Days, row.Hour)

    return breakfast_deadlines, launch_deadlines
