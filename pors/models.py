"""Before making any changes, I would like you to read all project documents.

Under no circumstances should operations be performed manually at the
database level. This is because the log is not stored in the ActionLog
table, and such behavior has consequences for the developer. Operations
should be performed through the specialized admin panel  (not referring
to the Django admin panel but a custom-designed panel).

Note that, in addition to these models, some database views are also
used in this project, and you can find its code in /pors/SQLs

Contracts:

The date should be stored in the database as a solar(shamsi) date and with
the Charfield data type.

Any change in one of the states that includes data in the database
should be recorded in the ActionLog table.

Prices are in Toman everywhere.
"""

from threading import Thread

from django.core.mail import send_mail
from django.db import models
from django.forms.models import model_to_dict


class Logger(models.Model):
    # todo doc
    def save(self, *args, **kwargs):
        user = kwargs.pop("user", "SYSTEM")
        log_msg = kwargs.pop("log", None)
        admin = kwargs.pop("admin", None)
        reason = kwargs.pop("reason", None)
        comment = kwargs.pop("comment", None)

        if self._state.adding:
            action_type = ActionLog.ActionTypeChoices.CREATE
            old_data = None
        else:
            action_type = ActionLog.ActionTypeChoices.UPDATE
            old_instance = self.__class__.objects.get(pk=self.pk)
            old_data = model_to_dict(old_instance)

        super().save(*args, **kwargs)

        model = self._meta.model
        record_id = self.id

        ActionLog.objects.log(
            action_type=action_type,
            log_msg=log_msg,
            model=model,
            record_id=record_id,
            old_data=old_data,
            user=user,
            admin=admin,
            reason=reason,
            comment=comment,
        )

    def delete(self, *args, **kwargs):
        user = kwargs.pop("user", "SYSTEM")
        log_msg = kwargs.pop("log", None)
        admin = kwargs.pop("admin", None)
        reason = kwargs.pop("reason", None)
        comment = kwargs.pop("comment", None)
        old_data = model_to_dict(self)

        record_id = self.id
        model = self._meta.model

        super().delete(*args, **kwargs)

        ActionLog.objects.log(
            action_type=ActionLog.ActionTypeChoices.DELETE,
            log_msg=log_msg,
            model=model,
            record_id=record_id,
            old_data=old_data,
            user=user,
            admin=admin,
            reason=reason,
            comment=comment,
        )

    class Meta:
        abstract = True


class User(models.Model):
    """This table is used for auth purposes"""

    Personnel = models.CharField(max_length=250)
    FullName = models.CharField(max_length=250)
    Profile = models.CharField(max_length=500, null=True, blank=True)

    # Change this to True if a personnel is admin
    IsAdmin = models.BooleanField(default=False)

    Token = models.CharField(max_length=64)
    ExpiredAt = models.CharField(max_length=10)

    # todo
    IsActive = models.BooleanField(default=True)

    # HR ConstValue Table Code (For Cache purposes)
    LastDeliveryBuilding = models.CharField(
        max_length=250, null=True, blank=True
    )
    LastDeliveryFloor = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self) -> str:
        return self.Personnel

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["Personnel"], name="unique_personnel"
            )
        ]


class SystemSetting(models.Model):
    """System Variables
    For example, instead of going to the IIS to take  it offline, we change
    the field in this table from 1 to 0, and in this way, the system cannot
    be accessed anymore.

    In general, all the variables below should undergo changes through the
    database.

    All these actions have been taken to provide a better user experience
    with the current system.

    Note that only one record should be created in this table.
    """

    # In case the order panel is closed, a message indicating unavailability
    # is shown to the user, and requests towards the server are not processed.
    IsSystemOpenForPersonnel = models.BooleanField(default=True)
    IsSystemOpenForAdmin = models.BooleanField(default=True)

    # During system updates, enable this option to inform the user that the
    # system is undergoing an update, and the ability to place orders is not
    # available.
    # todo
    SystemUpdating = models.BooleanField(default=False)

    # Does the system provide lunch-related services or not?
    IsSystemOpenForLaunchSubmission = models.BooleanField(default=False)

    # Does the system provide breakfast-related services or not?
    IsSystemOpenForBreakfastSubmission = models.BooleanField(default=True)


class Holiday(models.Model):
    """
    On official holidays of the country, operations other than Read are
    not typically performed on this table. It is likely that the date of
    official holidays in the country will be entered into this table year
    by year.

    So far, the holidays for the year 1402 have been entered into the table
    """

    HolidayDate = models.CharField(max_length=10)

    def __str__(self) -> str:
        return self.HolidayDate


