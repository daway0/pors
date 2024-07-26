import jdatetime
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from pors.business import get_first_orderable_date, is_date_valid_for_action
from pors.models import (
    Deadlines,
    EmailReason,
    EmailReminderHistory,
    MealTypeChoices,
    SystemSetting,
)
from pors.utils import (
    execute_raw_sql_with_params,
    localnow,
    order_link,
    send_email_notif,
    split_dates,
    weekday_to_word,
)


class Command(BaseCommand):
    help = "send reminder notification to users who haven't \
    submitted an order for that day"

    def handle(self, *args, **options):
        reminders, date = self._check_deadlines()
        str_date = date.strftime("%Y/%m/%d")
        history = EmailReminderHistory.objects.filter(RemindDate=str_date)

        settings = SystemSetting.objects.first()
        sent = False
        now = localnow()

        day_diff = date.day - now.day
        if day_diff == 0:
            day_word = "امروز"
        elif day_diff == 1:
            day_word = "فردا"
        else:
            day_word = weekday_to_word(date.weekday())

        if all(
            [*reminders.values(), settings.BRFReminder, settings.LNCReminder]
        ) and len(history) < len(MealTypeChoices.values):
            # Here we send notification for all mealtypes, even if
            # we already sent a notif for one of them already.

            self.stdout.write(
                self.style.SUCCESS(
                    "Sending email notification for all meal types."
                )
            )
            self._send_alltypes_notif(date, day_word)
            EmailReminderHistory.objects.bulk_create(
                [
                    EmailReminderHistory(
                        RemindDate=str_date, MealType=meal_type
                    )
                    for meal_type in MealTypeChoices.values
                ]
            )
            return

        for meal_type, valid in reminders.items():
            if (
                not valid
                or not getattr(settings, f"{meal_type}Reminder")
                or history.filter(MealType=meal_type).exists()
            ):
                continue
            sent = True
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sending email notification for {meal_type}."
                )
            )
            self._send_typed_notif(date, meal_type, day_word)
            EmailReminderHistory.objects.create(
                RemindDate=str_date, MealType=meal_type
            )

        if not sent:
            self.stdout.write(
                self.style.WARNING(
                    "Now is not the time for reminder notification "
                    + "or an email notification has already been sent."
                )
            )

    def _send_typed_notif(
        self, date: jdatetime.datetime, meal_type: str, day_word: str
    ):
        str_date = date.strftime("%Y/%m/%d")
        with open("./pors/SQLs/UsersWithoutMealTypedOrder.sql", "r") as f:
            query = f.read()

        emails = execute_raw_sql_with_params(
            query, (str_date, meal_type), raw=True
        )
        link = order_link(str_date, meal_type)
        message = render_to_string(
            "emails/reminder.html",
            {
                "mealtype": MealTypeChoices(meal_type).label,
                "date": str_date,
                "link": link,
                "day_word": day_word,
                f"{meal_type.lower()}_deadline": Deadlines.objects.filter(
                    WeekDay=date.weekday(), MealType=meal_type
                )
                .first()
                .Hour,
            },
        )
        send_email_notif(
            subject="یادآوری ثبت سفارش",
            message=message,
            emails=emails,
            reason=getattr(EmailReason, f"REMINDER_{meal_type}"),
            max_tries=3,
        )

    def _send_alltypes_notif(self, date: jdatetime.datetime, day_word: str):
        str_date = date.strftime("%Y/%m/%d")
        with open("./pors/SQLs/UsersWithoutOrderAll.sql", "r") as f:
            query = f.read()

        emails = execute_raw_sql_with_params(query, (str_date,), raw=True)
        link = order_link(str_date)

        message = render_to_string(
            "emails/reminder.html",
            {
                "mealtype": " و ".join(MealTypeChoices.labels),
                "date": str_date,
                "link": link,
                "day_word": day_word,
                "brf_deadline": Deadlines.objects.filter(
                    WeekDay=date.weekday(),
                    MealType=MealTypeChoices.BREAKFAST,
                )
                .first()
                .Hour,
                "lnc_deadline": Deadlines.objects.filter(
                    WeekDay=date.weekday(), MealType=MealTypeChoices.LAUNCH
                )
                .first()
                .Hour,
            },
        )

        send_email_notif(
            subject="یادآوری ثبت سفارش",
            message=message,
            emails=emails,
            reason=EmailReason.REMINDER_ALL,
            max_tries=3,
        )

    def _check_deadlines(self) -> tuple[dict, jdatetime.datetime]:
        now = localnow()
        reminders = {
            MealTypeChoices.BREAKFAST: False,
            MealTypeChoices.LAUNCH: False,
        }

        deadlines = Deadlines.objects.all()
        remind_before = SystemSetting.objects.first().RemindBefore

        deadlines = {
            MealTypeChoices.BREAKFAST: deadlines.filter(
                MealType=MealTypeChoices.BREAKFAST
            ),
            MealTypeChoices.LAUNCH: deadlines.filter(
                MealType=MealTypeChoices.LAUNCH
            ),
        }

        year, month, day = get_first_orderable_date(
            now,
            breakfast_deadlines=deadlines[MealTypeChoices.BREAKFAST],
            launch_deadlines=deadlines[MealTypeChoices.LAUNCH],
        )
        date = jdatetime.datetime(
            year, month, day, now.hour, now.minute, now.second
        )

        for mealtype in MealTypeChoices.values:
            deadline = deadlines[mealtype].get(WeekDay=date.weekday())

            valid_for_action = is_date_valid_for_action(
                now, date.strftime("%Y/%m/%d"), deadline.Days, deadline.Hour
            )
            if not valid_for_action:
                continue

            days_dif = date.day - now.day
            if days_dif - deadline.Days > 0:
                continue

            hour_diff = abs(
                deadlines[mealtype].get(WeekDay=date.weekday()).Hour
                - date.hour
            )
            if hour_diff * 60 - date.minute < remind_before:
                reminders[mealtype] = True

        return reminders, date
