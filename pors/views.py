from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_list_or_404, render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from . import business as b
from .decorators import check, is_open_for_admins, is_open_for_personnel
from .general_actions import GeneralCalendar
from .messages import Message
from .models import (
    Category,
    DailyMenuItem,
    Item,
    ItemsOrdersPerDay,
    Order,
    OrderItem,
    SystemSetting,
)
from .serializers import (
    AddMenuItemSerializer,
    AllItemSerializer,
    CategorySerializer,
    FirstPageSerializer,
    ListedDaysWithMenu,
    MenuItemSerializer,
    OrderSerializer,
    PersonnelMenuItemSerializer,
)
from .utils import (
    execute_raw_sql_with_params,
    first_and_last_day_date,
    generate_csv,
    split_dates,
)

message = Message()


def ui(request):
    return render(request, "personnelMainPanel.html")


def uiadmin(request):
    return render(request, "administrativeMainPanel.html")


@api_view(["POST"])
@check([is_open_for_admins])
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

        message.add_message(
            "آیتم با موفقیت اضافه شد.",
            Message.SUCCESS,
        )

        return Response({"messages": message.messages()}, status.HTTP_200_OK)

    message.add_message(
        "مشکلی درهنگام اضافه کردن آیتم رخ داده است.", Message.ERROR
    )
    return Response(
        {"messages": message.messages(), "errors": serializer.errors},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_admins])
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
        message.add_message("آیتم با موفقیت حذف شد.", Message.SUCCESS)
        return Response({"messages": message.messages()}, status.HTTP_200_OK)

    message.add_message(
        "مشکلی حین حذف آیتم از منو رخ داده است.", Message.ERROR
    )
    return Response(
        {"messages": message.messages(), "errors": validatior.error},
        status.HTTP_400_BAD_REQUEST,
    )


class AllItems(ListAPIView):
    """
    تمام ایتم های موجود برگشت داده می‌شود.
    """

    queryset = Item.objects.filter()
    serializer_class = AllItemSerializer