class Category(models.Model):
    """The categorization of orderable items is placed in this table. Note
    that each orderable item can belong to a category.

    For example,
    a cutlery set can also be placed in the 'Additions' category.
    a NoonPanir can also be placed in the 'Sobune' category.
    a Nushabe can aslo be placed in the 'Nushidani' category.
    and so on...
    """

    CategoryName = models.CharField(max_length=300)
    IsPrimary = models.BooleanField(default=False)

    def __str__(self):
        return self.CategoryName


class Subsidy(models.Model):
    """Subsidy or the share of Fanavaran from the order on a daily basis.

    Points related to the company's subsidy allocation:

    1. The subsidy is allocated on a daily basis to the order, and its
    accumulation is not possible.

    2. If the individual places an order with an amount less than the
    subsidy limit, nothing will be refunded from the Fanavarans' share.


       id   fromDate        untilDate      amount
       -----------------------------------------
       1    1402/02/05      1402/02/12     12
       2    1402/02/13      null           15

    Note 1: On the 5th and 12th days of Ordibehesht month, there is an
    allocation of 12 subsidies.

    Note 2: The column with a null 'untilDate' indicates the current
    subsidy share
    """

    # Fanavarans' share
    Amount = models.PositiveIntegerField()

    FromDate = models.CharField(max_length=10)
    UntilDate = models.CharField(max_length=10, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["UntilDate"], name="untildate_unique"
            )
        ]


class ItemProvider(models.Model):
    Title = models.CharField(max_length=50)

    def __str__(self):
        return self.Title


class MealTypeChoices(models.TextChoices):
    """To determine the serving time of a meal, we use the following
    choices.

    Note: In case of changing the codes for meals, the corresponding
    code in the front-end must be rewritten too!!!! So, be cautious,
    my friend
    """

    BREAKFAST = "BRF", "صبحانه"
    LAUNCH = "LNC", "ناهار"


