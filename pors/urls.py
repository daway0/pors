from django.urls import path

from . import report_views, views

app_name = "pors"

urlpatterns = [
    path("calendar/", views.personnel_calendar, name="calendar"),
    path("create-order/", views.create_order_item, name="order"),
    path(
        "create-breakfast-order/",
        views.create_breakfast_order,
        name="breakfast_order",
    ),
    path(
        "administrative/reports/item-ordering-personnel-list/",
        views.item_ordering_personnel_list_report,
        name="item_ordering_personnel_list_report",
    ),
    path("administrative/calendar/", views.edari_calendar, name="acalendar"),
    path("panel/", views.first_page, name="apanel"),
    path(
        "all-items/",
        views.AllItems.as_view(),
        name="all_items",
    ),
    path(
        "administrative/add-item-to-menu/",
        views.add_item_to_menu,
        name="aadd_item_to_menu",
    ),
    path(
        "administrative/remove-item-from-menu/",
        views.remove_item_from_menu,
        name="aremove_item_from_menu",
    ),
    path(
        "remove-item-from-order/",
        views.remove_order_item,
        name="remove_order_item",
    ),
    path("get-subsidy/", views.get_subsidy, name="get_subsidy"),
    # path(
    #     "change-delivery-place/",
    #     views.change_delivery_place,
    #     name="change_delivery_place",
    # ),
    path(
        "items-daily-report/",
        report_views.items_daily_report,
        name="items_daily_report",
    ),
    path(
        "personnel-financial-report/",
        report_views.personnel_financial_report,
        name="personnel_financial_report",
    ),
    path("", views.uiadmin),
    path("personnel/", views.ui),
]
