from django.db.models import Count, Sum
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import business as b
from . import decorators as decs
from . import models as m
from . import serializers as s
from . import utils as u
from .messages import Message

message = Message()


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
@decs.authenticate(privileged_users=True)
def food_provider_daily_ordering_report(request, user: m.User, override_user: m.User):
    schema = {"date": ""}
    try:
        u.validate_request_based_on_schema(schema, request.data)
    except ValueError as err:
        return Response({"errors": str(err)}, status.HTTP_400_BAD_REQUEST)

    date = u.validate_date(request.data.get("date"))

    queryset = m.FoodProviderOrdering.objects.filter(DeliveryDate=date).order_by(
        "MealType",
        "FoodProvider",
        "DeliveryBuilding").values(
        "ItemName",
        "ItemTotalCount",
        "DeliveryBuildingPersian",
        "FoodProviderPersian",
    )
    if not queryset:
        return u.raise_report_notfound(message, request)

    providers = queryset.values_list("FoodProviderPersian", flat=True)
    response = u.queryset_to_xlsx_response_food_provider_ordering(queryset, [
        "آیتم",
        "تعداد",
        "محل تحویل",
        "تامین کننده"
    ], providers)

    m.ActionLog.objects.log(
        m.ActionLog.ActionTypeChoices.CREATE,
        user,
        f"Food Provider Ordering report generated for {date}",
        m.PersonnelDailyReport
    )

    return response

@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
@decs.authenticate(privileged_users=True)
def personnel_daily_report(request, user: m.User, override_user: m.User):
    """
    Generating CSV based report for personnel's orders on each day.

    Args:
        request (dict): Request data which must contains:
        -  'date' (str): The date which you want to look for.
    """

    schema = {"date": ""}
    try:
        u.validate_request_based_on_schema(schema, request.data)
    except ValueError as err:
        return Response({"errors": str(err)}, status.HTTP_400_BAD_REQUEST)

    date = u.validate_date(request.data.get("date"))

    queryset = m.PersonnelDailyReport.objects.filter(DeliveryDate=date).order_by("-DeliveryDate", "Personnel").values(
        "NationalCode",
        "Personnel",
        "FirstName",
        "LastName",
        "ItemName",
        "Quantity",
        "DeliveryDate",
        "DeliveryBuildingPersian",
        "DeliveryFloorPersian"
    )
    if not queryset:
        return u.raise_report_notfound(message, request)

    response = u.queryset_to_xlsx_response(queryset, [
        "کد ملی",
        "نام کاربری",
        "نام",
        "نام خانوادگی",
        "ایتم",
        "تعداد",
        "زمان تحویل",
        "ساختمان تحویل",
        "طبقه تحویل"
    ])

    m.ActionLog.objects.log(
        m.ActionLog.ActionTypeChoices.CREATE,
        user,
        f"Daily Orders report generated for {date}",
        m.PersonnelDailyReport
    )

    return response


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
@decs.authenticate(privileged_users=True)
def personnel_financial_report(request, user: m.User, override_user: m.User):
    """
    Returning monthly financial report for each personel on the provided date.

    Args:
        request (dict): Request data which must contains:
        -  'month' (int): The month which you want to look for.
        -  'year' (int): The year which you want to look for.
    """

    schema = {"year": 0, "month": 0}
    try:
        u.validate_request_based_on_schema(schema, request.data)
    except ValueError as err:
        return Response({"errors": str(err)}, status.HTTP_400_BAD_REQUEST)

    month = request.data.get("month")
    year = request.data.get("year")

    if 12 < month < 0:
        return Response(
            {"errors": "Invalid month value."}, status.HTTP_400_BAD_REQUEST
        )

    first_date, last_date = u.first_and_last_day_date(month, year)

    orders = m.Order.objects.filter(
        DeliveryDate__range=[first_date, last_date]
    )

    result = orders.values("Personnel", "FirstName", "LastName").annotate(
        TotalOrders=Count("Id"),
        TotalPrice=Sum("TotalPrice"),
        TotalSubsidySpent=Sum("SubsidySpent"),
        TotalPersonnelDebt=Sum("PersonnelDebt"),
    )
    if not result:
        return u.raise_report_notfound(message, request)

    m.ActionLog.objects.log(
        m.ActionLog.ActionTypeChoices.CREATE,
        user,
        f"Monthly Financial report generated for year {year} and month "
        f"{month}",
        m.Order
    )
    csv_content = u.generate_csv(result)
    return csv_content


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
@decs.authenticate(privileged_users=True)
def item_ordering_personnel_list_report(
        request, user: m.User, override_user: m.User
):
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
            request,
            "مشکلی در اعتبارسنجی درخواست شما رخ داده است.",
            Message.ERROR,
        )
        return Response(
            {"messages": message.messages(request), "errors": str(err)},
            status.HTTP_400_BAD_REQUEST,
        )

    # query sets that are in report must have .values for specifying columns
    res = m.PersonnelDailyReport.objects.filter(
        DeliveryDate=date, ItemId=item_id
    ).order_by("-DeliveryDate").values(
        "NationalCode",
        "Personnel",
        "FirstName",
        "LastName",
        "ItemName",
        "Quantity",
        "DeliveryDate",
        "DeliveryBuildingPersian",
        "DeliveryFloorPersian",
    )
    if not res:
        return u.raise_report_notfound(message, request)

    response = u.queryset_to_xlsx_response(res, [
        "کد ملی",
        "نام کاربری",
        "نام",
        "نام خانوادگی",
        "ایتم",
        "تعداد",
        "زمان تحویل",
        "ساختمان تحویل",
        "طبقه تحویل"
    ])
    item = m.Item.objects.filter(id=item_id).first()
    m.ActionLog.objects.log(
        m.ActionLog.ActionTypeChoices.CREATE,
        user,
        f"Item Orders report generated for item {item.ItemName} for {date}",
        m.PersonnelDailyReport
    )

    return response


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
@decs.authenticate(privileged_users=True)
def personnel_monthly_report(request, user: m.User, override_user: m.User):
    serializer = s.PersonnelMonthlyReport(data=request.data)
    if not serializer.is_valid():
        return Response("Invalid request.", status.HTTP_400_BAD_REQUEST)

    month = serializer.validated_data.get("month")
    year = serializer.validated_data.get("year")
    first_date, last_date = u.first_and_last_day_date(month, year)
    qs = m.PersonnelDailyReport.objects.filter(
        DeliveryDate__range=[first_date, last_date]
    ).order_by("-DeliveryDate").values(
        "NationalCode",
        "Personnel",
        "FirstName",
        "LastName",
        "ItemName",
        "Quantity",
        "DeliveryDate",
        "DeliveryBuildingPersian",
        "DeliveryFloorPersian",
    )
    if not qs:
        return u.raise_report_notfound(message, request)

    response = u.queryset_to_xlsx_response(qs, [
        "کد ملی",
        "نام کاربری",
        "نام",
        "نام خانوادگی",
        "ایتم",
        "تعداد",
        "زمان تحویل",
        "ساختمان تحویل",
        "طبقه تحویل"
    ])
    m.ActionLog.objects.log(
        m.ActionLog.ActionTypeChoices.CREATE,
        user,
        f"Monthly Orders report generated for year {year} and month {month}",
        m.PersonnelDailyReport
    )

    return response
