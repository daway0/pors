from django.shortcuts import get_list_or_404, render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from . import business as b
from .config import OPEN_FOR_ADMINISTRATIVE
from .general_actions import GeneralCalendar
from .messages import Message
from .models import Category, DailyMenuItem, Item, ItemsOrdersPerDay, Order
from .serializers import (
    AddMenuItemSerializer,
    AllItemSerializer,
    CategorySerializer,
    DayMenuSerializer,
    EdariFirstPageSerializer,
    ListedDaysWithMenu,
    OrderSerializer,
    SelectedItemSerializer,
)
from .utils import (
    execute_raw_sql_with_params,
    first_and_last_day_date,
    get_first_orderable_date,
    split_dates,
)

message = Message()


def ui(request):
    return render(request, "administrativeMainPanel.html")


@api_view(["POST"])
def add_item_to_menu(request):
    """
    Adding items to menu.
    Data will pass several validations in order to add item in menu.

    Args:
        date: The date which you want to add item on.
        item: Id of the specific item.
    """

    serializer = AddMenuItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        message.add_message("گود جاب مرد", Message.SUCCESS)

        return Response({"message": message.messages()}, status.HTTP_200_OK)
    message.add_message("ملعون به ارور خوردم", Message.ERROR)
    return Response(
        {"erorr": serializer.errors, "message": message.messages()},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
def remove_item_from_menu(request):
    """
    Removing items from menu.
    Data will pass several validations in order to remove item.

    If any order has been submitted on that menu's item, then the
    item will not get removed.

    Args:
        date: The date which you want to remove item from.
        item: Id of the specific item.
    """

    validatior = b.ValidateRemove(request.data)
    if validatior.is_valid():
        validatior.remove_item()
        return Response(
            "Successsfully deleted the item from menu.", status.HTTP_200_OK
        )
    return Response(validatior.error, status.HTTP_400_BAD_REQUEST)


class AllItems(ListAPIView):
    """
    تمام ایتم های موجود برگشت داده می‌شود.
    """

    queryset = Item.objects.filter()
    serializer_class = AllItemSerializer


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
    error_message = b.validate_calendar_request(request.query_params)
    if error_message:
        return Response(error_message, status.HTTP_400_BAD_REQUEST)

    month = int(request.query_params.get("month"))
    year = int(request.query_params.get("year"))

    first_day_date, last_day_date = first_and_last_day_date(month, year)

    general_calendar = GeneralCalendar(year, month)

    # Days that have menues.
    days_with_menu_qs = (
        DailyMenuItem.objects.filter(
            AvailableDate__range=[first_day_date, last_day_date]
        )
        .values("AvailableDate")
        .distinct()
    )
    days_with_menu_data = ListedDaysWithMenu(days_with_menu_qs).data
    splited_days_with_menu = split_dates(
        days_with_menu_data["dates"], mode="day"
    )

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
        "daysWithMenu": splited_days_with_menu,
        **ordered_days_and_debt,
        **orders_items_data,
    }
    return Response(
        data=(final_schema),
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def edari_calendar(request):
    """
    Admin's calendar which have more detailed information about menus, orders.

    Args:
        year: Requested year.
        month: Requested month.

    Returns:
        will return several information which are:
        general calendar data,

        days that contains menu, and number of orders on each day,

        list of selected items on each day and
        the number of orders on each item on.
    """

    # Past Auth...
    error_message = b.validate_calendar_request(request.query_params)
    if error_message:
        return Response(error_message, status.HTTP_400_BAD_REQUEST)

    month = int(request.query_params.get("month"))
    year = int(request.query_params.get("year"))

    month_first_day_date, month_last_day_date = first_and_last_day_date(
        month, year
    )
    general_calendar = GeneralCalendar(year, month)
    days_with_menu = b.get_days_with_menu(month, year)

    selected_items = ItemsOrdersPerDay.objects.filter(
        Date__range=[month_first_day_date, month_last_day_date]
    )
    selected_items_serializer = SelectedItemSerializer(selected_items).data

    final_schema = {
        **general_calendar.get_calendar(),
        "daysWithMenu": days_with_menu,
        **selected_items_serializer,
    }
    return Response(
        data=final_schema,
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def edari_first_page(request):
    """
    First page information for `edari` users only.
    will pass authentication first.

    Returns:
        isOpnen: Is today valid for actions
        fullName: User's full name
        profile: User's profile picture
        currentDate: Current date of system (jalali).
    """

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
    """
    Responsible for submitting orders.
    The data will pass several validations in order to submit.
    check `ValidateOrder` docs for mor info.

    Args:
        date: The date which you want to submit order on.
        item: The item id which you want to buy.
    """

    # past auth ...
    # past check is app open for creating order.
    personnel = "e.rezaee@eit"
    request.data["personnel"] = personnel

    validator = b.ValidateOrder(request.data)
    if validator.is_valid(create=True):
        validator.create_order()
        return Response(
            "Order has been created successfully.", status.HTTP_201_CREATED
        )
    return Response(validator.error, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def remove_order_item(request):
    personnel = "e.rezaee@eit"
    request.data["personnel"] = personnel
    validator = b.ValidateOrder(request.data)
    if validator.is_valid(remove=True):
        validator.remove_order()
        return Response(
            "Order has been removed successfully.", status.HTTP_200_OK
        )
    return Response(validator.error, status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def create_breakfast_order(request):
    # past auth ...
    personnel = "e.rezaee@eit"
    request.data["personnel"] = personnel
    validator = b.ValidateBreakfast(request.data)
    if validator.is_valid():
        validator.create_breakfast_order()
        message.add_message("صبحانه با موفقیت ثبت شد.")
        return Response(
            {"messages": message.messages()}, status.HTTP_201_CREATED
        )

    message.add_message("ثبت صحبانه با مشکل مواجه شد.")
    return Response(
        {"messages": message.messages(), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )
