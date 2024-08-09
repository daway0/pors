import json
from typing import Optional, Union

import jdatetime
from django.db import IntegrityError, transaction
from django.db.models import F, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from django.urls import reverse

from . import models as m
from . import serializers as s
from .utils import (
    HR_HOST,
    HR_SCHEME,
    SERVER_PORT,
    create_jdate_object,
    execute_raw_sql_with_params,
    first_and_last_day_date,
    get_specific_deadline,
    localnow,
    send_email_notif,
    split_dates,
    split_json_dates,
    str_date_to_jdate,
    validate_date,
)


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


def validate_package_submission(
    validator: Union["ValidateOrder", "ValidateBreakfast"],
):
    """
    Validating submission based on several conditions:
        Package must exists in database
        There must be a 'DailyMenuPackage' record for requested
            date and package.
        User should not ordered package items more than its capacity.

    Args:
        validator: validator class which has all of our dependencies.

    Raises:
        ValueError: if any of beyond validations gets violated.
    """

    package = m.Package.objects.filter(
        pk=validator.package, packageitem__Item=validator.item
    ).first()
    if package is None:
        raise ValueError("requested item and package does not exists")

    total_orders = m.OrderItem.objects.filter(
        Personnel=validator.user,
        DeliveryDate=validator.date,
        PackageItem__Package=package,
    ).aggregate(TotalOrders=Coalesce(Sum("Quantity"), 0))
    if total_orders["TotalOrders"] >= package.FreeItemCount:
        validator.message = "ظرفیت سفارش پکیج برای شما تمام شده است."
        raise ValueError("Package cap is reached.")

    validator.package = package


def insert_package_record(
    validator: Union["ValidateOrder", "ValidateBreakfast"], note: Optional[str]
):
    package = m.Item.objects.filter(Package=validator.package).first()

    package_orders = m.OrderItem.objects.filter(
        Personnel=validator.user.Personnel,
        DeliveryDate=validator.date,
        Item=package,
    ).first()
    if package_orders is not None:
        package_orders.Quantity += 1
        package_orders.save()
    else:
        m.OrderItem(
            Personnel=validator.user.Personnel,
            DeliveryDate=validator.date,
            DeliveryBuilding=validator.user.LastDeliveryBuilding,
            DeliveryFloor=validator.user.LastDeliveryFloor,
            Item=package,
            Quantity=1,
            PricePerOne=0,
            Note=note,
        ).save(
            log=(
                f"Package item {package.ItemName} just added to order for"
                f" {validator.date}"
            ),
            user=validator.user.Personnel,
            admin=validator.admin_user,
            reason=validator.reason,
            comment=validator.comment,
        )


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

        self.reason = s_data.validated_data["reason"]
        self.comment = s_data.validated_data.get("comment")

    def _is_admin(self) -> bool:
        if not self.admin_user:
            return False
        return True

    def _send_email_notif(self, context: dict):
        if not self._is_admin() or not self.user.EmailNotif:
            return

        date: str = context["delivery_date"]
        weekday = str_date_to_jdate(date).weekday()
        context["weekday"] = weekday

        message = render_to_string("emails/adminAction.html", context)
        send_email_notif(
            "تغییر سفارش",
            message,
            [self.user.EmailAddress],
            m.EmailReason.ADMIN_ACTION,
        )


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

    def __init__(self, serializer_data: dict, user: m.User) -> None:
        self.user = user
        self.error = ""
        self.date: str = serializer_data["date"]
        self.item: m.Item = serializer_data["item"]

    def is_valid(self) -> bool:
        """
        Applying validations to the request data.
        if the request was not valid, will return false and
        store error result inside `self.error`.

        Returns:
            bool: was the request data valid or not.
        """

        try:
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
        order_item: OrderItem instance if user has already ordered
            the requested item.
        menu_item: DailyMenuItem instance if its available.
        package: item instance of package if order is for a specific package.
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
        self, serializer_data: dict, user: m.User, override_user: m.User
    ) -> None:
        super().__init__(user, override_user)
        self.message: str = ""
        self.error = ""
        self.date: str = serializer_data["date"]
        self.item: m.Item = serializer_data["item"]
        self.order_item: m.OrderItem = m.OrderItem.objects.none()
        self.menu_item: m.DailyMenuItem = m.DailyMenuItem.objects.none()
        self.package: m.Item = serializer_data.get("package")

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
            if create:
                self._validate_item_submission()
                self._validate_default_delivery_building()
                self._validate_package_submission()
            elif remove:
                self._validate_item_removal()

            if not self._is_admin():
                self._validate_date()
                create and self._validate_primary_item()
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

        menu_item = (
            m.DailyMenuItem.objects.filter(
                Item=self.item,
                AvailableDate=self.date,
                IsActive=True,
                Item__IsActive=True,
                Item__Package__isnull=True,
            )
            .exclude(Item__MealType=m.Item.MealTypeChoices.BREAKFAST)
            .first()
        )
        if not menu_item:
            self.message = "آیتم مورد نظر در تاریخ داده شده موجود نمی‌باشد."
            raise ValueError("item is not available in corresponding date.")

        if (
            menu_item.TotalOrdersLeft is not None
            and menu_item.TotalOrdersLeft == 0
        ):
            self.message = "آیتم مورد نظر ناموجود می‌باشد."
            raise ValueError("item's maximum orders is reached.")

        self.item = m.Item.objects.filter(pk=self.item).first()
        self.menu_item = menu_item

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

    def _validate_package_submission(self):
        if self.package is None:
            return

        validate_package_submission(self)

    def _validate_item_removal(self):
        """
        Checking if the personnel has ordered the specified item
            on provided date.
        """

        order_item = m.OrderItem.objects.filter(
            Personnel=self.user.Personnel,
            DeliveryDate=self.date,
            Item=self.item,
            PackageItem__Package=self.package if self.package else None,
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

    def _validate_primary_item(self):
        """
        Checking if user has already ordered a primary item, if so,
        they are not allowed to submit more.

        Validation returns if the requested item is not primary,
        or the request is for removing order.
        """
        if not self.item.Category.IsPrimary:
            return

        current_order = m.Order.objects.filter(
            DeliveryDate=self.date,
            Personnel=self.user,
            MealType=m.MealTypeChoices.LAUNCH,
        ).first()
        if current_order is not None and current_order.HasPrimary:
            self.message = "شما نمی‌توانید بیشتر 1 غذای اصلی سفارش دهید."
            raise ValueError("You cannot submit more than 1 primary item.")

    def create_order(self):
        """
        Submitting order.
        If the personnel has already ordered that item on the requested date,
        will instead increase its quantity by 1.

        Warnings:
            DO NOT use this method before checking `is_valid` method.

        Raises:
            ValueError: Can raise in situations where multiple users are
                submiting order for a same item at one, and the item's order
                limit is at edge. to avoid race conditions, database won't
                allow for negative values, therefore an IntegrityError
                will be raised.
        """

        if self.error:
            raise ValueError(
                "This method is only available if provided data is valid."
            )

        link = f"{HR_SCHEME}://{HR_HOST}:{SERVER_PORT}{reverse('pors:personnel_panel')}?order={self.date.replace('/', '')}{self.item.MealType}"

        try:
            with transaction.atomic():
                self.menu_item.TotalOrdersLeft = F("TotalOrdersLeft") - 1
                self.menu_item.save()

                package_item = (
                    m.PackageItem.objects.filter(
                        Item=self.item, Package=self.package
                    ).first()
                    if self.package
                    else None
                )

                instance = m.OrderItem.objects.filter(
                    Personnel=self.user.Personnel,
                    DeliveryDate=self.date,
                    Item=self.item,
                    PackageItem=package_item,
                ).first()

                note = m.OrderItem.objects.filter(
                    DeliveryDate=self.date,
                    Personnel=self.user,
                    Note__isnull=False,
                ).first()

                if self.package is not None:
                    insert_package_record(
                        self, note.Note if note is not None else None
                    )

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

                    self._send_email_notif(
                        {
                            "full_name": self.user.FullName,
                            "link": link,
                            "delivery_date": self.date,
                            "meal_type": m.MealTypeChoices.LAUNCH.label,
                            "increase_quantity_item": self.item,
                            "report": m.PersonnelDailyReport.objects.filter(
                                Personnel=self.user,
                                DeliveryDate=self.date,
                                MealType=m.MealTypeChoices.LAUNCH,
                            ),
                        },
                    )

                else:
                    new_item = m.OrderItem(
                        Personnel=self.user.Personnel,
                        DeliveryDate=self.date,
                        DeliveryBuilding=self.user.LastDeliveryBuilding,
                        DeliveryFloor=self.user.LastDeliveryFloor,
                        Item=self.item,
                        PackageItem=package_item,
                        Quantity=1,
                        PricePerOne=(
                            self.item.CurrentPrice
                            if self.package is None
                            else 0
                        ),
                        Note=note.Note if note is not None else None,
                    )
                    new_item.save(
                        log=(
                            f"Launch Item {self.item.ItemName} just added to order for"
                            f" {self.date}"
                        ),
                        user=self.user.Personnel,
                        admin=self.admin_user,
                        reason=self.reason,
                        comment=self.comment,
                    )
                    self._send_email_notif(
                        {
                            "full_name": self.user.FullName,
                            "link": link,
                            "delivery_date": self.date,
                            "meal_type": m.MealTypeChoices.LAUNCH.label,
                            "new_item": self.item,
                            "report": m.PersonnelDailyReport.objects.filter(
                                Personnel=self.user,
                                DeliveryDate=self.date,
                                MealType=m.MealTypeChoices.LAUNCH,
                            ),
                        },
                    )
        except IntegrityError:
            self.message = "آیتم مورد نظر ناموجود می‌باشد."
            raise ValueError("item's maximum orders is reached.")

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

        link = f"{HR_SCHEME}://{HR_HOST}:{SERVER_PORT}{reverse('pors:personnel_panel')}?order={self.date.replace('/', '')}{self.item.MealType}"

        with transaction.atomic():
            m.DailyMenuItem.objects.filter(
                Item=self.item, AvailableDate=self.date
            ).update(TotalOrdersLeft=F("TotalOrdersLeft") + 1)

            if self.package is not None:
                package = m.Item.objects.filter(Package=self.package).first()
                package_order = m.OrderItem.objects.filter(
                    Personnel=self.user,
                    Item=package,
                    DeliveryDate=self.date,
                ).first()
                if package_order.Quantity > 1:
                    package_order.Quantity -= 1
                    package_order.save()
                else:
                    package_order.delete(
                        log=(
                            f"Package item {package.ItemName} removed from order for"
                            f" {self.date}"
                        ),
                        user=self.user.Personnel,
                        admin=self.admin_user,
                        reason=self.reason,
                        comment=self.comment,
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
                self._send_email_notif(
                    {
                        "full_name": self.user.FullName,
                        "link": link,
                        "delivery_date": self.date,
                        "meal_type": self.item.get_MealType_display(),
                        "decrease_quantity_item": self.item,
                        "report": m.PersonnelDailyReport.objects.filter(
                            Personnel=self.user,
                            DeliveryDate=self.date,
                            MealType=self.item.MealType,
                        ),
                    },
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
                self._send_email_notif(
                    {
                        "full_name": self.user.FullName,
                        "link": link,
                        "delivery_date": self.date,
                        "meal_type": self.item.get_MealType_display(),
                        "removed_item": self.item,
                        "report": m.PersonnelDailyReport.objects.filter(
                            Personnel=self.user,
                            DeliveryDate=self.date,
                            MealType=self.item.MealType,
                        ),
                    },
                )


class ValidateBreakfast(OverrideUserValidator):
    """
    Validating breakfast order submission and submitting order
        if data was valid.
    The data will pass several validation before submission.

    Attributes:
        data: serializer validated data.
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
        self, serializer_data: dict, user: m.User, override_user: m.User
    ) -> None:
        super().__init__(user, override_user)
        self.message: str = ""
        self.error: str = ""
        self.date: str = serializer_data["date"]
        self.item: m.Item = serializer_data["item"]
        self.menu_item: m.DailyMenuItem = m.DailyMenuItem.objects.none()
        self.package: m.Package = serializer_data.get("package")

    def is_valid(self):
        """
        Applying validations to the request data.
        if the request was not valid, will return false and
        store error result inside `self.error`.

        Returns:
            bool: was the request data valid or not.
        """

        try:
            self._validate_item()
            self._validate_default_delivery_building()
            self._validate_package_submission()

            if not self._is_admin():
                self._validate_date()
                self._validate_order()
            else:
                self.validate_admin_request(self.data)

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

        menu_item = m.DailyMenuItem.objects.filter(
            Item=self.item,
            AvailableDate=self.date,
            IsActive=True,
            Item__IsActive=True,
            Item__MealType=m.Item.MealTypeChoices.BREAKFAST,
            Item__Package__isnull=True,
        ).first()
        if not menu_item:
            self.message = "آیتم مورد نظر فعال نمی‌باشد."
            raise ValueError("Item is not valid.")
        if (
            menu_item.TotalOrdersLeft is not None
            and menu_item.TotalOrdersLeft == 0
        ):
            self.message = "آیتم مورد نظر ناموجود می‌باشد."
            raise ValueError("item's maximum orders is reached.")

        self.item = m.Item.objects.filter(pk=self.item).first()
        self.menu_item = menu_item

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

    def _validate_package_submission(self):
        if self.package is None:
            return

        validate_package_submission(self)

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

        breakfast_order = m.Order.objects.filter(
            DeliveryDate=self.date,
            Personnel=self.user,
            MealType=m.MealTypeChoices.BREAKFAST,
        )
        if breakfast_order.exists():
            self.message = "امکان سفارش حداکثر 1 عدد آیتم صبحانه‌ای وجود دارد."
            raise ValueError(
                "Personnel cannot submit more than 1 breakfast" " item(s)."
            )

    def create_breakfast_order(self):
        """
        Creating breakfast order for personnel

        Warnings:
            DO NOT use this method before checking `is_valid` method.
        Raises:
            ValueError: Can raise in situations where multiple users are
                submiting order for a same item at one, and the item's order
                limit is at edge. to avoid race conditions, database won't
                allow for negative values, therefore an IntegrityError
                will be raised.
        """

        if self.error:
            raise ValueError(
                "This method is only available if provided data is valid."
            )

        link = f"{HR_SCHEME}://{HR_HOST}:{SERVER_PORT}{reverse('pors:personnel_panel')}?order={self.date.replace('/', '')}{self.item.MealType}"

        try:
            with transaction.atomic():
                self.menu_item.TotalOrdersLeft = F("TotalOrdersLeft") - 1
                self.menu_item.save()
                instance = m.OrderItem.objects.filter(
                    Personnel=self.user.Personnel,
                    DeliveryDate=self.date,
                    Item=self.item,
                ).first()
                note = m.OrderItem.objects.filter(
                    DeliveryDate=self.date,
                    Personnel=self.user,
                    Note__isnull=False,
                ).first()

                if self.package is not None:
                    insert_package_record(
                        self, note.Note if note is not None else None
                    )

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
                    self._send_email_notif(
                        {
                            "full_name": self.user.FullName,
                            "link": link,
                            "delivery_date": self.date,
                            "meal_type": m.MealTypeChoices.BREAKFAST.label,
                            "increase_quantity_item": self.item,
                            "report": m.PersonnelDailyReport.objects.filter(
                                Personnel=self.user,
                                DeliveryDate=self.date,
                                MealType=m.MealTypeChoices.BREAKFAST,
                            ),
                        },
                    )

                else:
                    m.OrderItem(
                        Personnel=self.user.Personnel,
                        DeliveryDate=self.date,
                        DeliveryBuilding=self.user.LastDeliveryBuilding,
                        DeliveryFloor=self.user.LastDeliveryFloor,
                        Item=self.item,
                        PackageItem=(
                            m.PackageItem.objects.filter(
                                Item=self.item, Package=self.package
                            ).first()
                            if self.package
                            else None
                        ),
                        PricePerOne=(
                            self.item.CurrentPrice
                            if self.package is None
                            else 0
                        ),
                        Note=note.Note if note is not None else None,
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
                    self._send_email_notif(
                        {
                            "full_name": self.user.FullName,
                            "link": link,
                            "delivery_date": self.date,
                            "meal_type": m.MealTypeChoices.BREAKFAST.label,
                            "new_item": self.item,
                            "report": m.PersonnelDailyReport.objects.filter(
                                Personnel=self.user,
                                DeliveryDate=self.date,
                                MealType=m.MealTypeChoices.BREAKFAST,
                            ),
                        },
                    )
        except IntegrityError:
            self.message = "آیتم مورد نظر ناموجود می‌باشد."
            raise ValueError("item's maximum orders is reached.")


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

    def __init__(self, serializer_data: dict, user: m.User) -> None:
        self.data = serializer_data
        self.user = user
        self.message: str = ""
        self.error: str = ""
        self.date: str = ""
        self.item: m.Item = m.Item.objects.none()
        self.total_orders_allowed: Optional[int] = None

    def is_valid(self):
        """
        Applying validations to the request data.
        if the request was not valid, will return false and
        store error result inside `self.error`.

        Returns:
            bool: was the request data valid or not.
        """

        try:
            self.date, self.item, self.total_orders_allowed = (
                self.data["date"],
                self.data["item"],
                self.data.get("totalOrdersAllowed"),
            )
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

        m.DailyMenuItem(
            AvailableDate=self.date,
            Item=self.item,
            TotalOrdersAllowed=self.total_orders_allowed,
            TotalOrdersLeft=self.total_orders_allowed,
        ).save(
            log=(
                f"Item {self.item.ItemName} just added to the menu for"
                f" {self.date}"
            ),
            user=self.user.Personnel,
        )
        if self.item.Package is not None:
            menu_items = [
                m.DailyMenuItem(
                    AvailableDate=self.date,
                    Item=item.Item,
                    TotalOrdersAllowed=self.total_orders_allowed,
                    TotalOrdersLeft=self.total_orders_allowed,
                )
                for item in m.PackageItem.objects.filter(
                    Package=self.item.Package
                )
                .annotate(
                    daily_menu_item=Subquery(
                        m.DailyMenuItem.objects.filter(
                            Q(Item=OuterRef("Item"))
                            & Q(AvailableDate=self.date)
                        ).values("id")
                    )
                )
                .filter(daily_menu_item__isnull=True)
            ]
            package_menu_items = m.DailyMenuItem.objects.bulk_create(
                menu_items
            )
            m.ActionLog.objects.log(
                m.ActionLog.ActionTypeChoices.CREATE,
                self.user,
                f"{[menu_item.Item.ItemName for menu_item in package_menu_items]} items added to menu automatically",
                m.DailyMenuItem,
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
        user: m.User,
        override_user: m.User,
    ) -> None:
        super().__init__(user, override_user)
        self.data = request_data
        self.message: str = ""
        self.error: str = ""
        self.date: str = ""
        self.meal_type: m.MealTypeChoices.value = ""
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

        if not self.new_delivery_building.startswith("Building_"):
            raise ValueError("Invalid building value.")

        valid_building = m.HR_constvalue.objects.filter(
            Code=self.new_delivery_building
        )
        if not valid_building.exists():
            self.message = "ساختمان انتخابی شما در سیستم موجود نمی‌باشد."
            raise ValueError(
                "'newDeliveryBuilding' value does not exists in available"
                " choices."
            )
        valid_floor = m.HR_constvalue.objects.filter(
            Code=self.new_delivery_floor, Parent_id=valid_building.first().pk
        )
        if not valid_floor.exists():
            self.message = "طبقه انتخابی شما در سیستم موجود نمی‌باشد."
            raise ValueError(
                "'newDeliveryFloor' value does not exists in available"
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
        user = m.User.objects.get(Personnel=personnel)
        user.LastDeliveryBuilding = self.new_delivery_building
        user.LastDeliveryFloor = self.new_delivery_floor
        user.save()

        m.OrderItem.objects.filter(
            Personnel=self.user.Personnel,
            DeliveryDate=self.date,
            Item__MealType=self.meal_type,
        ).update(
            DeliveryBuilding=self.new_delivery_building,
            DeliveryFloor=self.new_delivery_floor,
        )
        if self._is_admin():

            qs = m.HR_constvalue.objects.filter(
                Q(Code=self.new_delivery_building)
                | Q(Code=self.new_delivery_floor)
            )
            report = m.PersonnelDailyReport.objects.filter(
                Personnel=self.user,
                DeliveryDate=self.date,
                MealType=self.meal_type,
            )
            self._send_email_notif(
                {
                    "full_name": self.user.FullName,
                    "link": f"{HR_SCHEME}://{HR_HOST}:{SERVER_PORT}{reverse('pors:personnel_panel')}?order={self.date.replace('/', '')}{self.meal_type}",
                    "delivery_date": self.date,
                    "meal_type": m.MealTypeChoices(self.meal_type).label,
                    "building": qs.get(
                        Code=self.new_delivery_building
                    ).Caption,
                    "floor": qs.get(Code=self.new_delivery_floor).Caption,
                    "report": report,
                },
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
            reason=self.reason,
            comment=self.comment,
        )

    def validated_data(self) -> dict[str, str]:
        return dict(
            delivery_building=self.new_delivery_building,
            delivery_floor=self.new_delivery_floor,
        )
