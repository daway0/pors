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


class ItemFormCreate(forms.ModelForm):
    class Meta:
        common_class = 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
        model = m.Item
        fields = [
            'ItemName',
            'Category',
            'MealType',
            'ItemDesc',
            'Image',
            'CurrentPrice',
            'ItemProvider',
        ]
        labels = {
            'ItemName': 'عنوان آیتم',
            'Category': 'دسته بندی',
            'MealType': 'قابل استفاده در وعده',
            'CurrentPrice': 'قیمت',
            'ItemProvider': 'تامین کننده',
            'ItemDesc': 'توضیحات ایتم',
            'Image': 'عکس آیتم',
        }
        widgets = {
            'ItemName': forms.TextInput(attrs={
                'class': common_class,
                'placeholder': 'عنوان آیتم را وارد کنید'
            }),
            'Category': forms.Select(attrs={
                'class': common_class,
            }),
            'MealType': forms.Select(attrs={
                'class': common_class
            }),
            'ItemDesc': forms.Textarea(attrs={
                'class': f'{common_class} h-16',
                'placeholder': 'توضیحات آیتم را وارد کنید'
            }),
            'CurrentPrice': forms.NumberInput(attrs={
                'class': common_class,
                'placeholder': 'به تومان'
            }),
            'ItemProvider': forms.Select(attrs={
                'class': common_class
            }),
        }

    def __init__(self, *args, **kwargs):
        super(ItemFormCreate, self).__init__(*args, **kwargs)
        self.fields['Category'].empty_label = None 
        self.fields['ItemProvider'].empty_label = None 

    def create(self, validated_data):
        return m.Item.objects.create(**validated_data)