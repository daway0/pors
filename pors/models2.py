# Create your models here.
from django.db import models


class Category(models.Model):
    class Meta:
        verbose_name = "دسته بندی غذا"
        verbose_name_plural = "دسته بندی غذا ها"

    CategoryName = models.CharField(max_length=300, verbose_name="نام دسته بندی")

    def __str__(self):
        return self.CategoryName


class Food(models.Model):
    class Meta:
        verbose_name = "اطلاعات غذا"
        verbose_name_plural = "اطلاعات غذا ها"

    FoodName = models.CharField(max_length=500, verbose_name="نام غذا")
    Category = models.ForeignKey(
        "Category", on_delete=models.CASCADE, verbose_name="دسته بندی"
    )
    Food_desc = ...
    is_active = ...

    def __str__(self):
        return self.FoodName


class FoodAvailablity(models.Model):
    Food = ...
    Price = ...
    AvailabeDate = ...


class FoodOrder(models.Model):
    user = ...
    OrderedFood = ...  # FoodAvailablity
    Quantitiy = ...  # defualt1
