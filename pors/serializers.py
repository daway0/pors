from rest_framework import serializers
from models import OrderItem
from . import models as m


class AvailableItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ItemPrice
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


class ItemSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = m.ItemPrice
        fields = (
            "name",
            "Price",
            "img",
            "category",
            "description",
            "is_active",
        )

    def get_name(self, obj: m.ItemPrice):
        return obj.Item.ItemName

    def get_img(self, obj: m.ItemPrice):
        return obj.Item.ItemName

    def get_category(self, obj: m.ItemPrice):
        return obj.Item.Category

    def get_description(self, obj: m.ItemPrice):
        return obj.Item.ItemDesc

    def get_is_active(self, obj: m.ItemPrice):
        return obj.Item.IsActive


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Holiday
        fields = "DeliveryDate"


class SelectedItemsBasedOnDaySerializer(serializers.Serializer):
    Date = serializers.CharField(max_length=10)
    SelectedItems = serializers.ListField()


class SelectedItemsSerializer(serializers.Serializer):
    SelectedItems = serializers.SerializerMethodField()

    def get_SelectedItems(self, obj):
        d = {}
        for item_id, date in obj:
            if not date in d.keys():
                d[date] = [item_id]
                continue
            d[date].append(item_id)

        result = []
        for day, items in d.items():
            result += SelectedItemsBasedOnDaySerializer(
                instance={"Date": day,
                          "SelectedItems": items}
            ).data
        return result



def foo():
    qs = result = PorsOrderItem.objects.filter(
    Order_id__DeliveryDate__range=['1402-08-28', '1402-08-29']
).values('OrderedItem_id', 'Order_id__DeliveryDate')

    return reposone (SelectedItemsSerializer(qs))
