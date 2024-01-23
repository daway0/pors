import json
from typing import Optional

import jdatetime
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from . import models as m
from . import serializers as s
from .utils import (
    execute_raw_sql_with_params,
    first_and_last_day_date,
    get_submission_deadline,
    localnow,
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
          - 'item' (int): The item which you want to do action with.

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

    with open("./pors/SQLs/DayWithMenuOrderCount.sql", "r") as file:
        query = file.read()
    result = execute_raw_sql_with_params(query, (first_day, last_day))

    days_with_menu_serializer = s.DayWithMenuSerializer(result, many=True).data
    splited_days_with_menu = split_json_dates(
        json.dumps(days_with_menu_serializer)
    )

    return splited_days_with_menu


def is_date_valid_for_action(
    now: jdatetime.datetime, date: str, days_deadline: int, hours_deadline: int
) -> bool:
    """
    This function is responsible for checking if the date
    is valid for any action (submission | removal) based on the deadline.

    Args:
        date: the corresponding date
        deadline: The deadline of the submission.

    Returns:
        bool: is the date valid or not.
    """

    if 24 > hours_deadline < 0:
        raise ValueError("`hours_deadline` value must be between 0 and 24.")

    eligable_date = now + jdatetime.timedelta(days=days_deadline)
    if eligable_date.hour >= hours_deadline:
        eligable_date += jdatetime.timedelta(days=1)

    if date >= eligable_date.strftime("%Y/%m/%d"):
        return True
    return False


def get_first_orderable_date(
    now: jdatetime.datetime,
    days_deadline: int,
    hours_deadline: int,
):
    """
    Returning the first valid date for order submission based on deadline.

    Args:
        now: Current datetime.
        deadline: The deadline of the submissions.

    Returns:
        Tuple of `year`, `month` and `day` values, don't forget the order :).
    """
    if 24 > hours_deadline < 0:
        raise ValueError("`hours_deadline` value must be between 0 and 24.")

    now += jdatetime.timedelta(days=days_deadline)
    if now.hour >= hours_deadline:
        now += jdatetime.timedelta(days=1)
    return now.year, now.month, now.day


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
        message: Personnel friendly error message that describes the reason
            of violations, can be used in `messages` module,
            NOT available if data was valid.
    Request Args:
        id: The item id for removal.
        date: The corresponding menu date.
    """

    def __init__(self, request_data: dict) -> None:
        self.data = request_data
        self.error = ""
        self.message = ""

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
            self._validate_item()
            self._validate_date()
        except ValueError as e:
            self.error = str(e)
            return False

        return True

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
            self.message = "آیتم مورد نظر در منو موجود نمی‌باشد."
            raise ValueError("Item does not exists in provided date.")

        orders = m.OrderItem.objects.filter(
            DeliveryDate=self.date, Item=self.item
        )
        if orders:
            self.message = (
                "آیتم مورد نظر در حال حاضر توسط پرسنل سفارش داده شده است و"
                " قابل حذف نیست."
            )
            raise ValueError(
                "This item is not eligable for deleting, an order has already"
                "owned this item."
            )
        self.item = m.Item.objects.filter(pk=self.item).first()

    def _validate_date(self):
        """Validating date based on `is_date_valid_for_action` logic."""

        now = localnow()

        days_deadline, hours_deadline = get_submission_deadline(
            self.item.MealType, now.weekday()
        )

        is_date_valid_for_removal = is_date_valid_for_action(
            now, self.date, days_deadline, hours_deadline
        )
        if not is_date_valid_for_removal:
            self.message = "مهلت حذف کردن آیتم در تاریخ مورد نظر تمام شده است."
            raise ValueError(
                f"Deadline for {self.item.MealType} related"
                " actions on this date is over."
            )

    def remove_item(self):
        """Removing the item from menu.

        Warnings:
            DO NOT use this method before checking `is_valid` method.
        """

        if self.error:
            raise ValueError(
                "This method is only available if provided data is valid."
            )

        m.DailyMenuItem.objects.get(
            AvailableDate=self.date, Item=self.item
        ).delete(
            log=(
                f"Item {self.item.ItemName} just removed from menu for"
                f" {self.date}"
            ),
            user=self.data.get("personnel"),
        )


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
        message: Personnel friendly error message that describes the reason
            of violations, can be used in `messages` module,
            NOT available if data was valid.

    Request Args:
        id: The item id for removal.
        date: The corresponding menu date.
    """

    def __init__(self, request_data) -> None:
        self.data: dict = request_data
        self.error = ""
        self.message = ""

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
            if create:
                self._validate_item_submission()
            elif remove:
                self._validate_item_removal()
            self._validate_date()
        except ValueError as e:
            self.error = str(e)
            return False

        return True

    def _validate_item_submission(self):
        """
        Checking if the item is available in the requested date.
        Fetch and storing item in self.item if it was valid.
        """

        is_item_available = m.DailyMenuItem.objects.filter(
            Item=self.item,
            AvailableDate=self.date,
            IsActive=True,
            Item__IsActive=True,
            Item__MealType=m.Item.MealTypeChoices.LAUNCH,
        ).first()
        if not is_item_available:
            self.message = "آیتم مورد نظر در تاریخ داده شده موجود نمی‌باشد."
            raise ValueError("item is not available in corresponding date.")

        self.item = m.Item.objects.filter(pk=self.item).first()

    def _validate_item_removal(self):
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
            self.message = "آیتم مورد نظر در این تاریخ سفارش داده نشده است."
            raise ValueError("No order has been created with provided data.")

        self.order_item = order_item
        self.item = m.Item.objects.filter(pk=self.item).first()

    def _validate_date(self):
        """
        Checking if the order date is within deadline
        and valid for submission | removal.
        """

        now = localnow()

        days_deadline, hours_deadline = get_submission_deadline(
            self.item.MealType, now.weekday()
        )

        is_valid = is_date_valid_for_action(
            now, self.date, days_deadline, hours_deadline
        )
        if not is_valid:
            self.message = "مهلت ثبت / لغو سفارش در این تاریخ تمام شده است."
            raise ValueError(
                "Deadline for"
                f" {self.item.MealType} related actions"
                " on this date is over."
            )

    def create_order(self):
        """
        Submitting order.
        If the personnel has already ordered that item on the requested date,
        will instead increase its quantity by 1.

        Warnings:
            DO NOT use this method before checking `is_valid` method.
        """

        if self.error:
            raise ValueError(
                "This method is only available if provided data is valid."
            )

        instance = m.OrderItem.objects.filter(
            Personnel=self.data.get("personnel"),
            DeliveryDate=self.date,
            Item=self.item,
        ).first()
        if instance:
            instance.Quantity += 1
            instance.save(
                log=(
                    f"Launch Item {self.item.ItemName}'s Quantity just"
                    f" increased by 1 for {self.date}"
                ),
                user=self.data.get("personnel"),
            )
            return

        m.OrderItem(
            Personnel=self.data.get("personnel"),
            DeliveryDate=self.date,
            Item=self.item,
            Quantity=1,
            PricePerOne=self.item.CurrentPrice,
        ).save(
            log=(
                f"Launch Item {self.item.ItemName} just added to order for"
                f" {self.date}"
            ),
            user=self.data.get("personnel"),
        )

    def remove_order(self):
        """
        Removing the specified order.

        If the order quantity is greater than 1, then will decrease
            its value by 1,
        otherwise will remove the record.

        Warnings:
            DO NOT use this method before checking `is_valid` method.
        """

        if self.error:
            raise ValueError(
                "This method is only available if provided data is valid."
            )

        if self.order_item.Quantity > 1:
            self.order_item.Quantity -= 1
            self.order_item.save(
                log=(
                    f"Item {self.item.ItemName}'s Quantity just decreased by 1"
                    f" for {self.date}"
                ),
                user=self.data.get("personnel"),
            )
        else:
            self.order_item.delete(
                log=(
                    f"Item {self.item.ItemName} removed from order for"
                    f" {self.date}"
                ),
                user=self.data.get("personnel"),
            )


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
        message: Personnel friendly error message that describes the reason
            of violations, can be used in `messages` module,
            NOT available if data was valid.

    Request Args:
        id: The item id for removal.
        date: The corresponding menu date.
    """

    def __init__(self, request_data: dict) -> None:
        self.data = request_data
        self.error = ""
        self.message = ""

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
            self._validate_item()
            self._validate_date()
            self._validate_order()
        except ValueError as e:
            self.error = str(e)
            return False

        return True

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
            self.message = "آیتم مورد نظر فعال نمی‌باشد."
            raise ValueError("Item is not valid.")

        self.item = m.Item.objects.filter(pk=self.item).first()

    def _validate_date(self):
        """
        Validating date value.
        Personnel must submit breakfast orders 1 week sooner.
        """

        now = localnow()
        days_deadline, hours_deadline = get_submission_deadline(
            self.item.MealType, now.weekday()
        )

        is_valid_for_submission = is_date_valid_for_action(
            now, self.date, days_deadline, hours_deadline
        )
        if not is_valid_for_submission:
            self.message = (
                "مهلت ثبت / لغو سفارش صبحانه در این تاریخ تمام شده است."
            )
            raise ValueError(
                "Deadline for submitting breakfast order is over."
            )

    def _validate_order(self):
        """
        Counting total number of breakfast orders on the provided date
            and comparing it to the SystemSetting configs.
        The resason is the number of breakfast orders is limited.

        """

        total_breakfast_orders = (
            m.OrderItem.objects.filter(
                Personnel=self.data.get("personnel"),
                DeliveryDate=self.date,
                Item__MealType=m.Item.MealTypeChoices.BREAKFAST,
            )
            .values("Quantity")
            .aggregate(total=Coalesce(Sum("Quantity"), Value(0)))["total"]
        )

        threshold = (
            m.SystemSetting.objects.last().TotalItemsCanOrderedForBreakfastByPersonnel
        )
        if total_breakfast_orders >= threshold:
            self.message = "محدودیت ثبت سفارش صبحانه‌ای رد شده است."
            raise ValueError(
                "Personnel has already submitted a breakfast order on this"
                " date."
            )

    def create_breakfast_order(self):
        """
        Creating breakfast order for personnel

        Warnings:
            DO NOT use this method before checking `is_valid` method.
        """

        if self.error:
            raise ValueError(
                "This method is only available if provided data is valid."
            )

        instance = m.OrderItem.objects.filter(
            Personnel=self.data.get("personnel"),
            DeliveryDate=self.date,
            Item=self.item,
        ).first()
        if instance:
            instance.Quantity += 1
            instance.save(
                log=(
                    f"Breakfast Item {self.item.ItemName}'s Quantity just"
                    f" increased by 1 for {self.date}"
                ),
                user=self.data.get("personnel"),
            )
            return

        m.OrderItem(
            Personnel=self.data.get("personnel"),
            DeliveryDate=self.date,
            Item=self.item,
            PricePerOne=self.item.CurrentPrice,
        ).save(
            log=(
                f"Breakfast Item {self.item.ItemName} just added to the order"
                f" for {self.date}"
            ),
            user=self.data.get("personnel"),
        )


class ValidateAddMenuItem:
    """
    Validating data that was provided for adding specific
        item to a date's menu.
    The data will pass several validation before submission.

    Attributes:
        data: Raw data retrieved from request.
        item: Item id that has been requested to add,
            available AFTER validation.
        date: The corresponding menu date, available AFTER validation.
        error: Catched error message which was caused by validation violations,
            NOT available if data was valid.
        message: Personnel friendly error message that describes the reason
            of violations, can be used in `messages` module,
            NOT available if data was valid.

    Raises:
        ValueError: If the data violated any validations.
    """

    def __init__(self, request_data: dict) -> None:
        self.data = request_data
        self.error = ""
        self.message = ""

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
            self._validate_item()
            self._validate_date()
        except ValueError as e:
            self.error = str(e)
            return False

        return True

    def _validate_item(self):
        """
        Checking if the item is exists and valid.
        Then checking if the item is already exists in provided date's menu.

        Raises:
            ValueError:
            -  If the item does not exists in db, or not active.
            -  If the item currently exists in menu.
        """

        item_instance = m.Item.objects.filter(
            pk=self.item, IsActive=True
        ).first()
        if not item_instance:
            self.message = "آیتم مورد نظر فعال نمی‌باشد."
            raise ValueError("Invalid item.")

        self.item = item_instance

        is_already_exists = m.DailyMenuItem.objects.filter(
            AvailableDate=self.date, Item=self.item, IsActive=True
        )
        if is_already_exists:
            self.message = "آیتم مورد نظر در حال حاضر در منو روز موجود است."
            raise ValueError("Item already exists in provided date.")

    def _validate_date(self):
        """
        Checking if the date is valid for adding item to menu.

        Raises:
            ValueError:
            -  If the deadline has passed for adding.
        """

        now = localnow()
        days_deadline, hours_deadline = get_submission_deadline(
            self.item.MealType, now.weekday()
        )

        is_date_valid_for_add = is_date_valid_for_action(
            now, self.date, days_deadline, hours_deadline
        )
        if not is_date_valid_for_add:
            self.message = (
                "مهلت اضافه / حذف کردن آیتم مورد نظر در این تاریخ تمام شده"
                " است."
            )
            raise ValueError(
                "Deadline for"
                f" {self.item.MealType} related actions"
                " on this date is over."
            )

    def add_item(self):
        """
        Adding provided item to the provided date's menu.

        Warnings:
            DO NOT use this method before checking `is_valid` method.
        """

        if self.error:
            raise ValueError(
                "This method is only available if provided data is valid."
            )

        m.DailyMenuItem(AvailableDate=self.date, Item=self.item).save(
            log=(
                f"Item {self.item.ItemName} just added to the menu for"
                f" {self.date}"
            ),
            user=self.data.get("personnel"),
        )
