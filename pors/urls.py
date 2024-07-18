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
        "administrative/reports/specific-item/",
        report_views.item_ordering_personnel_list_report,
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
    path("change_order_delivery_place/", views.change_delivery_building),
    path(
        "administrative/reports/daily-orders/",
        report_views.personnel_daily_report,
        name="personnel_daily_report",
    ),
    path(
        "administrative/reports/daily-foodprovider-ordering/",
        report_views.food_provider_daily_ordering_report,
        name="foodprovider_daily_report",
    ),
    path(
        "administrative/reports/monthly-orders/",
        report_views.personnel_monthly_report,
    ),
    path(
        "administrative/reports/monthly-financial/",
        report_views.personnel_financial_report,
        name="personnel_financial_report",
    ),
    path("auth-gateway/", views.auth_gateway, name="gateway"),
    path("admin/", views.uiadmin, name="admin_panel"),
    path("", views.ui, name="personnel_panel"),
    path("available-users/", views.available_users, name="available_users"),
    path(
        "administrative/reasons/",
        views.admin_manipulation_reasons,
        name="manipulation_reasons",
    ),
    path("administrative/deadlines/", views.deadlines, name="deadlines"),
    path(
        "items/<int:item_id>/",
        views.item,
        name="item",
    ),
    path("administrative/notes/", views.note, name="note"),
]
