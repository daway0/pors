import datetime
from calendar import monthrange

from django.db.models import ExpressionWrapper, F, IntegerField, Sum, fields
from django.shortcuts import get_list_or_404, render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from .models import Category, DailyMenuItem, Holiday, Item, Order, OrderItem
from .serializers import (
    AvailableItemsSerializer,
    CategorySerializer,
    DayMenuSerializer,
    DebtSerializer,
    GeneralCalendarSerializer,
    HolidaySerializer,
    OrderedDaySerializer,
    OrderSerializer,
    SelectedItemSerializer,
)
from .utils import first_and_last_day_date, get_weekend_holidays

# Create your views here.


def ui(request):
    return render(request, "edari.html")


class AvailableItems(ListAPIView):
    """
    تمام ایتم های موجود برگشت داده می‌شود.
    """

    queryset = Item.objects.filter(IsActive=True)
    serializer_class = AvailableItemsSerializer


@api_view(["GET"])
def DayMenu(request):
    """
    این ویو مسئولیت ارائه منو غذایی مطابق پارامتر `date` را دارا است.
    """
    requested_date = request.query_params.get("date")
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


@api_view(["GET"])
def edari_calendar(request):
    """
    این ویو مسئولیت  ارائه روز های ماه و اطلاعات مربوط آن ها را دارد.
    این اطلاعات شامل سفارشات روز و تعطیلی روز ها می‌باشد.
    در صورت دریافت پارامتر های `month` و `year`, اطلاعات مربوط به تاریخ وارد شده ارائه داده می‌شود.
    """
    today = datetime.date.today()
    year = request.query_params.get("year", today.year)
    month = request.query_params.get("month", today.month)
    year = int(year)
    month = int(month)
    last_day_week_num, last_day = monthrange(year, month)
    first_day_week_num = datetime.datetime(year, month, 1).weekday()
    first_day_date, last_day_date = first_and_last_day_date(month, year)
    print(first_day_date, last_day_date)
    holidays = Holiday.objects.filter(
        HolidayDate__range=(first_day_date, last_day_date)
    )
    weekend_holidays = get_weekend_holidays(year, month)
    holidays_serializer = HolidaySerializer(holidays, many=True)
    holidays_serializer = holidays_serializer.data
    holidays_serializer += weekend_holidays
    holidays_serializer.sort()
    days_with_menu = DailyMenuItem.objects.filter(
        AvailableDate__range=(first_day_date, last_day_date),
    ).values("AvailableDate", "Item")
    days_with_menu_serializer = SelectedItemSerializer(
        days_with_menu, many=True
    )
    ordered_days = Order.objects.filter(
        DeliveryDate__range=(first_day_date, last_day_date),
        Personnel=request.user,
    ).values("DeliveryDate")
    ordered_days_serializer = OrderedDaySerializer(ordered_days).data
    debt = (
        Order.objects.filter(orderitem__isnull=False)
        .values("orderitem__PricePerOne", "AppliedSubsidy")
        .annotate(
            debt=ExpressionWrapper(
                Sum("orderitem__PricePerOne") - Sum("AppliedSubsidy"),
                output_field=IntegerField(),
            )
        )
        .values("debt")
    )
    debt_serializer = DebtSerializer(debt)
    orders = (
        OrderItem.objects.filter(
            Order__DeliveryDate__range=(first_day_date, last_day_date),
            Order__IsDeleted=False,
        )
        .select_related("Order", "OrderedItem")
        .values(
            "Order__DeliveryDate",
            "OrderedItem__id",
            "OrderedItem__ItemName",
            "OrderedItem__ItemDesc",
            "OrderedItem__Image",
            "OrderedItem__CurrentPrice",
            "OrderedItem__Category_id",
            "Quantity",
            "PricePerOne",
        )
        .annotate(
            total=ExpressionWrapper(
                F("Quantity") * F("PricePerOne"),
                output_field=fields.IntegerField(),
            ),
            fanavaran=F("Order__AppliedSubsidy"),
            debt=ExpressionWrapper(
                F("Quantity") * F("PricePerOne") - F("Order__AppliedSubsidy"),
                output_field=fields.IntegerField(),
            ),
        )
    )
    print(orders.query)


    orders_serializer = OrderSerializer(instance=orders, many=True).data

    # final = GeneralCalendarSerializer(
    #     data={
    #         "today": str(today),
    #         "year": year,
    #         "month": month,
    #         "firstDayOfWeek": first_day_week_num,
    #         "lastDayOfWeek": last_day_week_num,
    #         "holidays": holidays_serializer,
    #         "daysWithMenu": days_with_menu_serializer.data,
    #         "orderedDays": ordered_days_serializer,
    #         "debt": debt_serializer,
    #         "orders": ordered_days_serializer
    #     }
    # )
    # if final.is_valid():
    #     return Response(final.data)
    # return Response(final.errors)
    return Response(orders_serializer)
