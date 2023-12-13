import json
from typing import Optional

import jdatetime
from django.db.models import Sum

from . import models as m
from . import serializers as s
from .config import ORDER_REGISTRATION_CLOSED_IN
from .utils import (
    first_and_last_day_date,
    is_date_valid_for_action,
    split_json_dates,
    validate_date,
)


def validate_request(data: dict) -> tuple[str, int]:
    """
    This function is responsible for validating request data for
        validator classes which are defined in this module.

    Args:
        data (dict): The request data which must contains:\n
            - 'date' (str): The date which you want to submit action on.
            - 'item' (int | str): The item which you want to do action with.

    Raises:
        ValueError: If parameters are not specified, or not valid.

    Returns:
        date: Validated date value.
        item: Validated item value.
    """

    date = validate_date(data.get("date"))
    item = data.get("item")
    if not (date and item):
        raise ValueError("'item' and 'date' must specified.")
    try:
        item = int(item)
    except ValueError:
        raise ValueError("invalid 'item' value.")

    return date, item


def validate_calendar_request(
    data: dict,
) -> Optional[str]:
    """
    Responsible for validating request data for calendars.

    Args:
        data: request data which must contains `year` and `month` value.

    Returns:
        Error message if data violates the validation.

    """

    year = data.get("year")
    month = data.get("month")

    if not (year and month):
        return "'year' and 'month' parameters must specifed."
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        return "Invalid parameters."

    if not 1 <= month <= 12:
        return "Invalid month value."


def get_days_with_menu(month: int, year: int) -> dict[str, str]:
    """
    Fetching the days with menu on database and total orders
        on each day.

    Args:
        month: requested month.
        year: requested year.

    Returns:
        Serialized data contains the day with menus and total orders.
    """

    first_day, last_day = first_and_last_day_date(month, year)

    days_with_menu = (
        m.ItemsOrdersPerDay.objects.filter(Date__range=[first_day, last_day])
        .values("Date")
        .annotate(TotalOrders=Sum("TotalOrders"))
    )
    days_with_menu_serializer = s.DayWithMenuSerializer(
        days_with_menu, many=True
    ).data
    splited_days_with_menu = split_json_dates(
        json.dumps(days_with_menu_serializer)
    )

    return splited_days_with_menu


class ValidateRemove:
    """
    This class is responsible for validating item removal in menus.
    The data will pass multiple validations, if no error occurred,
    the item will get removed from the corresponding date.

    Attributes:
        data: Raw data retrieved from request.
        item: Item id that has been requested to remove,
            available AFTER validation.
        date: The corresponding menu date, available AFTER validation.
        error: Catched error message which was caused by validation violations,
            NOT available if data was valid.
    Request Args:
        id: The item id for removal.
        date: The corresponding menu date.
    """

    def __init__(self, request_data: dict) -> None:
        self.data = request_data

    def is_valid(self) -> bool:
        """
        Applying validations to the request data.
        if the request was not valid, will return false and
        store error result inside `self.error`.

        Returns:
            bool: was the request data valid or not.
        """

        try:
            self.date, self.item = validate_request(self.data)
            self._validate_date()
            self._validate_item()
        except ValueError as e:
            self.error = str(e)
            return False
        return True

    def _validate_date(self):
        """Validating date based on `validate_date` logic."""

        date = validate_date(self.date)
        if not date:
            raise ValueError("Date is not valid.")

        is_date_valid_for_removal = is_date_valid_for_action(date)
        if not is_date_valid_for_removal:
            raise ValueError("Deadline for any action on this date is over.")

    def _validate_item(self):
        """
        Checking if item is available on the corresponding date,
        Then checking if anyone has ordered this item yet,
        if someone has ordered already, the item is not valid for removing.
        """

        instance = m.DailyMenuItem.objects.filter(
            Item=self.item,
            AvailableDate=self.date,
            IsActive=True,
            Item__IsActive=True,
        )
        if not instance:
            raise ValueError("Item does not exists in provided date.")
        orders = m.OrderItem.objects.filter(
            DeliveryDate=self.date, Item=self.item
        )
        if orders:
            raise ValueError(
                "This item is not eligable for deleting, an order has already"
                "owned this item."
            )

    def remove_item(self):
        m.DailyMenuItem.objects.get(
            AvailableDate=self.date, Item=self.item
        ).delete()


