from decimal import ROUND_HALF_UP, Decimal

from django.db import models

MONEY_QUANTUM = Decimal("0.01")


class Currency(models.TextChoices):
    USD = "usd", "USD"
    EUR = "eur", "EUR"


CURRENCY_SYMBOLS = {
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
