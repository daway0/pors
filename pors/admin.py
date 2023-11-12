from django.contrib import admin
from pors import models

# Register your models here.
@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    ...


@admin.register(models.Item)
class ItemAdmin(admin.ModelAdmin):
    ...

@admin.register(models.ItemPrice)
class ItemPriceAdmin(admin.ModelAdmin):
    ...

@admin.register(models.DailyMenuItem)
class DailyMenuItemAdmin(admin.ModelAdmin):
    ...

