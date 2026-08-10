from decimal import Decimal

import pytest

from shop.core.exceptions import ApplicationError
from shop.core.money import resolve_single_currency, to_minor_units


class TestToMinorUnits:
    def test_two_decimal_currency_is_converted_to_cents(self):
        assert to_minor_units(Decimal("10.50"), "usd") == 1050

    def test_rounding_is_half_up(self):
        assert to_minor_units(Decimal("0.005"), "usd") == 1

    def test_zero_decimal_currency_is_not_multiplied(self):
        assert to_minor_units(Decimal("500"), "jpy") == 500


class TestResolveSingleCurrency:
    def test_returns_the_common_currency(self):
        assert resolve_single_currency(["usd", "usd"]) == "usd"

    def test_rejects_mixed_currencies(self):
        with pytest.raises(ApplicationError) as exc_info:
            resolve_single_currency(["usd", "eur"])

        assert exc_info.value.extra == {"currencies": ["eur", "usd"]}

    def test_rejects_empty_input(self):
        with pytest.raises(ApplicationError):
            resolve_single_currency([])
