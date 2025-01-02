import datetime
from django import template

register = template.Library()


@register.filter
def is_past_date(date):
    if date and isinstance(date, datetime.date):
        return date < datetime.date.today()  # Compare with current date
    return False

@register.filter
def is_delay(date):
    if date and isinstance(date, datetime.date):
        return date < datetime.date.today()
    return False
