from decimal import Decimal

import factory

from shop.catalog.models import Item
from shop.core.money import Currency
from shop.orders.models import Discount, Order, OrderItem, Tax


class ItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Item

    name = factory.Sequence(lambda n: f"Item {n}")
    description = "A very nice item."
    price = Decimal("10.00")
    currency = Currency.USD


class DiscountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Discount

    name = "Welcome discount"
    percent_off = Decimal("10.00")


class TaxFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tax

    name = "VAT"
    percentage = Decimal("20.00")
    is_inclusive = False


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    item = factory.SubFactory(ItemFactory)
    quantity = 1
