import re

from django import forms

from . import models as m
from .utils import localnow


class CreateItemForm(forms.ModelForm):
    class Meta:
        common_class = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
        model = m.Item
        fields = [
            "ItemName",
            "Category",
            "MealType",
            "ItemDesc",
            "Image",
            "CurrentPrice",
            "ItemProvider",
        ]
        labels = {
            "ItemName": "عنوان آیتم",
            "Category": "دسته بندی",
            "MealType": "قابل استفاده در وعده",
            "CurrentPrice": "قیمت",
            "ItemProvider": "تامین کننده",
            "ItemDesc": "توضیحات ایتم",
            "Image": "عکس آیتم",
        }
        widgets = {
            "ItemName": forms.TextInput(
                attrs={
                    "class": common_class,
                    "placeholder": "عنوان آیتم را وارد کنید",
                }
            ),
            "Category": forms.Select(
                attrs={
                    "class": common_class,
                }
            ),
            "MealType": forms.Select(attrs={"class": common_class}),
            "ItemDesc": forms.Textarea(
                attrs={
                    "class": f"{common_class} h-16",
                    "placeholder": "توضیحات آیتم را وارد کنید",
                }
            ),
            "CurrentPrice": forms.NumberInput(
                attrs={"class": common_class, "placeholder": "به تومان"}
            ),
            "ItemProvider": forms.Select(attrs={"class": common_class}),
        }

    def __init__(self, *args, **kwargs):
        super(CreateItemForm, self).__init__(*args, **kwargs)
        self.fields["Category"].empty_label = None
        self.fields["ItemProvider"].empty_label = None

    def clean_CurrentPrice(self):
        price = self.cleaned_data["CurrentPrice"]
        if not isinstance(price, int):
            raise forms.ValidationError("CurrentPrice must be int.")

        if price < 0:
            raise forms.ValidationError("CurrentPrice cannot be lower than 0.")

        return price

    def clean_Image(self):
        img = self.cleaned_data.get("Image")
        if img is None:
            return

        if img.size > (1024 * 1000):
            raise forms.ValidationError("image size is too big.")

        if not img.content_type.startswith("image"):
            raise forms.ValidationError(
                "invalid content type, only image is allowed."
            )

        if not re.match(
            r"^.*\.(jpg|jpeg|png|svg|jfif|pjpeg|pjp)$", img.name, re.IGNORECASE
        ):
            raise forms.ValidationError("invalid extension")

        return img

    def create(self, validated_data):
        item = m.Item.objects.create(**validated_data)
        m.ItemPriceHistory(
            Item=item,
            Price=item.CurrentPrice,
            FromDate=localnow().strftime("%Y/%m/%d"),
        ).save()
        return item

    def update(self, validated_data: dict, item: m.Item):
        validated_data.pop("id", None)
        price = validated_data.get("CurrentPrice")
        current_price = item.CurrentPrice

        for field, value in validated_data.items():
            setattr(item, field, value)
        item.save()

        if price != current_price:
            now = localnow().strftime("%Y/%m/%d")
            old_price_history = m.ItemPriceHistory.objects.filter(
                Item=item, UntilDate=None
            ).first()
            if old_price_history is not None:
                old_price_history.UntilDate = now
                old_price_history.save()

            m.ItemPriceHistory(
                Item=item,
                Price=price,
                FromDate=now,
            ).save()
