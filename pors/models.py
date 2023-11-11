from django.db import models



class Category(models.Model):
    class Meta:
        verbose_name = "دسته بندی غذا"
        verbose_name_plural = "دسته بندی غذا ها"
    CategoryName = models.CharField(max_length=300,verbose_name='نام دسته بندی')

    def __str__(self):
        return self.CategoryName





class Food(models.Model):
    class Meta:
        verbose_name = "اطلاعات غذا"
        verbose_name_plural = "اطلاعات غذا ها"
    FoodName = models.CharField(max_length=500,verbose_name='نام غذا')
    Category = models.ForeignKey('Category',on_delete=models.CASCADE,verbose_name='دسته بندی')
    FoodDesc = models.TextField(blank=True, null=True)
    IsActive = models.BooleanField(default=True)
    Image = models.ImageField(upload_to="media/foods/")

    def __str__(self):
        return self.FoodName


class Order(models.Model):
    Personnel = models.CharField()
    IsActive = models.BooleanField(default=True, help_text="IsDeleted?(Soft Delete)")
    Date = models.DateField()



class OrderItem(models.Model):
    OrderedFood = models.ForeignKey(...)
    Quantitiy = models.PositiveSmallIntegerField(default=1)
    IsActive = models.BooleanField(default=True)


class ActionLog(models.Model):
    class ActionChoices(models.TextChoices):
        CREATE = "CRT", "CREATE"
        DELETE = "DEL", "DELETE"
        UPDATE = "UPT", "UPDATE"
        CANCEL = "CN", "CANCEL"

    class ObjectChoices(models.TextChoices):
        ORDER = "ORD", "ORDER"
        ORDER_ITEM = "OIM", "ORDER_ITEM"
        
    CreatedAt = models.DateTimeField(auto_now_add=True)
    User = models.CharField()
    Action = models.CharField(choices=ActionChoices.choices)