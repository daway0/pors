import functools

from rest_framework import status
from rest_framework.response import Response

from . import models as m
from .messages import Message

messages = Message()


def is_open_for_admins():
    return m.SystemSetting.objects.last().IsSystemOpenForAdmin


def is_open_for_personnel():
    return m.SystemSetting.objects.last().IsSystemOpenForPersonnel


def check(what_to_check):
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
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator
