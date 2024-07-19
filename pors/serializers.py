from collections import namedtuple

from rest_framework import serializers

from . import business as b
from . import models as m
from . import utils as u
from .models import User

Deadline = namedtuple("Deadline", "Days Hour")


class AllItemSerializer(serializers.ModelSerializer):
    itemName = serializers.CharField(source="ItemName")
    image = serializers.CharField(source="Image")
    category = serializers.SlugRelatedField(
        slug_field="CategoryName",
        queryset=m.Category.objects.all().values("CategoryName"),
        source="Category",
    )
    currentPrice = serializers.IntegerField(source="CurrentPrice")
    mealType = serializers.CharField(source="get_MealType_display")
    serveTime = serializers.CharField(source="MealType")
    itemDesc = serializers.CharField(source="ItemDesc")
    isActive = serializers.BooleanField(source="IsActive")
    itemProvider = serializers.CharField(source="ItemProvider")

    class Meta:
        model = m.Item
        fields = (
            "id",
            "itemName",
            "image",
            "category",
            "currentPrice",
            "mealType",
            "serveTime",
            "itemDesc",
            "isActive",
            "itemProvider",
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Category
        fields = ("id", "Title")


class HolidaySerializer(serializers.Serializer):
    holidays = serializers.SerializerMethodField()

    def get_holidays(self, obj):
        result = []
        for date in obj.values():
            if date["HolidayDate"] not in result:
                result.append(date["HolidayDate"])
        return result


class ItemOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="Item")
    allowToRemoveMenuItems = serializers.SerializerMethodField()
    orderedBy = serializers.IntegerField(source="TotalOrders")

    def get_allowToRemoveMenuItems(self, obj):
        if obj.TotalOrders > 0:
            return False
        return True


class MenuItemSerializer(serializers.Serializer):
    menuItems = serializers.SerializerMethodField()

    def get_menuItems(self, obj):
        result = []
        current_date_obj = {}
        breakfast_deadlines, launch_deadlines = u.get_deadlines(Deadline)
        breakfast_deadlines: dict[int, Deadline]
        launch_deadlines: dict[int, Deadline]
        now = u.localnow()

        for object in obj:
            serializer = ItemOrderSerializer(
                data={"id": object.Item, "orderedBy": object.TotalOrders},
            ).initial_data
            if current_date_obj.get("date") == object.Date:
                current_date_obj["items"].append(serializer)
            else:
                current_date_obj = {}
                current_date_obj["date"] = object.Date
                weekday = u.create_jdate_object(object.Date).weekday()
                current_date_obj["openForLaunch"] = b.is_date_valid_for_action(
                    now,
                    current_date_obj["date"],
                    launch_deadlines[weekday].Days,
                    launch_deadlines[weekday].Hour,
                )
                current_date_obj["openForBreakfast"] = (
                    b.is_date_valid_for_action(
                        now,
                        current_date_obj["date"],
                        breakfast_deadlines[weekday].Days,
                        breakfast_deadlines[weekday].Hour,
                    )
                )
                current_date_obj["items"] = []
                current_date_obj["items"].append(serializer)
                result.append(current_date_obj)

        return result


class DebtSerializer(serializers.Serializer):
    totalDebt = serializers.IntegerField()


class OrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(source="ItemName")
    currentPrice = serializers.IntegerField(source="CurrentPrice")
    img = serializers.CharField(source="Image")
    category = serializers.IntegerField(source="Category_id")
    description = serializers.CharField(source="ItemDesc")
    quantity = serializers.IntegerField(source="Quantity")
    pricePerItem = serializers.IntegerField(source="PricePerOne")
    note = serializers.CharField(max_length=1000, source="Note")


class OrderSerializer(serializers.Serializer):
    orders = serializers.SerializerMethodField()

    def get_orders(self, obj):
        result = []
        schema = {}
        for object in obj:
            serializer = OrderItemSerializer(object).data
            date = schema.get("orderDate")
            if date == object["DeliveryDate"]:
                u.add_mealtype_building(object, schema)
                schema["orderItems"].append(serializer)
                continue

            schema = {}
            schema["orderDate"] = object["DeliveryDate"]

            u.add_mealtype_building(object, schema)

            schema["orderItems"] = []
            schema["orderItems"].append(serializer)
            schema["orderBill"] = {
                "total": object["TotalPrice"],
                "fanavaran": object["SubsidyCap"],
                "debt": object["PersonnelDebt"],
            }
            result.append(schema)

        return result


class GeneralCalendarSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    firstDayOfWeek = serializers.IntegerField()
    lastDayOfMonth = serializers.IntegerField()
    holidays = serializers.ListField()
    daysWithMenu = serializers.ListField()


class FirstPageSerializer(serializers.Serializer):
    isOpenForAdmins = serializers.BooleanField()
    isOpenForPersonnel = serializers.BooleanField()
    userName = serializers.CharField()
    isAdmin = serializers.BooleanField()
    fullName = serializers.CharField()
    profile = serializers.ImageField()
    buildings = serializers.DictField()
    latestBuilding = serializers.CharField()
    latestFloor = serializers.CharField()
    firstOrderableDate = serializers.DictField()
    totalItemsCanOrderedForBreakfastByPersonnel = serializers.IntegerField()
    godMode = serializers.BooleanField()


