from decimal import Decimal
from typing import TYPE_CHECKING, Any

import factory

from shop.catalog.models import Item
from shop.core.money import Currency
from shop.orders.models import Discount, Order, OrderItem, Tax

# factory_boy ships no type stubs, so each factory declares (only for the type
# checker) that calling it produces the model instance - which is exactly what
# DjangoModelFactory does at runtime.


class ItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Item

    name = factory.Sequence(lambda n: f"Item {n}")
    description = "A very nice item."
    price = Decimal("10.00")
    currency = Currency.USD

    if TYPE_CHECKING:

        def __new__(cls, *args: Any, **kwargs: Any) -> Item: ...  # type: ignore[misc]


class DiscountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Discount

    name = "Welcome discount"
    percent_off = Decimal("10.00")

    if TYPE_CHECKING:

        def __new__(cls, *args: Any, **kwargs: Any) -> Discount: ...  # type: ignore[misc]


class TaxFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tax

    name = "VAT"
    percentage = Decimal("20.00")
    is_inclusive = False

    if TYPE_CHECKING:

        def __new__(cls, *args: Any, **kwargs: Any) -> Tax: ...  # type: ignore[misc]


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    if TYPE_CHECKING:

        def __new__(cls, *args: Any, **kwargs: Any) -> Order: ...  # type: ignore[misc]


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    item = factory.SubFactory(ItemFactory)
    quantity = 1

    if TYPE_CHECKING:

        def __new__(cls, *args: Any, **kwargs: Any) -> OrderItem: ...  # type: ignore[misc]
