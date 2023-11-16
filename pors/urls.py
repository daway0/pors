from django.urls import path, include
from . import views

app_name = "pors"

urlpatterns = [
    path("calendar/", views.general_calendar, name="calendar"),
    path("edari_calendar/", views.edari_calendar, name="edari_calendar"),
    path("edari_first_page/", views.edari_first_page, name="edari_first_page"),
    path("", views.ui),
]
