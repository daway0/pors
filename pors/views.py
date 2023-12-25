from hashlib import sha256
from random import getrandbits

from django.db.models import Q
from django.http.response import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from jdatetime import timedelta
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from . import business as b
from .decorators import (
    authenticate,
    check,
    is_open_for_admins,
    is_open_for_personnel,
)
from .general_actions import GeneralCalendar
from .messages import Message
from .models import (
    Category,
    DailyMenuItem,
    Item,
    ItemsOrdersPerDay,
    Order,
    Subsidy,
    SystemSetting,
    User,
)
from .serializers import (
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
    generate_token_hash,
    get_personnel_from_token,
    get_submission_deadline,
    get_user_minimal_info,
    localnow,
    split_dates,
)

# from Utility.Authentication.Utils import (
#     V1_PermissionControl as permission_control,
#     V1_get_data_from_token as get_token_data,
#     V1_find_token_from_request as find_token
# )
#
# from Utility.APIManager.HR.get_single_user_info import v1 as user_info

message = Message()


@check([is_open_for_personnel])
@authenticate()
def ui(request, current_user):
    return render(
        request, "personnelMainPanel.html", get_user_minimal_info(current_user)
    )


@check([is_open_for_admins])
@authenticate(privileged_users=True)
def uiadmin(request, current_user):
    return render(
        request,
        "administrativeMainPanel.html",
        get_user_minimal_info(current_user),
    )


@api_view(["POST"])
@check([is_open_for_admins])
@authenticate(privileged_users=True)
def add_item_to_menu(request, current_user):
    """
    Adding items to menu.
    Data will pass several validations in order to add item in menu.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to add item on.
        -  'item' (str): The item which you want to add.
    """

    validator = b.ValidateAddMenuItem(request.data)
    if validator.is_valid():
        validator.add_item()

        message.add_message(
            "آیتم با موفقیت اضافه شد.",
            Message.SUCCESS,
        )

        return Response({"messages": message.messages()}, status.HTTP_200_OK)

    message.add_message(validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_admins])
