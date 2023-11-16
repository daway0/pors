from rest_framework import serializers

from . import models as m


class AvailableItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ItemPriceHistory
        fields = ("id", "ItemName", "Image")


class DayMenuSerializer(serializers.ModelSerializer):
    food_ids = serializers.SerializerMethodField(
        "List of foods based on the given date."
    )

    class Meta:
        model = m.DailyMenuItem
        fields = ("food_ids",)

    def get_food_ids(self, obj: m.DailyMenuItem):
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
            if date not in result:
                result.append(date)
        return result


class SelectedItemsBasedOnDaySerializer(serializers.Serializer):
    date = serializers.CharField(max_length=10)
    items = serializers.ListField()


class SelectedItemSerializer(serializers.Serializer):
    SelectedItems = serializers.SerializerMethodField()

    def get_SelectedItems(self, obj):
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
    lastDayOfWeek = serializers.IntegerField()
    holidays = serializers.ListField()
    daysWithMenu = serializers.ListField()


class EdariFirstPageSerializer(serializers.Serializer):
    is_open = serializers.BooleanField()
    full_name = serializers.CharField()
    profile = serializers.ImageField()
    current_date = serializers.DictField()


class DaysWithMenuSerializer(serializers.Serializer):
    days_with_menu = serializers.SerializerMethodField()

    def get_days_with_menu(self, obj):
        result = []
        for item in obj:
            result.append(item["AvailableDate"])
        return result


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
