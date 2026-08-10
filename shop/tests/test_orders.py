from decimal import Decimal

import pytest

from shop.core.exceptions import ApplicationError
from shop.core.money import Currency
from shop.orders.selectors import order_totals
from shop.orders.services import OrderLine, order_create
from shop.tests.factories import DiscountFactory, ItemFactory, OrderItemFactory, TaxFactory

pytestmark = pytest.mark.django_db


class TestOrderCreate:
    def test_creates_order_with_items(self):
        item_a = ItemFactory(price=Decimal("10.00"))
        item_b = ItemFactory(price=Decimal("5.00"))

        order = order_create(lines=[OrderLine(item=item_a), OrderLine(item=item_b, quantity=3)])

        assert order.order_items.count() == 2
        assert order_totals(order=order).subtotal == Decimal("25.00")

    def test_rejects_empty_order(self):
        with pytest.raises(ApplicationError):
            order_create(lines=[])

    def test_rejects_mixed_currencies(self):
        usd_item = ItemFactory(currency=Currency.USD)
        eur_item = ItemFactory(currency=Currency.EUR)

        with pytest.raises(ApplicationError):
            order_create(lines=[OrderLine(item=usd_item), OrderLine(item=eur_item)])

    def test_rejects_duplicate_items(self):
        item = ItemFactory()

        with pytest.raises(ApplicationError):
            order_create(lines=[OrderLine(item=item), OrderLine(item=item)])


class TestOrderTotals:
    def test_subtotal_multiplies_by_quantity(self):
        order_item = OrderItemFactory(item__price=Decimal("10.00"), quantity=3)

        totals = order_totals(order=order_item.order)

        assert totals.subtotal == Decimal("30.00")
        assert totals.total == Decimal("30.00")

    def test_discount_is_applied_before_tax(self):
        # 100 - 10% = 90, then 20% tax on 90 = 18 -> 108 total.
        order_item = OrderItemFactory(
            item__price=Decimal("100.00"),
            order__discount=DiscountFactory(percent_off=Decimal("10.00")),
            order__tax=TaxFactory(percentage=Decimal("20.00")),
        )

        totals = order_totals(order=order_item.order)

        assert totals.discount_amount == Decimal("10.00")
        assert totals.tax_amount == Decimal("18.00")
        assert totals.total == Decimal("108.00")

    def test_inclusive_tax_does_not_change_the_total(self):
        # 20% inclusive tax on 120 -> the tax share is 20, the total stays 120.
        order_item = OrderItemFactory(
            item__price=Decimal("120.00"),
            order__tax=TaxFactory(percentage=Decimal("20.00"), is_inclusive=True),
        )

        totals = order_totals(order=order_item.order)

        assert totals.tax_amount == Decimal("20.00")
        assert totals.total == Decimal("120.00")

    def test_inactive_discount_and_tax_are_ignored(self):
        order_item = OrderItemFactory(
            item__price=Decimal("100.00"),
            order__discount=DiscountFactory(is_active=False),
            order__tax=TaxFactory(is_active=False),
        )

        totals = order_totals(order=order_item.order)

        assert totals.discount_amount == Decimal("0.00")
        assert totals.tax_amount == Decimal("0.00")
        assert totals.total == Decimal("100.00")

    def test_mixed_currency_order_raises(self):
        usd_item = OrderItemFactory(item__currency=Currency.USD)
        OrderItemFactory(order=usd_item.order, item__currency=Currency.EUR)

        with pytest.raises(ApplicationError):
            order_totals(order=usd_item.order)
