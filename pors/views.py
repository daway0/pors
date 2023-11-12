import datetime
from calendar import monthrange

from django.shortcuts import get_list_or_404, render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from .models import Category, DailyMenuItem, Item
from .serializers import (
    AvailableItemsSerializer,
    CategorySerializer,
    DayMenuSerializer,
)

# Create your views here.


def ui(request):
    return render(request, "edari.html")


class AvailableItems(ListAPIView):
    """
    تمام ایتم های موجود برگشت داده می‌شود.
    """

    queryset = Item.objects.all()
    serializer_class = AvailableItemsSerializer


@api_view(["POST"])
def DayMenu(request):
    """
    این ویو مسئولیت ارائه منو غذایی مطابق پارامتر `date` را دارا است.
    """
    requested_date = request.data.get("date")
    if not requested_date:
        return Response(
            "'date' parameter must be specified.",
            status=status.HTTP_400_BAD_REQUEST,
        )
    queryset = get_list_or_404(DailyMenuItem, AvailableDate=requested_date)
    serializer = DayMenuSerializer(data=queryset, many=True)
    return Response(serializer.data, status.HTTP_200_OK)


class Categories(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


api_view(["GET"])
def calendar(request):
    """
    این ویو مسئولیت  ارائه روز های ماه و اطلاعات مربوط آن ها را دارد.
    این اطلاعات شامل سفارشات روز و تعطیلی روز ها می‌باشد.
    در صورت دریافت پارامتر های `month` و `year`, اطلاعات مربوط به تاریخ وارد شده ارائه داده می‌شود.
    """
    if request.data.get("month") and request.data.get("year"):
        ...
    today = datetime.date.today()
    year = today.year
    month = today.month
    last_day_week_num, last_day = monthrange(year, month)
    first_day_week_num = datetime.datetime(year, month, 1).weekday()
