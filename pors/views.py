# import datetime
# from calendar import monthrange
#
# from django.shortcuts import get_list_or_404, render
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.generics import ListAPIView
# from rest_framework.response import Response
#
# from .models import Category, DailyMenuItem, Holiday, Item, Order, OrderItem
# from .serializers import (
#     AvailableItemsSerializer,
#     CategorySerializer,
#     DayMenuSerializer,
#     HolidaySerializer,
#     SelectedItemSerializer,
# )
# from .utils import first_and_last_day_date, get_weekend_holidays
#
# # Create your views here.
#
#
# def ui(request):
#     return render(request, "edari.html")
#
#
# class AvailableItems(ListAPIView):
#     """
#     تمام ایتم های موجود برگشت داده می‌شود.
#     """
#
#     queryset = Item.objects.filter(IsActive=True)
#     serializer_class = AvailableItemsSerializer
#
#
# @api_view(["GET"])
# def DayMenu(request):
#     """
#     این ویو مسئولیت ارائه منو غذایی مطابق پارامتر `date` را دارا است.
#     """
#     requested_date = request.query_params.get("date")
#     if not requested_date:
#         return Response(
#             "'date' parameter must be specified.",
#             status=status.HTTP_400_BAD_REQUEST,
#         )
#     queryset = get_list_or_404(DailyMenuItem, AvailableDate=requested_date)
#     serializer = DayMenuSerializer(data=queryset, many=True)
#     return Response(serializer.data, status.HTTP_200_OK)
#
#
# class Categories(ListAPIView):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer
#
#
# @api_view(["GET"])
# def calendar(request):
#     """
#     این ویو مسئولیت  ارائه روز های ماه و اطلاعات مربوط آن ها را دارد.
#     این اطلاعات شامل سفارشات روز و تعطیلی روز ها می‌باشد.
#     در صورت دریافت پارامتر های `month` و `year`, اطلاعات مربوط به تاریخ وارد شده ارائه داده می‌شود.
#     """
#     today = datetime.date.today()
#     year = request.query_params.get("year", today.year)
#     month = request.query_params.get("month", today.month)
#     last_day_week_num, last_day = monthrange(year, month)
#     first_day_week_num = datetime.datetime(year, month, 1).weekday()
#     first_day_date, last_day_date = first_and_last_day_date(month, year)
#     holidays = Holiday.objects.filter(
#         Date__range=(first_day_date, last_day_date)
#     )
#     weekend_holidays = get_weekend_holidays(year, month)
#     # Todo = Have no f.. idea how to map request user to the personnel yet.
#     selected_items = OrderItem.objects.filter(
#         OrderedFood__DelivaryDate__range=(first_day_date, last_day_date),
#         OrderedFood__Personnel=request.user,
#     )
#     selected_items_serializer = SelectedItemSerializer(
#         data={"date": selected_items.OrderedFood__id}, many=True
#     )
#     selected_items_list = [
#         selected_item["id"] for selected_item in selected_items_serializer.data
#     ]
#     holidays_serializer = HolidaySerializer(holidays, many=True)
#     holidays_list = [
#         holiday["DeliveryDate"] for holiday in holidays_serializer.data
#     ]
#     holidays_list += weekend_holidays
#     holidays_list.sort()
#     return Response(
#         {
#             "year": year,
#             "month": month,
#             "first": {"dayOfMonth": 1, "dayOfWeek": first_day_week_num},
#             "last": {"dayOfMonth": last_day, "dayOfWeek": last_day_week_num},
#             "holidays": holidays_list,
#             "selectedItems": selected_items_list,
#         }
#     )


