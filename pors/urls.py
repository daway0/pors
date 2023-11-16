from django.urls import path, include
from . import views

app_name = "pors"

urlpatterns = [
    path("calendar/", views.general_calendar, name="calendar"),
    path("administrative/calendar/", views.edari_calendar, name="acalendar"),
    path("administrative/panel/", views.edari_first_page, name="apanel"),
    path(
        "administrative/available-items/",
        views.AvailableItems.as_view(),
        name="aallitems",
    ),
    path(
        "administrative/add-item-to-menu/",
        views.AvailableItems.as_view(),
        name="aadditem",
    ),
    path(
        "administrative/remove-item-from-menu/",
        views.AvailableItems.as_view(),
        name="aremoveitem",
    ),

    path("", views.ui),
]
