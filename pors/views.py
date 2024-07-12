from random import getrandbits

from django.db.models import Q
from django.http.response import HttpResponse
from django.shortcuts import get_list_or_404, render
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
    AdminManipulationReason,
    Category,
    DailyMenuItem,
    Deadlines,
    Item,
    ItemsOrdersPerDay,
    Order,
    Subsidy,
    SystemSetting,
    User,
)
from .serializers import (
    AdminManipulationReasonsSerializer,
    AllItemSerializer,
    CategorySerializer,
    Deadline,
    DeadlineSerializer,
    FirstPageSerializer,
    ListedDaysWithMenu,
    MenuItemSerializer,
    OrderSerializer,
    PersonnelMenuItemSerializer,
    UserSerializer,
)
from .utils import (
    execute_raw_sql_with_params,
    fetch_available_location,
    first_and_last_day_date,
    generate_token_hash,
    get_deadlines,
    localnow,
    split_dates,
)

# todo shipment
# from Utility.Authentication.Utils import (
#     V1_PermissionControl as permission_control,
#     V1_get_data_from_token as get_token_data,
#     V1_find_token_from_request as find_token
# )

message = Message()


@authenticate()
def ui(request, user, override_user: User):
    return render(request, "personnelMainPanel.html")


@authenticate(privileged_users=True)
def uiadmin(request, user, override_user: User):
    return render(request, "administrativeMainPanel.html")


@api_view(["POST"])
@check([is_open_for_admins])
@authenticate(privileged_users=True)
def add_item_to_menu(request, user: User, override_user: User):
    """
    Adding items to menu.
    Data will pass several validations in order to add item in menu.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to add item on.
        -  'item' (str): The item which you want to add.
    """

    validator = b.ValidateAddMenuItem(request.data, user)
    if validator.is_valid():
        validator.add_item()

        message.add_message(
            request,
            "آیتم با موفقیت اضافه شد.",
            Message.SUCCESS,
        )

        return Response(
            {"messages": message.messages(request)}, status.HTTP_200_OK
        )

    message.add_message(request, validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(request), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_admins])
