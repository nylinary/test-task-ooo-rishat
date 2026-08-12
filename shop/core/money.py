from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

from django.db import models

from shop.core.exceptions import ApplicationError

MONEY_QUANTUM = Decimal("0.01")


class Currency(models.TextChoices):
    USD = "usd", "USD"
    EUR = "eur", "EUR"


# Keyed by plain `str`: lookups use model field values, not enum members.
CURRENCY_SYMBOLS: dict[str, str] = {
    Currency.USD: "$",
    Currency.EUR: "€",
}

# https://docs.stripe.com/currencies#zero-decimal
ZERO_DECIMAL_CURRENCIES = frozenset(
    {
        "bif",
        "clp",
        "djf",
        "gnf",
        "jpy",
        "kmf",
        "krw",
        "mga",
        "pyg",
        "rwf",
        "ugx",
        "vnd",
        "vuv",
        "xaf",
        "xof",
        "xpf",
    }
)


def quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def to_minor_units(amount: Decimal, currency: str) -> int:
    """
    Convert a decimal amount into the smallest currency unit, as Stripe
    expects it (e.g. `Decimal("10.50")` + "usd" -> 1050 cents).
    """
    if currency.lower() in ZERO_DECIMAL_CURRENCIES:
        return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def resolve_single_currency(currencies: Iterable[str]) -> str:
    """
    A payment happens in exactly one currency, so a set of items that is paid
    for together has to agree on it.
    """
    distinct = set(currencies)

    if not distinct:
        raise ApplicationError("Нет товаров, по которым можно определить валюту.")

    if len(distinct) > 1:
        raise ApplicationError(
            "Все товары должны быть в одной валюте, чтобы оплатить их вместе.",
            extra={"currencies": sorted(distinct)},
        )

    return distinct.pop()
