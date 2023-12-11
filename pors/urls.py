from django.urls import path, include
from . import views



app_name = "pors"

urlpatterns = [
    path("calendar/", views.personnel_calendar, name="calendar"),
    path("administrative/calendar/", views.edari_calendar, name="acalendar"),
    path("administrative/panel/", views.edari_first_page, name="apanel"),
    path(
        "administrative/available-items/",
        views.AvailableItems.as_view(),
        name="aavailable_items",
    ),
    path(
        "administrative/add-item-to-menu/",
        views.add_item_to_menu,
        name="aadd_item_to_menu",
    ),
    path(
        "administrative/remove-item-from-menu/",
        views.remove_item_from_menu,
        name="aremove_item_from_menu",
    ),
    path("", views.ui),
]