@authenticate(privileged_users=True)
def remove_item_from_menu(request, user: User, override_user: User):
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

    validator = b.ValidateRemove(request.data, user)
    if validator.is_valid():
        validator.remove_item()
        message.add_message(request, "آیتم با موفقیت حذف شد.", Message.SUCCESS)
        return Response(
            {"messages": message.messages(request)}, status.HTTP_200_OK
        )

    message.add_message(request, validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(request), "errors": validator.error},
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
def personnel_calendar(request, user: User, override_user: User):
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
            request,
            "خطایی در حین اعتبارسنجی درخواست رخ داده است.",
            Message.ERROR,
        )
        return Response(
            {"messages": message.messages(request), "errors": error_message},
            status.HTTP_400_BAD_REQUEST,
        )

    month = int(request.query_params.get("month"))
    year = int(request.query_params.get("year"))
    first_day_date, last_day_date = first_and_last_day_date(month, year)

    personnel = (
        user.Personnel if not override_user else override_user.Personnel
    )

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
    menu_items_serialized_data = PersonnelMenuItemSerializer(
        menu_items,
        context={"bypass_date_limitations": True if override_user else False},
    ).data

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
def edari_calendar(request, user: User, override_user: User):
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
            request,
            "خطایی در حین اعتبارسنجی درخواست رخ داده است.",
            Message.ERROR,
        )
        return Response(
            {"messages": message.messages(request), "errors": error_message},
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
def first_page(request, user: User, override_user: User):
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
    if override_user:
        user = override_user

    system_settings = SystemSetting.objects.last()
    open_for_admins = system_settings.IsSystemOpenForAdmin
    open_for_personnel = system_settings.IsSystemOpenForPersonnel

    now = localnow()
    breakfast_deadlines, launch_deadlines = get_deadlines(Deadline)
    if not (breakfast_deadlines and launch_deadlines):
        return Response(
            "No deadline has been found for today's week number, Abort!",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    year, month, day = b.get_first_orderable_date(
        now, breakfast_deadlines, launch_deadlines
    )

    first_orderable_date = {"year": year, "month": month, "day": day}

    buildings = fetch_available_location()

    serializer = FirstPageSerializer(
        data={
            "isOpenForAdmins": open_for_admins,
            "isOpenForPersonnel": open_for_personnel,
            "userName": user.Personnel,
            "isAdmin": user.IsAdmin,
            "fullName": user.FullName,
            "profile": user.Profile,
            "buildings": buildings,
            "latestBuilding": user.LastDeliveryBuilding,
            "latestFloor": user.LastDeliveryFloor,
            "firstOrderableDate": first_orderable_date,
            "godMode": True if override_user else False,
        }
    ).initial_data

    return Response(serializer, status.HTTP_200_OK)


@api_view(["POST"])
@check([is_open_for_personnel])
@authenticate()
def create_order_item(request, user: User, override_user: User):
    """
    Responsible for submitting orders.
    The data will pass several validations in order to submit.
    check `ValidateOrder` docs for mor info.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to submit order.
        -  'item' (str): The item which you want to order.
    """

    validator = b.ValidateOrder(request.data, user, override_user)
    if validator.is_valid(create=True):
        validator.create_order()
        message.add_message(
            request,
            "آیتم مورد نظر با موفقیت در سفارش شما ثبت شد.",
            Message.SUCCESS,
        )
        return Response(
            {"messages": message.messages(request)},
            status.HTTP_201_CREATED,
        )

    message.add_message(request, validator.message, Message.ERROR)
    return Response(
        {
            "messages": message.messages(request),
            "errors": validator.error,
        },
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_personnel])
@authenticate()
def remove_order_item(request, user: User, override_user: User):
    """
    This view will remove an item from specific order.
    Check `ValidateOrder` docs for more information about validators.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to remove order item from.
        -  'item' (str): The item which you want to remove.
    """

    validator = b.ValidateOrder(request.data, user, override_user)
    if validator.is_valid(remove=True):
        validator.remove_order()
        message.add_message(
            request,
            "آیتم مورد نظر با موفقیت از سفارش شما حذف شد.",
            Message.SUCCESS,
        )
        return Response(
            {"messages": message.messages(request)}, status.HTTP_200_OK
        )

    message.add_message(request, validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(request), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@check([is_open_for_personnel])
@authenticate()
def create_breakfast_order(request, user: User, override_user: User):
    """
    Responsible for submitting breakfast orders.
    The data will pass several validations in order to submit.
    check `ValidateBreakfast` docs for mor info.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to submit order.
        -  'item' (str): The item which you want to order.
    """

    validator = b.ValidateBreakfast(request.data, user, override_user)
    if validator.is_valid():
        validator.create_breakfast_order()
        message.add_message(
            request, "صبحانه با موفقیت ثبت شد.", message.SUCCESS
        )
        return Response(
            {"messages": message.messages(request)}, status.HTTP_201_CREATED
        )

    message.add_message(request, validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(request), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
def get_subsidy(request):
    date = b.validate_date(request.query_params.get("date"))
    if not date:
        message.add_message(
            request,
            "مشکلی در اعتبارسنجی درخواست شما رخ داده است.",
            Message.ERROR,
        )
        return Response(
            {
                "messages": message.messages(request),
                "errors": "Invalid 'date' value.",
            }
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


# todo shipment
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
    # todo shipment
    # token = find_token(request)
    # personnel = get_token_data(token, "username")
    #
    # full_name = get_token_data(token, "user_FullName")
    # is_admin = False
    # profile = profile_url(personnel)

    personnel = "e.rezaee@eit"
    full_name = "erfan rezaee"
    profile = ""
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

        response.set_cookie(
            "token", token, path=cookies_path, max_age=max_age, samesite="lax"
        )
        return response

    elif personnel_user_record.ExpiredAt < now.strftime("%Y/%m/%d"):
        # In this scenario, personnel's token is expired,
        # So we generate a new one, update the existing one in database,
        # and set the new token for personnel as a cookie.

        token = generate_token_hash(personnel, full_name, getrandbits(10))
        personnel_user_record.Token = token
        personnel_user_record.ExpiredAt = cookies_expire_time
        personnel_user_record.save()

        response.set_cookie(
            "token", token, path=cookies_path, max_age=max_age, samesite="lax"
        )
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
            samesite="lax",
        )

    return response


@api_view(["POST"])
@check([is_open_for_personnel])
@authenticate()
def change_delivery_building(request, user: User, override_user: User):
    validator = b.ValidateDeliveryBuilding(request.data, user, override_user)
    if validator.is_valid():
        validator.change_delivery_place()
        message.add_message(
            request, "محل تحویل سفارش با موفقیت تغییر یافت.", Message.SUCCESS
        )
        return Response(
            {"messages": message.messages(request)}, status.HTTP_200_OK
        )

    message.add_message(request, validator.message, Message.ERROR)
    return Response(
        {"messages": message.messages(request), "errors": validator.error},
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@check([is_open_for_admins])
@authenticate(privileged_users=True)
def available_users(request, user, override_user):
    qs = User.objects.all()
    return Response(data=UserSerializer(qs, many=True).data, status=200)


@api_view(["GET"])
@check([is_open_for_admins])
@authenticate(privileged_users=True)
def admin_manipulation_reasons(request, user, override_user):
    qs = AdminManipulationReason.objects.all()
    serializer = AdminManipulationReasonsSerializer(qs, many=True).data
    return Response(serializer, status.HTTP_200_OK)


@api_view(["GET", "PATCH"])
@check([is_open_for_admins])
@authenticate(privileged_users=True)
def deadline(request, user, override_user, weekday: int):
    if request.method == "GET":
        deadlines = get_list_or_404(Deadlines, WeekDay=weekday)
        serializer = DeadlineSerializer(deadlines, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = DeadlineSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    Deadlines.update(**serializer.validated_data, admin_user=user)

    return Response(status=status.HTTP_200_OK)
