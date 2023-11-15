



from django.urls import path, include
from . import views

app_name = "pors"

urlpatterns = [
    path("calendar/", views.edari_calendar, name="edari_calendar"),
    path("", views.ui)
]
