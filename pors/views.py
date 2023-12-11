from django.shortcuts import get_list_or_404, render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from . import business as b
from .config import OPEN_FOR_ADMINISTRATIVE
from .general_actions import GeneralCalendar
from .models import Category, DailyMenuItem, Item, ItemsOrdersPerDay, Order
from .serializers import (
    AddMenuItemSerializer,
    AvailableItemsSerializer,
    CategorySerializer,
    DayMenuSerializer,
    EdariFirstPageSerializer,
    OrderSerializer,
    SelectedItemSerializer,
)
from .utils import (
    execute_raw_sql_with_params,
    first_and_last_day_date,
    get_first_orderable_date,
    split_dates,
)

# Create your views here.


def ui(request):
    return render(request, "administrativeMainPanel.html")


@api_view(["POST"])
def add_item_to_menu(request):
    serializer = AddMenuItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            "Successfully added the item into the menu.", status.HTTP_200_OK
        )
    return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def remove_item_from_menu(request):
    validatior = b.ValidateRemove(request.data)
    if validatior.is_valid():
        validatior.remove_item()
        return Response(
            "Successsfully deleted the item from menu.", status.HTTP_200_OK
        )
    return Response(validatior.error, status.HTTP_400_BAD_REQUEST)


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
def personnel_calendar(request):
    """
    این ویو مسئولیت  ارائه روز های ماه و اطلاعات مربوط آن ها را دارد.
    این اطلاعات شامل سفارشات روز و تعطیلی روز ها می‌باشد.
    در صورت دریافت پارامتر های `month` و `year`, اطلاعات مربوط به تاریخ وارد شده ارائه داده می‌شود.
    """
    # Past Auth...
    personnel = "j.pashootan@eit"
    year = request.query_params.get("year")
    month = request.query_params.get("month")
    if year is None or month is None:
        return Response(
            "'year' and 'month' parameters must specified.",
            status.HTTP_400_BAD_REQUEST,
        )
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        return Response("Invalid parameters.", status.HTTP_400_BAD_REQUEST)
    if month > 12:
        return Response("Invalid month value.", status.HTTP_400_BAD_REQUEST)

    first_day_date, last_day_date = first_and_last_day_date(month, year)

    general_calendar = GeneralCalendar(year, month)

    orders = Order.objects.filter(
        DeliveryDate__range=(first_day_date, last_day_date),
        Personnel=personnel,
    )
    totalDebt = sum([obj.PersonnelDebt for obj in orders])

    ordered_days_list = [obj.DeliveryDate for obj in orders]
    spilitted_ordered_days_list = split_dates(ordered_days_list, "day")

    # Couldn't use django orm because "Order" doesn't have
    # relation with orderitem table.
    query = """
    SELECT oi.DeliveryDate, oi.Quantity, oi.PricePerOne,
           i.id, i.ItemName, i.Image, i.CurrentPrice,
           i.Category_id, i.ItemDesc, oi.Personnel,
           o.SubsidyAmount, o.PersonnelDebt, o.TotalPrice
    FROM pors_orderitem AS oi
    INNER JOIN pors_item AS i ON oi.Item_id = i.id
    INNER JOIN "Order" AS o ON o.Personnel = oi.Personnel AND o.DeliveryDate = oi.DeliveryDate
    WHERE oi.DeliveryDate between %s AND %s and oi.Personnel = %s
    ORDER BY oi.DeliveryDate
    """
    params = (first_day_date, last_day_date, personnel)
    order_items = execute_raw_sql_with_params(query, params)

    orders_items_data = OrderSerializer(order_items).data
    ordered_days_and_debt = {
        "orderedDays": spilitted_ordered_days_list,
        "totalDebt": totalDebt,
    }

    # Unpacking Serializers data into 1 single dictionary
    final_schema = {
        **general_calendar.get_calendar(),
        **ordered_days_and_debt,
        **orders_items_data,
    }
    return Response(
        data=(final_schema),
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def edari_calendar(request):
    # Past Auth...
    personnel = ...
    year = request.query_params.get("year")
    month = request.query_params.get("month")

    if year is None or month is None:
        return Response(
            "'year' and 'month' parameters must specified.",
            status.HTTP_400_BAD_REQUEST,
        )
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        return Response("Invalid parameters.", status.HTTP_400_BAD_REQUEST)

    if not 1 <= month <= 12:
        return Response("Invalid month value.", status.HTTP_400_BAD_REQUEST)

    month_first_day_date, month_last_day_date = first_and_last_day_date(
        month, year
    )
    general_calendar = GeneralCalendar(year, month)

    selected_items = ItemsOrdersPerDay.objects.filter(
        Date__range=[month_first_day_date, month_last_day_date]
    )
    selected_items_serializer = SelectedItemSerializer(selected_items).data

    return Response(
        data=(general_calendar.get_calendar(), selected_items_serializer),
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def edari_first_page(request):
    # ... past auth
    is_open = OPEN_FOR_ADMINISTRATIVE
    full_name = "test"  # DONT FORGET TO SPECIFY ...
    profile = "test"  # DONT FORGET TO SPECIFY ...
    year, month, day = get_first_orderable_date()
    current_date = {"day": day, "month": month, "year": year}

    serializer = EdariFirstPageSerializer(
        data={
            "isOpen": is_open,
            "fullName": full_name,
            "profile": profile,
            "currentDate": current_date,
        }
    ).initial_data

    return Response(serializer, status.HTTP_200_OK)


@api_view(["POST"])
def create_order_item(request):
    # past auth ...
    # past check is app open for creating order.
    personnel = "e.rezaee@eit"
    validator = b.ValidateOrder(request.data)
    if validator.is_valid():
        validator.create_order(personnel)
        return Response(
            "Order has been created successfully.", status.HTTP_201_CREATED
        )
    return Response(validator.error, status.HTTP_400_BAD_REQUEST)
