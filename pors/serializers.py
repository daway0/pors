from rest_framework import serializers

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



class SelectedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.OrderItem
        fields = ("date", "id")