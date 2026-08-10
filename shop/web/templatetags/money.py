from decimal import Decimal

from django import template

from shop.core.money import CURRENCY_SYMBOLS

register = template.Library()


@register.filter
def money(amount: Decimal, currency: str) -> str:
    """`{{ totals.total|money:totals.currency }}` -> `€12.00`"""
    return f"{CURRENCY_SYMBOLS.get(currency, '')}{amount:.2f}"
