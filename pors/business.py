import json
from typing import Optional

import jdatetime
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from . import models as m
from . import serializers as s
from .utils import (
    create_jdate_object,
    execute_raw_sql_with_params,
    first_and_last_day_date,
    get_specific_deadline,
    localnow,
    split_dates,
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
    breakfast_deadlines: dict[int, s.Deadline],
    launch_deadlines: dict[int, s.Deadline],
):
    """
    Returning the first valid date for order submission based on deadline.
    The deadline values must be a Deadline namedtuple.

    Args:
        now: Current datetime.
        breakfast_deadlines: Deadline for breakfast submissions.
        launch_deadlines: Deadline for launch submissions.
    Returns:
        Tuple of `year`, `month` and `day` values, don't forget the order :).
    """

    passed_days = 0
    weekday = now.weekday()
    while True:
        breakfast_deadline = breakfast_deadlines[weekday]
        launch_deadline = launch_deadlines[weekday]

        if (
            (
                breakfast_deadline.Days == passed_days
                and breakfast_deadline.Hour <= now.hour
            )
            or (breakfast_deadline.Days > passed_days)
        ) and (
            (
                launch_deadline.Days == passed_days
                and launch_deadline.Hour <= now.hour
            )
            or (launch_deadline.Days > passed_days)
        ):

            passed_days += 1
            if weekday != 6:  # has 7 days only (starts with 0)
                weekday += 1
            else:
                weekday = 0

        else:
            now += jdatetime.timedelta(days=passed_days)
            return now.year, now.month, now.day


class OverrideUserValidator:
    """
    Abstract class for classes that allow admins to manipulate/create/delete
    user's orders.
    All classes that are inheriting from this class, will allow admins to
    do actions on behalf of the personnel, without any DATE related
    limitations.

    If 'override_user' arg is provided, then 'user' will be the
    'override_user', and the 'user' attribute will be the 'admin' user.
    If not, then the 'user' is personnel and admin is None.

    Args:
        user: Personnel's user object.
        admin_user: Admin's user object.
    """

    def __init__(
        self,
        user: m.User,
        override_user: m.User,
    ) -> None:
        self.user = user if not override_user else override_user
        self.admin_user = user.Personnel if override_user else None
        self.reason: m.AdminManipulationReason = None
        self.comment: str = None

    def validate_admin_request(self, data: dict):
        """
        Validating request that supposed to come from admin.
        """
        s_data = s.AdminReasonserializer(data=data)
        if not s_data.is_valid():
            raise ValueError(s_data.errors)

        if s_data.validated_data[
            "reason"
        ].Title == "other" and not s_data.validated_data.get("comment"):
            raise ValueError(
                "you must provide a comment when using other's reason"
            )

        self.reason = s_data.validated_data["reason"]
        self.comment = s_data.validated_data.get("comment")

    def _is_admin(self) -> bool:
        if not self.admin_user:
            return False
        return True


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

    def __init__(self, request_data: dict, user: m.User) -> None:
        self.data = request_data
        self.user = user
        self.error = ""
        self.date: str = ""
        self.item: m.Item = m.Item.objects.none()

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

        year, month, day = split_dates(self.date, mode="all")
        date_obj = jdatetime.datetime(year, month, day)
        days_deadline, hours_deadline = get_specific_deadline(
            date_obj.weekday(), self.item.MealType
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
            user=self.user.Personnel,
        )


