from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Prefetch, QuerySet
from django.shortcuts import get_object_or_404

from shop.core.money import quantize_money
from shop.orders.models import Order, OrderItem


@dataclass(frozen=True)
class OrderTotals:
    currency: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal


def _order_queryset() -> QuerySet[Order]:
    return Order.objects.select_related("discount", "tax").prefetch_related(
        Prefetch("order_items", queryset=OrderItem.objects.select_related("item"))
    )


def order_list() -> QuerySet[Order]:
    return _order_queryset()


def order_get(*, order_id: int) -> Order:
    return get_object_or_404(_order_queryset(), id=order_id)


def order_totals(*, order: Order) -> OrderTotals:
    """
    Money math for an order, mirroring how Stripe computes a Checkout Session:
    the discount is applied to the subtotal first, the tax rate afterwards.
    """
    currency = order.currency
    subtotal = quantize_money(
        sum((order_item.amount for order_item in order.order_items.all()), Decimal("0"))
    )

    discount = order.applied_discount
    discount_amount = quantize_money(subtotal * discount.percent_off / 100) if discount else Decimal("0.00")

    taxable_amount = subtotal - discount_amount

    tax = order.applied_tax
    tax_amount = Decimal("0.00")

    if tax:
        if tax.is_inclusive:
            # The tax is already part of the price, it is only broken out for display.
            tax_amount = quantize_money(taxable_amount * tax.percentage / (100 + tax.percentage))
        else:
            tax_amount = quantize_money(taxable_amount * tax.percentage / 100)

    total = taxable_amount if (tax and tax.is_inclusive) else taxable_amount + tax_amount

    return OrderTotals(
        currency=currency,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        total=quantize_money(total),
    )