class Item(models.Model):
    """Anything that can be ordered may include food, beverages, cutlery
    sets, etc.
    """

    class MealTypeChoices(models.TextChoices):
        """To determine the serving time of a meal, we use the following
        choices.

        Note: In case of changing the codes for meals, the corresponding
        code in the front-end must be rewritten too!!!! So, be cautious,
        my friend
        """

        BREAKFAST = "BRF", "صبحانه"
        LAUNCH = "LNC", "ناهار"

    ItemName = models.CharField(max_length=500)
    Category = models.ForeignKey("Category", on_delete=models.CASCADE)
    MealType = models.CharField(
        choices=MealTypeChoices.choices,
        default=MealTypeChoices.BREAKFAST,
        max_length=3,
    )
    ItemDesc = models.TextField(blank=True, null=True)

    # todo
    IsActive = models.BooleanField(default=True, help_text="")

    # If no image is uploaded, the system automatically sets a default image
    Image = models.ImageField(
        upload_to="media/items/",
        null=True,
        blank=True,
    )

    # This field should not be modified by the admin or even the DBA.
    # Changes to this field should occur when adding a new record to the
    # ItemPriceHistory table
    CurrentPrice = models.PositiveIntegerField()

    ItemProvider = models.ForeignKey(
        "ItemProvider", on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return self.ItemName


class Deadlines(Logger):
    # todo doc

    WeekDay = models.PositiveSmallIntegerField()
    MealType = models.CharField(choices=MealTypeChoices.choices, max_length=3)
    Days = models.PositiveSmallIntegerField(
        default=0,
    )
    Hour = models.PositiveSmallIntegerField(
        default=0,
    )
    weekday_persian = {
        0: "شنبه",
        1: "یکشنبه",
        2: "دوشنبه",
        3: "سه‌شنبه",
        4: "چهارشنبه",
        5: "پنج‌شنبه",
        6: "جمعه",
    }

    def update(new_deadlines: list[dict], admin_user: User):
        changed_deadlines: list[dict] = list()
        old_data = dict()

        for deadline in new_deadlines["deadlines"]:
            changed = False
            record = deadline["id"]
            prev_days = record.Days
            prev_hours = record.Hour

            for key, value in deadline.items():
                if key == "id":
                    continue
                if getattr(record, key) != value:
                    changed = True
                    setattr(record, key, value)
            if changed:
                changed_deadlines.append(record)
                old_data[record.id] = (prev_days, prev_hours)

        Deadlines.objects.bulk_update(changed_deadlines, ["Days", "Hour"])

        for deadline in changed_deadlines:
            ActionLog.objects.log(
                action_type=ActionLog.ActionTypeChoices.UPDATE,
                user=admin_user,
                log_msg=f"Deadline for weekday {deadline.WeekDay} changed",
                record_id=deadline.id,
                old_data={
                    "Days": old_data[deadline.id][0],
                    "Hour": old_data[deadline.id][1],
                },
            )
            if new_deadlines["notifyPersonnel"]:
                deadline.send_change_notif()

    def send_change_notif(self):
        emails = list(
            User.objects.filter(IsActive=True).values_list(
                "Personnel", flat=True
            )
        )
        message = (
            f"مهلت ثبت سفارش روز {Deadlines.weekday_persian[self.WeekDay]} "
            f"به {self.Days} روز و {self.Hour} ساعت تغییر یافت."
        )

        thread = Thread(
            target=send_mail,
            args=("تغییر مهلت ثبت سفارش", message, "pors_admin@eit", emails),
        )
        thread.start()


class Order(models.Model):
    """Personnel Orders View"""

    Id = models.PositiveIntegerField(primary_key=True)
    Personnel = models.CharField(max_length=250)
    FirstName = models.CharField(max_length=250)
    LastName = models.CharField(max_length=250)
    DeliveryDate = models.CharField(max_length=10)
    HasPrimary = models.BooleanField()
    SubsidyCap = models.PositiveIntegerField()
    TotalPrice = models.PositiveIntegerField()

    # HR ConstValue Table Code
    DeliveryBuilding = models.CharField(max_length=250)
    DeliveryFloor = models.CharField(max_length=250)
    DeliveryBuildingPersian = models.CharField(max_length=250)
    DeliveryFloorPersian = models.CharField(max_length=250)
    MealType = models.CharField(max_length=3)

    # PersonnelDebt = TotalPrice - SubsidyCap
    # Note that PersonnelDebt will never be negative
    PersonnelDebt = models.PositiveIntegerField()

    # The amount spent by Fanavaran
    SubsidySpent = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = "Order"


class FoodProviderOrdering(models.Model):
    """Food Provider Ordering List View"""

    Id = models.PositiveIntegerField(primary_key=True)
    ItemName = models.CharField(max_length=250)
    MealType = models.CharField(max_length=250)
    PricePerOne = models.PositiveIntegerField()
    ItemTotalCount = models.PositiveIntegerField()
    DeliveryDate = models.CharField(max_length=10)
    DeliveryBuilding = models.CharField(max_length=10)
    FoodProvider = models.PositiveIntegerField()
    FoodProviderPersian = models.CharField(max_length=10)
    DeliveryBuildingPersian = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = "FoodProviderOrdering"


class OrderItem(Logger):
    """The ordered items for personnel"""

    CreatedAt = models.DateTimeField(auto_now_add=True)
    ModifiedAt = models.DateTimeField(auto_now=True, null=True)
    Personnel = models.CharField(max_length=250)
    DeliveryDate = models.CharField(max_length=10)
    Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    Quantity = models.PositiveSmallIntegerField(default=1)

    # HR ConstValue Table Code
    DeliveryBuilding = models.CharField(max_length=250)
    DeliveryFloor = models.CharField(max_length=250)

    # Taken from the current item price (Item/CurrentPrice) and entered here.
    # Technical redundancy
    PricePerOne = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["Personnel", "DeliveryDate", "Item"],
                name="unique_item_date_personnel",
            ),
        ]


class ItemsOrdersPerDay(models.Model):
    """The following view shows how many daily items have been ordered
    until now. If an item has not been ordered, it returns 0 as TotalOrders

    In simpler terms, this view shows how many people have ordered a
    particular item, and TotalOrders indicates that count.
    """

    Id = models.PositiveIntegerField(primary_key=True)
    Item = models.PositiveIntegerField()
    Date = models.CharField(max_length=10)
    TotalOrders = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = "ItemsOrdersPerDay"


class ItemPriceHistory(models.Model):
    """This table keeps the price change history of items.

    Note that the start and end date of a record are considered with the
    same price.

    Note 2 This tabel has trigger on DB level # todo
    """

    Item = models.ForeignKey(
        Item, on_delete=models.CASCADE, null=False, blank=False
    )

    Price = models.PositiveIntegerField()
    FromDate = models.CharField(max_length=10)
    UntilDate = models.CharField(max_length=10, null=True)

    def __str__(self):
        return f"{self.Item.ItemName} {self.Price}"


class DailyMenuItem(Logger):
    """
    It specifies information about the item available for order on each day
    """

    AvailableDate = models.CharField(max_length=10)
    Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    IsActive = models.BooleanField(default=True)  # todo

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["AvailableDate", "Item"],
                name="unique_AvailableDate_Item",
            )
        ]


