from django import template

register = template.Library()


@register.filter
def money(value):
    try:
        return f'Rs. {value:,.2f}'
    except (TypeError, ValueError):
        return 'Rs. 0.00'


@register.filter
def times(value):
    return range(int(value or 0))
