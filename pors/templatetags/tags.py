from django import template

register = template.Library()

persian_numbers = {
    "0": "۰",
    "1": "۱",
    "2": "۲",
    "3": "۳",
    "4": "۴",
    "5": "۵",
    "6": "۶",
    "7": "۷",
    "8": "۸",
    "9": "۹",
}

persian_weekdays = {
    "0": "شنبه",
    "1": "یک‌شنبه",
    "2": "دوشنبه",
    "3": "سه‌شنبه",
    "4": "چهار‌شنبه",
    "5": "بنج‌شنبه",
    "6": "جمعه",
}


@register.filter()
def english_to_persian_number(value) -> str:
    output_string = "".join(
        persian_numbers.get(char, char) for char in str(value)
    )
    return output_string


@register.filter()
def weekday_word(weeknumber) -> str:
    return persian_weekdays.get(str(weeknumber))