@authenticate(privileged_users=True)
def remove_item_from_menu(request, current_user):
    """
    Removing items from menu.
    Data will pass several validations in order to remove item.

    If any order has been submitted on that menu's item, then the
    item will not get removed.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to remove item from.
        -  'item' (str): The item which you want to remove.
    """

    validator = b.ValidateRemove(request.data)
    if validator.is_valid():
        validator.remove_item()
        message.add_message("آیتم با موفقیت حذف شد.", Message.SUCCESS)
        return Response({"messages": message.messages()}, status.HTTP_200_OK)

    message.add_message(validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


class AllItems(ListAPIView):
    """
    Returning list of all items from database.
    """

    queryset = Item.objects.filter()
    serializer_class = AllItemSerializer


class Categories(ListAPIView):
    """Returning list of all categories from dataase."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


@api_view(["GET"])
@check([is_open_for_personnel])
@authenticate()
def personnel_calendar(request, current_user):
    """
    Personnel's calendar which have enough information
        to generate the calendar from them.

    Args:
        year: Requested year.
        month: Requested month.

    Returns:
        Will return several information which are:
        -  General calendar data.
        -  Days that contains menu.
        -  List of menu items on each day.
        -  All ordered items and their detailed information.
    """

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
    personnel = get_personnel_from_token(
        request.COOKIES.get("token")
    ).Personnel

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
    with open("./pors/SQLs/PersonnelOrderWithBill.sql", mode="r") as f:
        query = f.read()

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
@authenticate(privileged_users=True)
def edari_calendar(request, current_user):
    """
    Admin's calendar which have more detailed information about menus, orders.

    Args:
        year: Requested year.
        month: Requested month.

    Returns:
        Will return several information which are:
        -  General calendar data.
        -  Days that contains menu, and number of orders on each day.
        -  List of menu items on each day and number of orders on each item.
    """

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
@authenticate()
def first_page(request, current_user):
    """
    First page information.
    will pass authentication first.

    Returns:
        isOpenForAdmins: Is system responsive to any admin actions.
        isOpenForPersonnel: Is system responsive to any personnel actions.
        fullName: User's full name
        profile: User's profile picture
        firstOrderableDate: First valid date for order submission.
    """

    personnel = get_personnel_from_token(request.COOKIES.get("token"))

    system_settings = SystemSetting.objects.last()
    open_for_admins = system_settings.IsSystemOpenForAdmin
    open_for_personnel = system_settings.IsSystemOpenForPersonnel

    (
        days_breakfast_deadline,
        hours_breakfast_deadline,
        days_launch_deadline,
        hours_launch_deadline,
    ) = get_submission_deadline()

    now = localnow()

    if (
        system_settings.BreakfastRegistrationWindowDays
        < system_settings.LaunchRegistrationWindowDays
    ):
        year, month, day = b.get_first_orderable_date(
            now, days_breakfast_deadline, hours_breakfast_deadline
        )
    else:
        year, month, day = b.get_first_orderable_date(
            now, days_launch_deadline, hours_launch_deadline
        )

    first_orderable_date = {"year": year, "month": month, "day": day}

    serializer = FirstPageSerializer(
        data={
            "isOpenForAdmins": open_for_admins,
            "isOpenForPersonnel": open_for_personnel,
            "fullName": personnel.FullName,
            "profile": personnel.Profile,
            "firstOrderableDate": first_orderable_date,
            "totalItemsCanOrderedForBreakfastByPersonnel": (
                system_settings.TotalItemsCanOrderedForBreakfastByPersonnel
            ),
        }
    ).initial_data

    return Response(serializer, status.HTTP_200_OK)


@api_view(["POST"])
@check([is_open_for_personnel])
@authenticate()
def create_order_item(request, current_user):
    """
    Responsible for submitting orders.
    The data will pass several validations in order to submit.
    check `ValidateOrder` docs for mor info.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to submit order.
        -  'item' (str): The item which you want to order.
    """

    personnel = get_personnel_from_token(request.COOKIES.get("token"))
    request.data["personnel"] = personnel.Personnel

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

    message.add_message(validator.message, Message.ERROR)
    return Response(
        {
            "messages": message.messages(),
            "errors": validator.error,
        },
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_personnel])
@authenticate()
def remove_order_item(request, current_user):
    """
    This view will remove an item from specific order.
    Check `ValidateOrder` docs for more information about validators.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to remove order item from.
        -  'item' (str): The item which you want to remove.
    """

    personnel = get_personnel_from_token(request.COOKIES.get("token"))
    request.data["personnel"] = personnel.Personnel
    validator = b.ValidateOrder(request.data)
    if validator.is_valid(remove=True):
        validator.remove_order()
        message.add_message(
            "آیتم مورد نظر با موفقیت از سفارش شما حذف شد.", Message.SUCCESS
        )
        return Response({"messages": message.messages()}, status.HTTP_200_OK)

    message.add_message(validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_personnel])
@authenticate()
def create_breakfast_order(request, current_user):
    """
    Responsible for submitting breakfast orders.
    The data will pass several validations in order to submit.
    check `ValidateBreakfast` docs for mor info.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to submit order.
        -  'item' (str): The item which you want to order.
    """

    # past auth ...

    personnel = get_personnel_from_token(request.COOKIES.get("token"))
    request.data["personnel"] = personnel.Personnel

    validator = b.ValidateBreakfast(request.data)
    if validator.is_valid():
        validator.create_breakfast_order()
        message.add_message("صبحانه با موفقیت ثبت شد.", message.SUCCESS)
        return Response(
            {"messages": message.messages()}, status.HTTP_201_CREATED
        )

    message.add_message(validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
def get_subsidy(request):
    date = b.validate_date(request.query_params.get("date"))
    if not date:
        message.add_message(
            "مشکلی در اعتبارسنجی درخواست شما رخ داده است.", Message.ERROR
        )
        return Response(
            {"messages": message.messages(), "errors": "Invalid 'date' value."}
        )

    subsidy = (
        Subsidy.objects.filter(
            Q(FromDate__lte=date, UntilDate__isnull=True)
            | Q(FromDate__lte=date, UntilDate__gte=date)
        )
        .first()
        .Amount
    )

    return Response({"data": {"subsidy": subsidy}})


# @permission_control
@api_view(["GET"])
def auth_gateway(request):
    """
    Authentication gateway that will use fanavaran's auth method to get
        personnel's info and create corresponding `User` record for them.

    After authentication, we will generate a token for personnel and set
        it as a cookie named `key` for them, with the max age of 2 weeks.

    Any request to this gateway has a reason, which can be:
        - Personnel doesn't have a user record in db.
        - The token got expired and must get new one.
        - Personnel already has a valid token in db, but the request's token
            is invalid or not set at all.
    """

    # token = find_token(request)
    # personnel = get_token_data(token, "username")
    #
    # full_name = get_token_data(token, "user_FullName")
    # is_admin = False
    personnel = "m.noruzi@eit"
    full_name = "mikaeil norouzi"
    is_admin = False

    personnel_user_record = User.objects.filter(
        Personnel=personnel, IsActive=True
    ).first()

    now = localnow()

    cookies_expire_time = now + timedelta(weeks=2)
    max_age = int((cookies_expire_time - now).total_seconds())
    cookies_expire_time = cookies_expire_time.strftime("%Y/%m/%d")

    request_token = request.COOKIES.get("token")
    cookies_path = reverse("pors:personnel_panel")

    full_path = f"{request.scheme}://{request.get_host()}{cookies_path}"
    response = HttpResponse(
        content=f"<script>window.location.replace('{full_path}')</script>",
        status=202,
    )

    if not personnel_user_record:
        # Personnel does not have a user record at all.
        # In this scenario, we will create a user record, with an api key
        # that will set as a cookie for personnel.

        # profile = user_info(personnel)["StaticPhotoURL"]
        profile = ""
        token = generate_token_hash(personnel, full_name, getrandbits)
        User.objects.create(
            Personnel=personnel,
            FullName=full_name,
            Profile=profile,
            IsAdmin=is_admin,
            Token=token,
            ExpiredAt=cookies_expire_time,
            IsActive=True,
        )

        response.set_cookie("token", token, path=cookies_path, max_age=max_age)
        return response

    elif personnel_user_record.ExpiredAt < now.strftime("%Y/%m/%d"):
        # In this scenario, personnel's token is expired,
        # So we generate a new one, update the existing one in database,
        # and set the new token for personnel as a cookie.

        token = generate_token_hash(personnel, full_name, getrandbits(10))
        personnel_user_record.Token = token
        personnel_user_record.ExpiredAt = cookies_expire_time
        personnel_user_record.save()

        response.set_cookie("token", token, path=cookies_path, max_age=max_age)
        return response

    elif not request_token or request_token != personnel_user_record.Token:
        # This is scenario happens when user already has a valid record
        # and token in database, but the request's token is invalid
        # or not present at all.
        # Either case, we fetch the current personnel's token from database
        # and set it as a cookie.

        response.set_cookie(
            "token",
            personnel_user_record.Token,
            path=cookies_path,
            max_age=max_age,
        )

    return response