class ValidateOrder:
    """
    Validating order submission and submiting order if it's valid.
    The data will pass several validation before submission.

    Attributes:
        data: Raw data retrieved from request.
        item: The item which was requested by client,
            available AFTER validation.
        date: The order date, available AFTER validation.
        error: Catched error message which was caused by validation violations,
            NOT available if data was valid.

    Request Args:
        id: The item id for removal.
        date: The corresponding menu date.
    """

    def __init__(self, request_data) -> None:
        self.data: dict = request_data

    def is_valid(self, create=False, remove=False):
        """
        Applying validations to the request data based on the request type.
        if the request was not valid, will return false and
        store error result inside `self.error`.

        Its essential to specify ONE of the optional parameters,
        Otherwise will raise ValueError

        Args:
            Optional[create]: Apply submission validations.
            Optional[remove]: Apply removal validations.

        Returns:
            bool: was the request data valid or not.

        Raises:
            ValueError: If no parameters are specified.
        """

        if not (create or remove):
            raise ValueError(
                "No parameters are specified for applying validations."
            )

        try:
            self.date, self.item = validate_request(self.data)
            self._validate_date()
            if create:
                self._validate_item()
            elif remove:
                self._validate_removal()
        except ValueError as e:
            self.error = str(e)
            return False

        return True

    def _validate_date(self):
        """
        Validating date value based on `validate_date` logic first,
        Then checking if the order date is within deadline
        and valid for submission | removal.
        """

        date = validate_date(self.date)
        if not date:
            raise ValueError("invalid 'date' value.")
        is_valid = is_date_valid_for_action(date)
        if not is_valid:
            raise ValueError("Deadline for any action on this date is over.")

    def _validate_item(self):
        """
        Checking if the item is available in the requested date.
        Fetch and storing item in self.item if it was valid.
        """

        is_item_available = m.DailyMenuItem.objects.filter(
            Item=self.item,
            AvailableDate=self.date,
            IsActive=True,
            Item__IsActive=True,
        ).first()
        if not is_item_available:
            raise ValueError("item is not available in corresponding date.")

        self.item = m.Item.objects.filter(pk=self.item).first()

    def _validate_removal(self):
        """
        Checking if the personnel has ordered the specified item
            on provided date.
        """

        order_item = m.OrderItem.objects.filter(
            Personnel=self.data.get("personnel"),
            DeliveryDate=self.date,
            Item=self.item,
        ).first()
        if not order_item:
            raise ValueError("No order has been created with provided data.")

        self.order_item = order_item

    def create_order(self):
        """
        Submitting order.
        If the personnel has already ordered that item on the requested date,
        will instead increase its quantity by 1.
        """

        instance = m.OrderItem.objects.filter(
            Personnel=self.data.get("personnel"),
            DeliveryDate=self.date,
            Item=self.item,
        ).first()
        if instance:
            instance.Quantity += 1
            instance.save()
            return

        m.OrderItem.objects.create(
            Personnel=self.data.get("personnel"),
            DeliveryDate=self.date,
            Item=self.item,
            Quantity=1,
            PricePerOne=self.item.CurrentPrice,
        )

    def remove_order(self):
        """
        Removing the specified order.

        If the order quantity is greater than 1, then will decrease
            its value by 1,
        otherwise will remove the record.
        """

        if self.order_item.Quantity > 1:
            self.order_item.Quantity -= 1
        else:
            self.order_item.delete()


class ValidateBreakfast:
    """
    Validating breakfast order submission and submitting order
        if data was valid.
    The data will pass several validation before submission.

    Attributes:
        data: Raw data retrieved from request.
        item: Item id that has been requested to remove,
            available AFTER validation.
        date: The corresponding menu date, available AFTER validation.
        error: Catched error message which was caused by validation violations,
            NOT available if data was valid.

    Request Args:
        id: The item id for removal.
        date: The corresponding menu date.
    """

    def __init__(self, request_data: dict) -> None:
        self.data = request_data

    def is_valid(self):
        """
        Applying validations to the request data.
        if the request was not valid, will return false and
        store error result inside `self.error`.

        Returns:
            bool: was the request data valid or not.
        """

        try:
            self.date, self.item = validate_request(self.data)
            self._validate_date()
            self._validate_item()
            self._validate_order()
        except ValueError as e:
            self.error = str(e)
            return False

        return True

    def _validate_date(self):
        """
        Validating date value.
        Personnel must submit breakfast orders 1 week sooner.
        """

        date = validate_date(self.date)
        if not date:
            raise ValueError("Invalid date value.")

        now = jdatetime.datetime.now()
        if now.hour > ORDER_REGISTRATION_CLOSED_IN:
            now += jdatetime.timedelta(days=8)
        else:
            now += jdatetime.timedelta(days=7)

        eligable_date = now.strftime("%Y/%m/%d")
        if date >= eligable_date:
            return

        raise ValueError("Deadline for submitting breakfast order is over.")

    def _validate_item(self):
        """
        Checking if the item is available in the requested date,
            then checking if the item's `MealType` is breakfast.

        Fetch and storing item in `self.item` if it was valid.
        """

        is_item_valid = m.DailyMenuItem.objects.filter(
            Item=self.item,
            AvailableDate=self.date,
            IsActive=True,
            Item__IsActive=True,
            Item__MealType=m.Item.MealTypeChoices.BREAKFAST,
        )
        if not is_item_valid:
            raise ValueError("Item is not valid.")

        self.item = m.Item.objects.filter(pk=self.item).first()

    def _validate_order(self):
        """
        Checking if the personnel has already submitted breakfast order
            on the provided date.
        The resason is each personnel can only submit ONE breakfast a day.

        """
        does_personnel_already_submitted_breakfast_order = (
            m.OrderItem.objects.filter(
                Personnel=self.data.get("personnel"),
                DeliveryDate=self.date,
                Item=self.item,
            )
        )
        if does_personnel_already_submitted_breakfast_order:
            raise ValueError(
                "Personnel has already submitted a breakfast order on this"
                " date."
            )

    def create_breakfast_order(self):
        """Creating breakfast order for personnel"""

        m.OrderItem.objects.create(
            Personnel=self.data.get("personnel"),
            DeliveryDate=self.date,
            Item=self.item,
            PricePerOne=self.item.CurrentPrice,
        )
