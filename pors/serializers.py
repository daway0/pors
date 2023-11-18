from rest_framework import serializers

from . import models as m
from .utils import validate_date


class AvailableItemsSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField(source="id")
    itemName = serializers.CharField(source="ItemName")
    image = serializers.CharField(source="Image")

    class Meta:
        model = m.Item
        fields = ("id", "itemName", "image")


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


# class ItemSerializer(serializers.ModelSerializer):
#     name = serializers.SerializerMethodField()
#     img = serializers.SerializerMethodField()
#     category = serializers.SerializerMethodField()
#     description = serializers.SerializerMethodField()
#     is_active = serializers.SerializerMethodField()

#     class Meta:
#         model = m.ItemPrice
#         fields = (
#             "name",
#             "Price",
#             "img",
#             "category",
#             "description",
#             "is_active",
#         )

#     def get_name(self, obj: m.ItemPrice):
#         return obj.Item.ItemName

#     def get_img(self, obj: m.ItemPrice):
#         return obj.Item.ItemName

#     def get_category(self, obj: m.ItemPrice):
#         return obj.Item.Category

#     def get_description(self, obj: m.ItemPrice):
#         return obj.Item.ItemDesc

#     def get_is_active(self, obj: m.ItemPrice):
#         return obj.Item.IsActive


class HolidaySerializer(serializers.Serializer):
    holidays = serializers.SerializerMethodField()

    def get_holidays(self, obj):
        result = []
        for date in obj.values():
            if date["HolidayDate"] not in result:
                result.append(date["HolidayDate"])
        return result


class SelectedItemsBasedOnDaySerializer(serializers.Serializer):
    date = serializers.CharField(max_length=10)
    items = serializers.ListField()


class SelectedItemSerializer(serializers.Serializer):
    selectedItems = serializers.SerializerMethodField()

    def get_selectedItems(self, obj):
        result = []
        for item in obj:
            result.append(
                SelectedItemsBasedOnDaySerializer(
                    data={
                        "date": item.get("date"),
                        "items": item.get("items"),
                    },
                    many=True,
                ).initial_data
            )
        return result


class DebtSerializer(serializers.Serializer):
    debt = serializers.IntegerField()


class OrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="OrderedItem__id")
    title = serializers.CharField(source="OrderedItem__ItemName")
    currentPrice = serializers.IntegerField(source="OrderedItem__CurrentPrice")
    img = serializers.CharField(source="OrderedItem__Image")
    category = serializers.IntegerField(source="OrderedItem__Category_id")
    description = serializers.CharField(source="OrderedItem__ItemDesc")
    quantity = serializers.IntegerField(source="Quantity")
    pricePerItem = serializers.IntegerField(source="PricePerOne")


class OrderBillSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    fanavaran = serializers.IntegerField()
    debt = serializers.IntegerField()


class OrderSerializer(serializers.Serializer):
    orderDate = serializers.CharField()
    orderItems = serializers.SerializerMethodField()
    orderBill = serializers.SerializerMethodField()

    def get_orderItems(self, obj):
        result = OrderItemSerializer(obj.get("orderItems"), many=True).data
        return result

    def get_orderBill(self, obj):
        return OrderBillSerializer(obj.get("orderBill")).data


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


class DaysWithMenuSerializer(serializers.Serializer):
    daysWithMenu = serializers.SerializerMethodField()

    def get_daysWithMenu(self, obj):
        result = []
        for item in obj:
            result.append(item["AvailableDate"])
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


class RemoveMenuItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="Item")
    date = serializers.CharField(max_length=10, source="AvailableDate")

    def validate(self, data):
        date = validate_date(data["AvailableDate"])
        if not date:
            raise serializers.ValidationError("Date is not valid.")
        instance = m.DailyMenuItem.objects.filter(
            AvailableDate=date, Item=data["Item"]
        )
        if not instance:
            raise serializers.ValidationError(
                "Item not exists in provided date"
            )
        orders = m.OrderItem.objects.select_related("Order").filter(
            Order__DeliveryDate=data["AvailableDate"], OrderedItem=data["Item"]
        )
        if orders:
            raise serializers.ValidationError(
                "This item is not eligable for deleting, an order has already"
                " owned this item."
            )
        return data

    def _remove_item(self):
        date = self.validated_data.get("AvailableDate")
        item = self.validated_data.get("Item")
        m.DailyMenuItem.objects.get(AvailableDate=date, Item=item).delete()


class CreateOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.OrderItem
        fields = ("OrderedItem", "Quantity", "PricePerOne", "Order")

    # def create(self, validated_data):
    #     validated_data.pop("PricePerOne", None)
    #     validated_data.pop("Order", None)
    #     instance = m.OrderItem.objects.create(**validated_data)


class CreateOrderSerializer(serializers.Serializer):
    item = serializers.IntegerField()
    personnel = serializers.CharField(max_length=250, source="Personnel")
    date = serializers.CharField(max_length=10, source="DeliveryDate")
    quantity = serializers.IntegerField()

    def validate(self, data):
        date = validate_date(data.get("DeliveryDate"))
        if not date:
            raise serializers.ValidationError("Invalid 'date' value.")
        if not self._validate_item(date, data.get("item")):
            raise serializers.ValidationError("Invalid 'item' value.")
        return data

    def _validate_item(self, date: str, item_id: int) -> bool:
        is_item_available = m.DailyMenuItem.objects.select_related(
            "Item"
        ).filter(
            Item__IsActive=True,
            Item__id=item_id,
            IsActive=True,
            AvailableDate=date,
        )
        return bool(is_item_available)

    def create(self, validated_data):
        subsidy = m.Subsidy.objects.get(UntilDate__isnull=True).Amount
        instance = m.Order.objects.create(**validated_data)
        instance.AppliedSubsidy = subsidy
        return instance


# class EdariCalendarSchemaSerializer(serializers.Serializer):
#     generalCalendar = serializers.SerializerMethodField()
#     daysWithMenu = serializers.SerializerMethodField()
#     orderedDays = serializers.SerializerMethodField()
#     totalIndebtedness = serializers.SerializerMethodField()
#     orders = serializers.SerializerMethodField()

#     def get_generalCalendar(self, obj):
#         ...


# def foo():
#     qs = result = PorsOrderItem.objects.filter(
#         Order_id__DeliveryDate__range=["1402-08-28", "1402-08-29"]
#     ).values("OrderedItem_id", "Order_id__DeliveryDate")

#     return reposone(SelectedItemsSerializer(qs))