class ValidateOrder(OverrideUserValidator):
    """
    Validating order submission and submiting order if it's valid.
    The data will pass several validation before submission.

    Attributes:
        data: Raw data retrieved from request.
        user: User object.
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

    def __init__(
        self, request_data: dict, user: m.User, override_user: m.User
    ) -> None:
        super().__init__(user, override_user)
        self.data = request_data
        self.message: str = ""
        self.error = ""
        self.date: str = ""
        self.item: m.Item = m.Item.objects.none()
        self.order_item: m.OrderItem = m.OrderItem.objects.none()

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
                self._validate_default_delivery_building()
            elif remove:
                self._validate_item_removal()

            if not self._is_admin():
                self._validate_date()
            else:
                self.validate_admin_request(self.data)

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

    def _validate_default_delivery_building(self):
        """
        Checking user's default delivery building and floor value in db.
        Either one or both of them is null, it raise ValueError.
        """

        delivery_building = self.user.LastDeliveryBuilding
        delivery_floor = self.user.LastDeliveryFloor
        if not (delivery_building and delivery_floor):
            self.message = (
                "لطفا پیش از ثبت سفارش محل تحویل سفارش خود را انتخاب کنید."
            )
            raise ValueError(
                "User does not have default value for buidling and floor."
            )

    def _validate_item_removal(self):
        """
        Checking if the personnel has ordered the specified item
            on provided date.
        """

        order_item = m.OrderItem.objects.filter(
            Personnel=self.user.Personnel,
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

        year, month, day = split_dates(self.date, mode="all")
        date_obj = jdatetime.datetime(year, month, day)
        days_deadline, hours_deadline = get_specific_deadline(
            date_obj.weekday(), self.item.MealType
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
            Personnel=self.user.Personnel,
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
                user=self.user.Personnel,
                admin=self.admin_user,
                reason=self.reason,
                comment=self.comment,
            )
            return

        m.OrderItem(
            Personnel=self.user.Personnel,
            DeliveryDate=self.date,
            DeliveryBuilding=self.user.LastDeliveryBuilding,
            DeliveryFloor=self.user.LastDeliveryFloor,
            Item=self.item,
            Quantity=1,
            PricePerOne=self.item.CurrentPrice,
        ).save(
            log=(
                f"Launch Item {self.item.ItemName} just added to order for"
                f" {self.date}"
            ),
            user=self.user.Personnel,
            admin=self.admin_user,
            reason=self.reason,
            comment=self.comment,
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
                user=self.user.Personnel,
                admin=self.admin_user,
                reason=self.reason,
                comment=self.comment,
            )
        else:
            self.order_item.delete(
                log=(
                    f"Item {self.item.ItemName} removed from order for"
                    f" {self.date}"
                ),
                user=self.user.Personnel,
                admin=self.admin_user,
                reason=self.reason,
                comment=self.comment,
            )


class ValidateBreakfast(OverrideUserValidator):
    """
    Validating breakfast order submission and submitting order
        if data was valid.
    The data will pass several validation before submission.

    Attributes:
        data: Raw data retrieved from request.
        user: User object.
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

    def __init__(
        self, request_data: dict, user: m.User, override_user: m.User
    ) -> None:
        super().__init__(user, override_user)
        self.data = request_data
        self.message: str = ""
        self.error: str = ""
        self.date: str = ""
        self.item: m.Item = m.Item.objects.none()

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
            self._validate_default_delivery_building()

            if not self._is_admin():
                self._validate_date()
            else:
                self.validate_admin_request(self.data)

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

    def _validate_default_delivery_building(self):
        """
        Checking user's default delivery building and floor value in db.
        Either one or both of them is null, it raise ValueError.
        """

        delivery_building = self.user.LastDeliveryBuilding
        delivery_floor = self.user.LastDeliveryFloor
        if not (delivery_building and delivery_floor):
            self.message = (
                "لطفا پیش از ثبت سفارش محل تحویل سفارش خود را انتخاب کنید."
            )
            raise ValueError(
                "User does not have default value for buidling and floor."
            )

    def _validate_date(self):
        """
        Validating date value.
        Personnel must submit breakfast orders 1 week sooner.
        """

        now = localnow()

        year, month, day = split_dates(self.date, mode="all")
        date_obj = jdatetime.datetime(year, month, day)
        days_deadline, hours_deadline = get_specific_deadline(
            date_obj.weekday(), self.item.MealType
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
                Personnel=self.user.Personnel,
                DeliveryDate=self.date,
                DeliveryBuilding=self.user.LastDeliveryBuilding,
                DeliveryFloor=self.user.LastDeliveryFloor,
                Item__MealType=m.Item.MealTypeChoices.BREAKFAST,
            )
            .values("Quantity")
            .aggregate(total=Coalesce(Sum("Quantity"), Value(0)))["total"]
        )

        threshold = (
            m.SystemSetting.objects.last().TotalItemsCanOrderedForBreakfastByPersonnel
        )
        if total_breakfast_orders >= threshold:
            self.message = (
                f" امکان سفارش حداکثر{threshold} عدد آیتم صبحانه‌ای وجود دارد."
            )
            raise ValueError(
                f"Personnel cannot submit more than {threshold} breakfast"
                " item(s)."
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
            Personnel=self.user.Personnel,
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
                user=self.user.Personnel,
                admin=self.admin_user,
                reason=self.reason,
                comment=self.comment,
            )
            return

        m.OrderItem(
            Personnel=self.user.Personnel,
            DeliveryDate=self.date,
            DeliveryBuilding=self.user.LastDeliveryBuilding,
            DeliveryFloor=self.user.LastDeliveryFloor,
            Item=self.item,
            PricePerOne=self.item.CurrentPrice,
        ).save(
            log=(
                f"Breakfast Item {self.item.ItemName} just added to the order"
                f" for {self.date}"
            ),
            user=self.user.Personnel,
            admin=self.admin_user,
            reason=self.reason,
            comment=self.comment,
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

    def __init__(self, request_data: dict, user: m.User) -> None:
        self.data = request_data
        self.user = user
        self.message: str = ""
        self.error: str = ""
        self.date: str = ""
        self.item: m.Item = m.Item.objects.none()

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
        year, month, day = split_dates(self.date, mode="all")
        date_obj = jdatetime.datetime(year, month, day)
        days_deadline, hours_deadline = get_specific_deadline(
            date_obj.weekday(), self.item.MealType
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
            user=self.user.Personnel,
        )


class ValidateDeliveryBuilding(OverrideUserValidator):
    """
    This class is responsible for validating 'change delivery building' api.
    If the data was valid, the user can change their delivery building and
        floor via 'change_delivary_place' interface.

    Attributes:
        data: Raw request data.
        error: Catched error message which was caused by validation violations,
            NOT available if data was valid.
        message: Personnel friendly error message that describes the reason
            of violations, can be used in `messages` module,
            NOT available if data was valid.
        date: User provided date after validation.
        available_buildings: Valid buildings which must fetched from HR.
        order: Related order object.
    """

    def __init__(
        self,
        request_data: dict,
        buildings: dict[str, list[str]],
        user: m.User,
        override_user: m.User,
    ) -> None:
        super().__init__(user, override_user)
        self.available_buildings: dict[str, list[str]] = buildings
        self.data = request_data
        self.message: str = ""
        self.error: str = ""
        self.date: str = ""
        self.new_delivery_building: str = ""
        self.new_delivery_floor: str = ""
        self.order: m.Order = m.Order.objects.none()

    def is_valid(self):
        """
        Applying validations to the request data.
        if the request was not valid, will return false and
        store error result inside `self.error`.

        Returns:
            bool: was the request data valid or not.
        """

        try:
            self._validate_request()
            self._validate_building()
            self._validate_order_items()

            if not self._is_admin():
                self._validate_date()
            else:
                self.validate_admin_request(self.data)

        except ValueError as e:
            self.error = str(e)
            return False

        return True

    def _validate_request(self):
        """
        Validating request data must contains:
          - date: Date which user wants to change their building on.
          - newDeliveryBuilding: Valid building.
          - newDeliveryFloor: Valid floor.

        After validation, data will get store on their applicable attr.
        """

        date = self.data.get("date")
        new_delivery_building = self.data.get("newDeliveryBuilding")
        new_delivery_floor = self.data.get("newDeliveryFloor")
        meal_type = self.data.get("mealType")
        if not (
            date and new_delivery_building and new_delivery_floor and meal_type
        ):
            raise ValueError(
                "'date', 'newDeliveryBuilding', 'newDeliveryFloor'"
                " and 'mealType' parameters must specified."
            )

        self.new_delivery_building = new_delivery_building
        self.new_delivery_floor = new_delivery_floor
        self.meal_type = meal_type

        if meal_type not in m.MealTypeChoices.values:
            raise ValueError("Invalid 'mealType' value")

        self.date = validate_date(date)
        if not self.date:
            raise ValueError("Invalid 'date' value.")

    def _validate_building(self):
        """
        Validating provided building and floor via 'available_buildings'.
        """

        if not self.available_buildings:
            raise ValueError("'buildings' parameter is empty!")

        valid = False
        for building, floors in self.available_buildings.items():
            if self.new_delivery_building != building:
                continue

            elif self.new_delivery_floor not in floors:
                self.message = "طبقه انتخابی شما در سیستم موجود نمی‌باشد."
                raise ValueError(
                    "'newDeliveryFloor' value does not exists in available"
                    " choices."
                )
            valid = True

        if not valid:
            self.message = "ساختمان انتخابی شما در سیستم موجود نمی‌باشد."
            raise ValueError(
                "'newDeliveryBuilding' value does not exists in available"
                " choices."
            )

    def _validate_order_items(self):
        """
        Checking if the user has submitted an order in provided date,
        then checking if the requested building is not the same.

        Will store order object in 'self.order' after validation.
        """

        current_order = m.Order.objects.filter(
            Personnel=self.user.Personnel,
            DeliveryDate=self.date,
            MealType=self.meal_type,
        ).first()

        if current_order and (
            current_order.DeliveryBuilding == self.new_delivery_building
            and current_order.DeliveryFloor == self.new_delivery_floor
        ):
            self.message = (
                "سفارش روز مورد نظر با ساختمان داده شده یکسان است و نیازی به"
                " تغییر نیست."
            )
            raise ValueError(
                "Your order is already submitted with provided building."
            )

        self.order = current_order

    def _validate_date(self):
        """
        Checking if the requested date is valid for action.
        """

        date_obj = create_jdate_object(self.date)
        deadline: s.Deadline = get_specific_deadline(
            weekday=date_obj.weekday(),
            meal_type=self.meal_type,
            deadline=s.Deadline,
        )
        now = localnow()

        is_valid = is_date_valid_for_action(
            now, self.date, deadline.Days, deadline.Hour
        )

        if not is_valid:
            self.message = "مهلت عوض کردن ساختمان تحویل سفارش تمام شده است."
            raise ValueError(
                "Deadline for changing delivery building is over."
            )

    def change_delivery_place(self):
        """
        Changing personnel's 'DeliveryBuilding' and 'DeliveryFloor' value
        in requested date, also logging the action.

        Will also change the cached data in 'User' table.
        """

        personnel = self.user.Personnel
        m.OrderItem.objects.filter(
            Personnel=self.user.Personnel,
            DeliveryDate=self.date,
            Item__MealType=self.meal_type,
        ).update(
            DeliveryBuilding=self.new_delivery_building,
            DeliveryFloor=self.new_delivery_floor,
        )

        # manual log insertion
        # todo doc
        m.ActionLog.objects.log(
            m.ActionLog.ActionTypeChoices.UPDATE,
            personnel,
            f"Delivery place has changed to {self.new_delivery_building}  {self.new_delivery_floor} "
            f"for {self.date} and meal type {self.meal_type}",
            m.OrderItem,
            None,
            (
                dict(
                    DeliveryBuilding=self.order.DeliveryBuilding,
                    DeliveryFloor=self.order.DeliveryFloor,
                )
                if self.order
                else None
            ),
            self.admin_user,
            manipulation_reason=self.reason,
            manipulation_reason_comment=self.comment,
        )

        user = m.User.objects.get(Personnel=personnel)
        user.LastDeliveryBuilding = self.new_delivery_building
        user.LastDeliveryFloor = self.new_delivery_floor
        user.save()

    def validated_data(self) -> dict[str, str]:
        return dict(
            delivery_building=self.new_delivery_building,
            delivery_floor=self.new_delivery_floor,
        )
