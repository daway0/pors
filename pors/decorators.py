import functools
from typing import Callable

from django.http.response import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from . import models as m
from .messages import Message

messages = Message()


def is_open_for_admins() -> bool:
    """Returning current system state for admin users."""

    return m.SystemSetting.objects.last().IsSystemOpenForAdmin


def is_open_for_personnel() -> bool:
    """Returning current system state for personnel."""

    return m.SystemSetting.objects.last().IsSystemOpenForPersonnel


def check(what_to_check: list[Callable]):
    """
    This decorator will run several checker functions that lookup
        for system's current state.
    If the checker functions pass, the view will get executed successfully.
    Checker functions are received from args as a list of functions,
        and will run recursively.

    Examples:
        ```python
        @check([is_open_for_admins, is_open_for_personnel])
        def some_view(request):
            ...
        ```

    Args:
        what_to_check: List of checker functions.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            for checker in what_to_check:
                if not checker():
                    messages.add_message(
                        "سیستم در حال حاضر از دسترس خارج است.", Message.ERROR
                    )
                    return Response(
                        {
                            "messages": messages.messages(),
                            "errors": "System is down!",
                        },
                        status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def authenticate(privileged_users: bool = False):
    """
    Authenticating users based on the `key` token.
    If the authentication fails, the personnel will get redirected
        to the authentication gateway.

    If the `privileged_users` is set, will also check the personnel's role
        in database via `IsAdmin` field.

    Args:
        privileged_users (bool): Does this view requires admin privilege.
    """

    def decorator(view: Callable):
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            token = request.COOKIES.get("token")
            gateway_url = reverse("pors:gateway")
            if not token:
                return HttpResponseRedirect(redirect_to=gateway_url)

            user = m.User.objects.filter(Key=token, IsActive=True).first()
            if not user:
                return HttpResponseRedirect(redirect_to=gateway_url)

            if privileged_users and not user.IsAdmin:
                return HttpResponseForbidden(
                    "You are not authorized to access this api with current"
                    " privilege ;)."
                )

            return view(request, *args, **kwargs)

        return wrapper

    return decorator
