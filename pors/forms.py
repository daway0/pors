from django import forms

from . import models as m


class CreateItemForm(forms.Form):
    ItemName = forms.CharField(max_length=500, label="نام")
    Category = forms.IntegerField()
    MealType = forms.CharField(max_length=3)
    ItemDesc = forms.CharField(
        max_length=250,
        required=False,
        widget=forms.Textarea,
    )
    IsActive = forms.BooleanField(initial=True)
    Image = forms.FileField(required=False)
    CurrentPrice = forms.IntegerField(min_value=0)
    ItemProvider = forms.IntegerField()

    def validate_Category(self, category_id):
        category = m.Category.objects.filter(id=category_id).first()
        if category is None:
            raise forms.ValidationError("invalid category id")

        return category
    
    def validate_ItemProvider(self, provider_id):
        provider = m.ItemProvider.objects.filter(id=provider_id).first()
        if provider is None:
            raise forms.ValidationError("invalid provider id")

    def create(self, validated_data):
        return m.Item.objects.create(**validated_data)
