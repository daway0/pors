from rest_framework import serializers

from . import models as m
from .utils import validate_date


class AllItemSerializer(serializers.ModelSerializer):
    itemName = serializers.CharField(source="ItemName")
    image = serializers.CharField(source="Image")
    category = serializers.PrimaryKeyRelatedField(
        queryset=m.Category.objects.all(), source="Category"
    )
    currentPrice = serializers.IntegerField(source="CurrentPrice")
    mealType = serializers.CharField(source="get_MealType_display")
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
            "isActive",
        )


class DayMenuSerializer(serializers.ModelSerializer):
    foodIds = serializers.SerializerMethodField(
        "List of foods based on the given date."
    )

    class Meta:
        model = m.DailyMenuItem
        fields = ("food_ids",)

    def get_foodIds(self, obj: m.DailyMenuItem):
        food_ids = [price_item.Item.id for price_item in obj.PriceItem.all()]
        return food_ids


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


class SelectedItemSerializer(serializers.Serializer):
    selectedItems = serializers.SerializerMethodField()

    def get_selectedItems(self, obj):
        result = []
        current_date_obj = {}
        for object in obj:
            serializer = ItemOrderSerializer(
                data={"id": object.Item, "orderedBy": object.TotalOrders},
            ).initial_data
            if current_date_obj.get("date") == object.Date:
                current_date_obj["items"].append(serializer)
            else:
                current_date_obj = {}
                current_date_obj["date"] = object.Date
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
            schema["orderItems"] = []
            schema["orderItems"].append(serializer)
            schema["orderBill"] = {
                "total": object["TotalPrice"],
                "fanavaran": object["SubsidyAmount"],
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


class EdariFirstPageSerializer(serializers.Serializer):
    isOpen = serializers.BooleanField()
    fullName = serializers.CharField()
    profile = serializers.ImageField()
    currentDate = serializers.DictField()


class DayWithMenuSerializer(serializers.Serializer):
    day = serializers.CharField(source="Date")
    ordersNumber = serializers.IntegerField(source="TotalOrders")


class ListedDaysWithMenu(serializers.Serializer):
    dates = serializers.SerializerMethodField()

    def get_dates(self, obj):
        result = []
        for date in obj.values():
            if date["AvailableDate"] not in result:
                result.append(date["AvailableDate"])

        return result


class AddMenuItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="Item")
    date = serializers.CharField(max_length=10, source="AvailableDate")

    def validate(self, data):
        date = validate_date(data["AvailableDate"])
        if not date:
            raise serializers.ValidationError("Date is not valid.")
        instance = m.DailyMenuItem.objects.filter(
            AvailableDate=date, Item=data["Item"]
        )
        if instance:
            raise serializers.ValidationError(
                "Item already exist on provided date."
            )
        data["Item"] = m.Item.objects.get(id=data["Item"])
        data["IsActive"] = True
        return data

    def create(self, validated_data):
        return m.DailyMenuItem.objects.create(**validated_data)


class PersonnelSchemaSerializer(serializers.Serializer):
    orderedDays = serializers.ListField()
    totalDebt = serializers.IntegerField()