class Categories(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


@api_view(["GET"])
@check([is_open_for_personnel])
def personnel_calendar(request):
    """
    این ویو مسئولیت  ارائه روز های ماه و اطلاعات مربوط آن ها را دارد.
    این اطلاعات شامل سفارشات روز و تعطیلی روز ها می‌باشد.
    در صورت دریافت پارامتر های `month` و `year`, اطلاعات مربوط به تاریخ وارد شده ارائه داده می‌شود.
    """

    # Past Auth...
    personnel = "e.rezaee@eit"
    error_message = b.validate_calendar_request(request.query_params)
    if error_message:
        message.add_message(
            "خطایی در حین اعتبارسنجی درخواست رخ داده است.", Message.ERROR
        )
        return Response(
            {"messages": message.messages(), "errors": error_message},
            status.HTTP_400_BAD_REQUEST,
        )

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
        .order_by("AvailableDate")
        .distinct()
    )
    days_with_menu_data = ListedDaysWithMenu(days_with_menu_qs).data
    splited_days_with_menu = split_dates(
        days_with_menu_data["dates"], mode="day"
    )

    menu_items = (
        DailyMenuItem.objects.filter(
            AvailableDate__range=[first_day_date, last_day_date],
            IsActive=True,
        )
        .order_by("AvailableDate", "Item_id")
        .values("AvailableDate", "Item_id")
    )
    menu_items_serialized_data = PersonnelMenuItemSerializer(menu_items).data

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
        **menu_items_serialized_data,
        **ordered_days_and_debt,
        **orders_items_data,
    }
    return Response(
        data=(final_schema),
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@check([is_open_for_admins])
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
        message.add_message(
            "خطایی در حین اعتبارسنجی درخواست رخ داده است.", Message.ERROR
        )
        return Response(
            {"messages": message.messages(), "errors": error_message},
            status.HTTP_400_BAD_REQUEST,
        )
    month = int(request.query_params.get("month"))
    year = int(request.query_params.get("year"))

    month_first_day_date, month_last_day_date = first_and_last_day_date(
        month, year
    )
    general_calendar = GeneralCalendar(year, month)
    days_with_menu = b.get_days_with_menu(month, year)

    menu_items = ItemsOrdersPerDay.objects.filter(
        Date__range=[month_first_day_date, month_last_day_date]
    )
    menu_items_serializer = MenuItemSerializer(menu_items).data

    final_schema = {
        **general_calendar.get_calendar(),
        "daysWithMenu": days_with_menu,
        **menu_items_serializer,
    }
    return Response(
        data=final_schema,
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def first_page(request):
    """
    First page information.
    will pass authentication first.

    Returns:
        isOpnen: Is today valid for actions
        fullName: User's full name
        profile: User's profile picture
        currentDate: Current date of system (jalali).
    """

    # ... past auth
    system_settings = SystemSetting.objects.last()
    open_for_admins = system_settings.IsSystemOpenForAdmin
    open_for_personnel = system_settings.IsSystemOpenForPersonnel
    full_name = "test"  # DONT FORGET TO SPECIFY ...
    profile = "test"  # DONT FORGET TO SPECIFY ...

    if (
        system_settings.BreakfastRegistrationWindowHours
        < system_settings.LaunchRegistrationWindowHours
    ):
        year, month, day = b.get_first_orderable_date(
            Item.MealTypeChoices.BREAKFAST
        )
    else:
        year, month, day = b.get_first_orderable_date(
            Item.MealTypeChoices.LAUNCH
        )

    first_orderable_date = {"year": year, "month": month, "day": day}

    serializer = FirstPageSerializer(
        data={
            "isOpenForAdmins": open_for_admins,
            "isOpenForPersonnel": open_for_personnel,
            "fullName": full_name,
            "profile": profile,
            "firstOrderableDate": first_orderable_date,
            "totalItemsCanOrderedForBreakfastByPersonnel": (
                system_settings.TotalItemsCanOrderedForBreakfastByPersonnel
            ),
        }
    ).initial_data

    return Response(serializer, status.HTTP_200_OK)


@api_view(["POST"])
@check([is_open_for_personnel])
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
        message.add_message(
            "آیتم مورد نظر با موفقیت در سفارش شما ثبت شد.", Message.SUCCESS
        )
        return Response(
            {"messages": message.messages()},
            status.HTTP_201_CREATED,
        )

    message.add_message(
        "مشکلی در حین ثبت آیتم مورد نظر رخ داده است.", Message.ERROR
    )
    return Response(
        {
            "messages": message.messages(),
            "errors": validator.error,
        },
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_personnel])
def remove_order_item(request):
    personnel = "e.rezaee@eit"
    request.data["personnel"] = personnel
    validator = b.ValidateOrder(request.data)
    if validator.is_valid(remove=True):
        validator.remove_order()
        message.add_message(
            "آیتم مورد نظر با موفقیت از سفارش شما حذف شد.", Message.SUCCESS
        )
        return Response({"messages": message.messages()}, status.HTTP_200_OK)

    message.add_message(
        "مشکلی حین حذف آیتم مورد نظر از سفارش شما رخ داده است.", Message.ERROR
    )
    return Response(
        {"messages": message.messages(), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_personnel])
def create_breakfast_order(request):
    # past auth ...
    # TODO decorator for checking is system open for breakfast submission
    personnel = "e.rezaee@eit"
    request.data["personnel"] = personnel
    validator = b.ValidateBreakfast(request.data)
    if validator.is_valid():
        validator.create_breakfast_order()
        message.add_message("صبحانه با موفقیت ثبت شد.", message.SUCCESS)
        return Response(
            {"messages": message.messages()}, status.HTTP_201_CREATED
        )

    message.add_message("ثبت صحبانه با مشکل مواجه شد.", Message.ERROR)
    return Response(
        {"messages": message.messages(), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_admins])
def item_ordering_personnel_list_report(request):
    """
    This view is responsible for generating a csv file that contains
        personnel who have ordered a specific item on specific date.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to look for.
        -  'item' (str): The item which you want to look for.
    """

    # past auth ...
    try:
        date, item_id = b.validate_request(request.data)
    except ValueError as err:
        message.add_message(
            "مشکلی در اعتبارسنجی درخواست شما رخ داده است.", Message.ERROR
        )
        return Response({"messages": message.messages(), "errors": str(err)})

    personnel = OrderItem.objects.filter(
        DeliveryDate=date, Item=item_id
    ).values(
        "Personnel",
        "Quantity",
    )
    csv_content = generate_csv(personnel)

    response = HttpResponse(
        content=csv_content,
        content_type="text/csv",
    )
    return response
