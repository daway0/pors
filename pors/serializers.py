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
    Date = serializers.CharField(max_length=10)
    SelectedItems = serializers.ListField()


class SelectedItemSerializer(serializers.Serializer):
    SelectedItems = serializers.SerializerMethodField()

    def get_SelectedItems(self, obj):
        days = {}
        for item_id, date in obj:
            if date not in days.keys():
                days[date] = [item_id]
                continue
            days[date].append(item_id)

        result = []
        for day, items in days.items():
            result += SelectedItemsBasedOnDaySerializer(
                data={"Date": day, "SelectedItems": items}
            ).data
        return result


class OrderedDaySerializer(serializers.Serializer):
    ordered_days = serializers.SerializerMethodField()

    def get_ordered_days(self, obj):
        result = []
        for date in obj.values():
            if date not in result:
                result.append(date)
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
    orderDate = serializers.CharField(source="Order__DeliveryDate")
    orderItems = serializers.SerializerMethodField()
    orderBill = serializers.SerializerMethodField()

    def get_orderItems(self, obj):
        result = OrderItemSerializer(obj, many=True).data
        return result

    def get_orderBill(self, obj):
        return OrderBillSerializer(obj).data


class GeneralCalendarSerializer(serializers.Serializer):
    today = serializers.CharField()
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    firstDayOfWeek = serializers.IntegerField()
    lastDayOfWeek = serializers.IntegerField()
    holidays = serializers.ListField()
    daysWithMenu = serializers.ListField()
    orderedDays = serializers.ListField()
    debt = serializers.IntegerField()
    orders = serializers.ListField()


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