class ActionLog(models.Model):
    """Every action performed in this system is stored in this table.
    Models that inherit from Logger have default CRUD operations logged for
    them

    ActionDesc: The main explanation, stating what data has changed during
    the occurrence of this action, or in general, what has happened, should
    be transparently expressed. The design of the message structure is the
    responsibility of the developer.

    AdminActionReason: The system, especially the order
    registration/cancellation and modification process, is designed to
    eliminate the need for admin intervention. If, in any way, the admin (
    administrative or the central systems team) has made changes and
    intervened in this process, the reason for this action must be clearly
    stated in this field.

    An important note about the AdminActionReason field is that it is not
    mandatory to have a value at the database level (null=True), and the
    developer must handle it (whenever the admin is in the process of
    making changes, this field must be required).
    """

    class LogManager(models.Manager):
        def log(
            self,
            action_type,
            user="SYSTEM",
            log_msg=None,
            model=None,
            record_id=None,
            old_data: dict = None,
            admin=None,
            reason=None,
            comment=None,
        ):
            table_name = model._meta.model_name if model else None
            return self.create(
                User=user,
                TableName=table_name,
                ReferencedRecordId=record_id,
                ActionType=action_type,
                ActionDesc=log_msg,
                OldData=old_data,
                Admin=admin,
                ManipulationReason=reason,
                ManipulationReasonComment=comment,
            )

    class ActionTypeChoices(models.TextChoices):
        CREATE = "C", "create"
        READ = "R", "read"
        UPDATE = "U", "update"
        DELETE = "D", "delete"

    ActionAt = models.DateTimeField(auto_now_add=True)

    # If the system automatically logs an action, the user should be
    # recorded as  'SYSTEM'
    User = models.CharField(max_length=250)
    TableName = models.CharField(max_length=50, null=True)
    ReferencedRecordId = models.PositiveIntegerField(null=True)
    ActionType = models.CharField(
        max_length=1, choices=ActionTypeChoices.choices
    )

    # Summary of what happened in this log for system supporter
    # (in the most human-readable word)
    ActionDesc = models.CharField(max_length=1000, null=True)
    OldData = models.JSONField(null=True)

    Admin = models.CharField(max_length=250, null=True)
    ManipulationReasonComment = models.CharField(max_length=250, null=True)
    ManipulationReason = models.ForeignKey(
        "AdminManipulationReason", on_delete=models.SET_NULL, null=True
    )

    objects = LogManager()

    class Meta:
        ordering = ["-ActionAt"]


class PersonnelDailyReport(models.Model):
    Id = models.PositiveIntegerField(primary_key=True)
    NationalCode = models.CharField(max_length=10)
    Personnel = models.CharField(max_length=250)
    FirstName = models.CharField(max_length=250)
    LastName = models.CharField(max_length=250)
    ItemName = models.CharField(max_length=500)
    ItemId = models.IntegerField()
    Quantity = models.PositiveSmallIntegerField()
    DeliveryDate = models.CharField(max_length=10)
    DeliveryBuilding = models.CharField(max_length=250)
    DeliveryFloor = models.CharField(max_length=250)
    DeliveryBuildingPersian = models.CharField(max_length=250)
    DeliveryFloorPersian = models.CharField(max_length=250)

    class Meta:
        managed = False
        db_table = "PersonnelDailyReport"

    def __str__(self) -> str:
        return self.Personnel


class TempUsers(models.Model):
    UserName = models.CharField(max_length=100, primary_key=True)
    FirstName = models.CharField(max_length=200)
    LastName = models.CharField(max_length=200)
    NationalCode = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = "Users"


class HR_constvalue(models.Model):
    Caption = models.CharField(max_length=50)
    Code = models.CharField(max_length=100)
    Parent = models.ForeignKey(
        "HR_constvalue",
        verbose_name="شناسه پدر",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    IsActive = models.BooleanField(default=True)
    OrderNumber = models.PositiveSmallIntegerField(
        null=True, blank=True, default=1
    )
    ConstValue = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.Caption

    @property
    def ParentTitle(self):
        return self.Parent.Caption

    class Meta:
        db_table = "HR_constvalue"
        verbose_name = "مقدار ثابت"
        verbose_name_plural = "مقادیر ثابت"
        ordering = ["Parent_id", "OrderNumber"]


class AdminManipulationReason(models.Model):
    Title = models.CharField(max_length=350)
    ReasonCode = models.CharField(max_length=50, null=True)
