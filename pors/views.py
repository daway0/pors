from django.db.models import (
    Case,
    ExpressionWrapper,
    F,
    IntegerField,
    Sum,
    Value,
    When,
    fields,
)
from django.shortcuts import get_list_or_404, render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from . import business as b
from .config import OPEN_FOR_ADMINISTRATIVE
from .general_actions import get_general_calendar
from .models import Category, DailyMenuItem, Item, ItemsOrdersPerDay
from .serializers import (
    AddMenuItemSerializer,
    AvailableItemsSerializer,
    CategorySerializer,
    CreateOrderItemSerializer,
    DayMenuSerializer,
    EdariFirstPageSerializer,
    ItemOrderSerializer,
    OrderSerializer,
    SelectedItemSerializer,
)
from .utils import (
    first_and_last_day_date,
    get_current_date,
    get_first_orderable_date,
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


# @api_view(["GET"])
# def personnel_calendar(request):
#     """
#     این ویو مسئولیت  ارائه روز های ماه و اطلاعات مربوط آن ها را دارد.
#     این اطلاعات شامل سفارشات روز و تعطیلی روز ها می‌باشد.
#     در صورت دریافت پارامتر های `month` و `year`, اطلاعات مربوط به تاریخ وارد شده ارائه داده می‌شود.
#     """
#     # Past Auth...
#     personnel = ...
#     year = request.query_params.get("year")
#     month = request.query_params.get("month")
#     if year is None or month is None:
#         return Response(
#             "'year' and 'month' parameters must specified.",
#             status.HTTP_400_BAD_REQUEST,
#         )
#     try:
#         month = int(month)
#         year = int(year)
#     except ValueError:
#         return Response("Invalid parameters.", status.HTTP_400_BAD_REQUEST)
#     if month > 12:
#         return Response("Invalid month value.", status.HTTP_400_BAD_REQUEST)
#     first_day_date, last_day_date = first_and_last_day_date(month, year)
#     general_calendar = get_general_calendar(year, month)
#     ordered_days = Order.objects.filter(
#         DeliveryDate__range=(first_day_date, last_day_date),
#         Personnel=personnel,
#     ).values("DeliveryDate")
#     ordered_days_list = [date["DeliveryDate"] for date in ordered_days]
#     # Todo handle the difference between subidy and total cost
#     debt = (
#         Order.objects.filter(DeliveryDate__range=["1402/00/00", "1403/00/00"])
#         .annotate(
#             total_price=Sum(
#                 ExpressionWrapper(
#                     F("orderitem__Quantity") * F("orderitem__PricePerOne"),
#                     output_field=fields.IntegerField(),
#                 )
#             )
#         )
#         .aggregate(
#             total_price=Sum("total_price"),
#             total_subsidy=Sum("AppliedSubsidy"),
#             difference=Sum(
#                 ExpressionWrapper(
#                     F("orderitem__Quantity") * F("orderitem__PricePerOne"),
#                     output_field=fields.IntegerField(),
#                 )
#             )
#             - Sum("AppliedSubsidy"),
#         )
#     )
#     """
#     ```sql
#     SELECT SUM(OI."Quantity" * OI."PricePerOne") AS total_cost,
#     SUM(O."AppliedSubsidy") AS subsidy,
#     CASE
#                     WHEN SUM(OI."Quantity" * OI."PricePerOne") - SUM(O."AppliedSubsidy") > 0 THEN SUM(OI."Quantity" * OI."PricePerOne") - SUM(O."AppliedSubsidy")
#                     ELSE 0
#     END AS debt
#     FROM PORS_ORDER AS O
#     INNER JOIN PORS_ORDERITEM AS OI ON O."id" = OI."Order_id"
#     WHERE o."IsDeleted" = False
#     """
#
#     # debt_serializer = DebtSerializer(debt).data
#     orders_items_qs = (
#         OrderItem.objects.filter(
#             Order__DeliveryDate__range=(first_day_date, last_day_date),
#             Order__IsDeleted=False,
#         )
#         .select_related("Order", "OrderedItem")
#         .values(
#             "Order__DeliveryDate",
#             "OrderedItem__id",
#             "OrderedItem__ItemName",
#             "OrderedItem__ItemDesc",
#             "OrderedItem__Image",
#             "OrderedItem__CurrentPrice",
#             "OrderedItem__Category_id",
#             "Quantity",
#             "PricePerOne",
#         )
#         .annotate(
#             total=ExpressionWrapper(
#                 F("Quantity") * F("PricePerOne"),
#                 output_field=fields.IntegerField(),
#             ),
#             fanavaran=F("Order__AppliedSubsidy"),
#             debt=ExpressionWrapper(
#                 F("Quantity") * F("PricePerOne") - F("Order__AppliedSubsidy"),
#                 output_field=fields.IntegerField(),
#             ),
#         )
#     )
#
#     orders = []
#     order_items = {}
#     order_bill = {}
#
#     for order in orders_items_qs:
#         if order["Order__DeliveryDate"] in order_bill.keys():
#             continue
#
#         order_bill[order["Order__DeliveryDate"]] = {
#             "total": order["total"],
#             "fanavaran": order["fanavaran"],
#             "debt": order["debt"],
#         }
#
#     for order in orders_items_qs:
#         if order["Order__DeliveryDate"] not in order_items:
#             order_items[order["Order__DeliveryDate"]] = []
#
#         order_items[order["Order__DeliveryDate"]].append(
#             {
#                 "OrderedItem__id": order["OrderedItem__id"],
#                 "OrderedItem__ItemName": order["OrderedItem__ItemName"],
#                 "OrderedItem__ItemDesc": order["OrderedItem__ItemDesc"],
#                 "OrderedItem__Image": order["OrderedItem__Image"],
#                 "OrderedItem__CurrentPrice": order[
#                     "OrderedItem__CurrentPrice"
#                 ],
#                 "OrderedItem__Category_id": order["OrderedItem__Category_id"],
#                 "Quantity": order["Quantity"],
#                 "PricePerOne": order["PricePerOne"],
#             }
#         )
#
#     for order_date in order_bill.keys():
#         orders.append(
#             {
#                 "orderDate": order_date,
#                 "orderItems": order_items[order_date],
#                 "orderBill": order_bill[order_date],
#             }
#         )
#
#     orders_serializer = OrderSerializer(instance=orders, many=True).data
#     return Response(
#         data=(
#             general_calendar,
#             ordered_days_list,
#             # debt_serializer,
#             orders_serializer,
#         ),
#         status=status.HTTP_200_OK,
#     )


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
    if month > 12:
        return Response("Invalid month value.", status.HTTP_400_BAD_REQUEST)
    first_day_date, last_day_date = first_and_last_day_date(month, year)
    general_calendar = get_general_calendar(year, month)
    selected_items = ItemsOrdersPerDay.objects.filter(
        Date__range=[first_day_date, last_day_date]
    )
    selected_items_serializer = SelectedItemSerializer(selected_items).data
    return Response(
        data=(general_calendar, selected_items_serializer),
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


# @api_view(["GET"])
# def create_order(request):
#     # pas auth ...
#     personnel = ...
#     item = request.data.get("item")
#     date = request.data.get("date")
#     quantity = request.data.get("quantity")
#     if not item or date or quantity:
#         return Response(
#             "'item','date' and 'quantity' must specified.",
#             status.HTTP_400_BAD_REQUEST,
#         )
#     date = validate_date(date)
#     order = Order.objects.filter(DeliveryDate=date, Personnel=personnel)
#     if not order:
#         order_serializer = CreateOrderSerializer(data=request.data)
#         if not order_serializer.is_valid():
#             return Response(
#                 order_serializer.errors, status.HTTP_400_BAD_REQUEST
#             )
#     else:
#         CreateOrderItemSerializer(request.data)
#         ...
