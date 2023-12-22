from django.db.models import Count, F, Sum, Window
from django.db.models.functions import RowNumber
from django.http.response import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import decorators as decs
from . import models as m
from . import serializers as s
from . import utils as u
from .messages import Message

message = Message()


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
def items_daily_report(request):
    schema = {"date": ""}
    try:
        u.validate_request(schema, request.data)
    except ValueError as err:
        return Response({"errors": str(err)})

    date = u.validate_date(request.data.get("date"))

    queryset = m.PersonnelDailyReport.objects.filter(DeliveryDate=date)
    if not queryset:
        message.add_message(
            "هیچ رکوردی بین بازه ارائه داده شده موجود نیست.", Message.ERROR
        )
        return Response(
            {"messages": message.messages(), "errors": "Queryset is empty!"}
        )

    response = u.generate_csv(queryset)

    return response


@api_view(["POST"])
@decs.check([decs.is_open_for_admins])
def personnel_financial_report(request):
    schema = {"firstDate": "", "lastDate": ""}
    try:
        u.validate_request(schema, request.data)
    except ValueError as err:
        return Response({"errors": str(err)})

    first_date = u.validate_date(request.data.get("firstDate"))
    last_date = u.validate_date(request.data.get("lastDate"))

    orders = m.Order.objects.filter(
        DeliveryDate__range=[first_date, last_date]
    )

    result = orders.values("Personnel", "FirstName", "LastName", "TeamName", "RoleName").annotate(
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
            {"messages": message.messages(), "errors": "Queryset is empty!"}
        )

    csv_content = u.generate_csv(result)
    return csv_content
