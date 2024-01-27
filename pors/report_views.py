from django.db.models import Count, Sum
from django.http.response import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import business as b
from . import decorators as decs
from . import models as m
from . import utils as u
from .messages import Message

message = Message()


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
@decs.authenticate(privileged_users=True)
def personnel_daily_report(request, current_user):
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

    queryset = m.PersonnelDailyReport.objects.filter(DeliveryDate=date)
    if not queryset:
        message.add_message(
            "هیچ رکوردی بین بازه ارائه داده شده موجود نیست.", Message.ERROR
        )
        return Response(
            {"messages": message.messages(), "errors": "Queryset is empty!"},
            status.HTTP_404_NOT_FOUND,
        )

    response = u.generate_csv(queryset)

    return response


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
@decs.authenticate(privileged_users=True)
def personnel_financial_report(request, current_user):
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

    result = orders.values(
        "Personnel", "FirstName", "LastName"
    ).annotate(
        TotalOrders=Count("Id"),
        TotalPrice=Sum("TotalPrice"),
        TotalSubsidySpent=Sum("SubsidySpent"),
        TotalPersonnelDebt=Sum("PersonnelDebt"),
    )
    if not result:
        message.add_message(
            "هیچ رکوردی بین بازه ارائه داده شده موجود نیست.", Message.ERROR
        )
        return Response(
            {"messages": message.messages(), "errors": "Queryset is empty!"},
            status.HTTP_404_NOT_FOUND,
        )

    csv_content = u.generate_csv(result)
    return csv_content


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
@decs.authenticate(privileged_users=True)
def item_ordering_personnel_list_report(request, current_user):
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
        return Response(
            {"messages": message.messages(), "errors": str(err)},
            status.HTTP_400_BAD_REQUEST,
        )

    # query sets that are in report must have .values for specifying columns
    personnel = m.PersonnelDailyReport.objects.filter(
        DeliveryDate=date, ItemId=item_id
    ).values(
        "Personnel",
        "FirstName",
        "LastName",
        "ItemName",
        "Quantity",
        "DeliveryDate",
    )
    if not personnel:
        message.add_message(
            "هیچ رکوردی بین بازه ارائه داده شده موجود نیست.", Message.ERROR
        )
        return Response(
            {"messages": message.messages(), "errors": "Queryset is empty!"},
            status.HTTP_404_NOT_FOUND,
        )

    csv_content = u.generate_csv(personnel)

    response = HttpResponse(
        content=csv_content,
        content_type="text/csv",
    )
    return response