class DayWithMenuSerializer(serializers.Serializer):
    day = serializers.CharField(source="AvailableDate")
    ordersNumber = serializers.IntegerField(source="OrderCount")


class ListedDaysWithMenu(serializers.Serializer):
    dates = serializers.SerializerMethodField()

    def get_dates(self, obj):
        result = []
        for date in obj.values():
            if date["AvailableDate"] not in result:
                result.append(date["AvailableDate"])

        return result


class PersonnelSchemaSerializer(serializers.Serializer):
    orderedDays = serializers.ListField()
    totalDebt = serializers.IntegerField()


class MenuItems(serializers.Serializer):
    id = serializers.IntegerField(source="Item_id")


class PersonnelMenuItemSerializer(serializers.Serializer):
    menuItems = serializers.SerializerMethodField()

    def get_menuItems(self, obj):
        result = []
        current_date_obj = {}
        breakfast_deadlines, launch_deadlines = u.get_deadlines(Deadline)
        breakfast_deadlines: dict[int, Deadline]
        launch_deadlines: dict[int, Deadline]
        now = u.localnow()

        # Its set to true if user is admin and accessing another
        # user's panel from his/her side.
        # True means all days are viable for add/remove/changing order.
        bypass_date_limitations = self.context.get("bypass_date_limitations")

        for object in obj:
            serializer = MenuItems(object).data
            if current_date_obj.get("date") == object.get("AvailableDate"):
                current_date_obj["items"].append(serializer)
            else:
                current_date_obj = {}
                current_date_obj["date"] = object.get("AvailableDate")
                weekday = u.create_jdate_object(
                    object.get("AvailableDate")
                ).weekday()
                current_date_obj["openForLaunch"] = (
                    b.is_date_valid_for_action(
                        now,
                        current_date_obj["date"],
                        launch_deadlines[weekday].Days,
                        launch_deadlines[weekday].Hour,
                    )
                    if not bypass_date_limitations
                    else True
                )
                current_date_obj["openForBreakfast"] = (
                    (
                        b.is_date_valid_for_action(
                            now,
                            current_date_obj["date"],
                            breakfast_deadlines[weekday].Days,
                            breakfast_deadlines[weekday].Hour,
                        )
                    )
                    if not bypass_date_limitations
                    else True
                )
                current_date_obj["items"] = []
                current_date_obj["items"].append(serializer)
                result.append(current_date_obj)

        return result


class FloorSerializer(serializers.Serializer):
    code = serializers.CharField(source="Code")
    title = serializers.CharField(source="Caption")


class BuildingSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()
    floors = FloorSerializer(many=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["Personnel", "FullName"]


class PersonnelMonthlyReport(serializers.Serializer):
    year = serializers.IntegerField(max_value=9999, min_value=0000)
    month = serializers.IntegerField(max_value=12, min_value=1)


class AdminManipulationReasonsSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="Title")
    reasonCode = serializers.CharField(source="ReasonCode")

    class Meta:
        model = m.AdminManipulationReason
        fields = ["id", "title", "reasonCode"]


class AdminReasonserializer(serializers.Serializer):
    reason = serializers.IntegerField()
    comment = serializers.CharField(max_length=250, required=False)

    def validate_reason(self, id):
        reason = m.AdminManipulationReason.objects.filter(pk=id).first()
        if reason is None:
            raise serializers.ValidationError("invalid id")

        return reason

    def validate(self, attrs):
        data = super().validate(attrs)

        if data["reason"].Title.lower() == "other" and not data.get("comment"):
            raise ValueError(
                "you must provide a comment when using other's reason"
            )

        return data


class DeadlineSerializer(serializers.Serializer):
    days = serializers.IntegerField(source="Days", min_value=0)
    hours = serializers.IntegerField(source="Hour", min_value=0, max_value=24)
    # weekday = serializers.IntegerField(source="WeekDay", read_only=True)
    mealType = serializers.CharField(source="MealType")

    def validate_mealType(self, type: str):
        if type not in m.MealTypeChoices.values:
            raise serializers.ValidationError("invalid meal type.")

        return type


class UpdateDeadlineSerializer(serializers.Serializer):
    notifyPersonnel = serializers.BooleanField()
    deadlines = DeadlineSerializer(many=True)


class NoteSerializer(serializers.Serializer):
    date = serializers.CharField(max_length=10)
    note = serializers.CharField(
        max_length=1000, required=False, allow_null=True
    )
    reason = serializers.IntegerField()
    comment = serializers.CharField(max_length=250, required=False)

    def validate_reason(self, id):
        reason = m.AdminManipulationReason.objects.filter(pk=id).first()
        if reason is None:
            raise serializers.ValidationError("invalid id")

        return reason

    def validate_date(self, date):
        date = u.validate_date(date)
        if date is None:
            raise serializers.ValidationError("invalid date value.")

        return date

    def validate(self, attrs):
        data = super().validate(attrs)

        if data["reason"].ReasonCode.lower() == "other" and not data.get("comment"):
            raise serializers.ValidationError(
                "you must provide a comment when using other's reason"
            )

        return data
