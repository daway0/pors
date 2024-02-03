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


class OrderSerializer(serializers.Serializer):
    orders = serializers.SerializerMethodField()

    def get_orders(self, obj):
        result = []
        schema = {}
        for object in obj:
            serializer = OrderItemSerializer(object).data
            date = schema.get("orderDate")
            if date == object["DeliveryDate"]:
                schema["orderItems"].append(serializer)
                continue

            schema = {}
            schema["orderDate"] = object["DeliveryDate"]
            schema["deliveryBuilding"] = object["DeliveryBuilding"]
            schema["deliveryFloor"] = object["DeliveryFloor"]
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
    code = serializers.CharField()
    title = serializers.CharField()


class BuildingSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()
    floors = FloorSerializer()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["Personnel", "FullName"]


class PersonnelMonthlyReport(serializers.Serializer):
    year = serializers.IntegerField(max_value=9999, min_value=0000)
    month = serializers.IntegerField(max_value=12, min_value=1)
