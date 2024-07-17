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


@register.filter()
def english_to_persian_number(value) -> str:
    output_string = "".join(
        persian_numbers.get(char, char) for char in str(value)
    )
    return output_string
