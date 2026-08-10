from collections.abc import Sequence
from dataclasses import dataclass

from django.db import transaction

from shop.catalog.models import Item
from shop.core.exceptions import ApplicationError
from shop.core.money import resolve_single_currency
from shop.orders.models import Discount, Order, OrderItem, Tax


@dataclass(frozen=True)
class OrderLine:
    item: Item
    quantity: int = 1


@transaction.atomic
def order_create(
    *,
    lines: Sequence[OrderLine],
    discount: Discount | None = None,
    tax: Tax | None = None,
    customer_email: str = "",
) -> Order:
    if not lines:
        raise ApplicationError("An order must contain at least one item.")

    if any(line.quantity < 1 for line in lines):
        raise ApplicationError("Item quantity must be at least 1.")

    item_ids = [line.item.id for line in lines]

    if len(set(item_ids)) != len(item_ids):
        raise ApplicationError("An item can only be added to an order once, use `quantity` instead.")

    # Fails loudly for mixed-currency orders, which cannot be charged as a
    # single Stripe payment.
    resolve_single_currency({line.item.currency for line in lines})

    order = Order(customer_email=customer_email, discount=discount, tax=tax)
    order.full_clean()
    order.save()

    OrderItem.objects.bulk_create(
        [OrderItem(order=order, item=line.item, quantity=line.quantity) for line in lines]
    )

    return order
