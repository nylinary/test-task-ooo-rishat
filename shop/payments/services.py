"""
Business logic that turns our models into Stripe payments.

`shop.integrations.stripe.gateway` does the talking to Stripe, this module
decides *what* to send: which keypair (currency), which line items, which
coupon and tax rate.
"""

from shop.catalog.models import Item
from shop.core.money import to_minor_units
from shop.integrations.stripe import gateway
from shop.orders.models import Discount, Order, Tax
from shop.orders.selectors import order_totals


def create_checkout_session_for_item(
    *,
    item: Item,
    success_url: str,
    cancel_url: str,
) -> gateway.CheckoutSession:
    return gateway.create_checkout_session(
        currency=item.currency,
        line_items=[
            gateway.LineItem(
                name=item.name,
                description=item.description,
                unit_amount=to_minor_units(item.price, item.currency),
                quantity=1,
            )
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"item_id": str(item.id)},
    )


def create_checkout_session_for_order(
    *,
    order: Order,
    success_url: str,
    cancel_url: str,
) -> gateway.CheckoutSession:
    """
    Charge a whole order in one Checkout Session.

    The discount and the tax are passed to Stripe as first-class objects
    (a Coupon and a Tax Rate), so they show up as separate lines in the
    Checkout form instead of being baked into the price.
    """
    currency = order.currency

    tax = order.applied_tax
    tax_rate_ids = [stripe_tax_rate_id(tax=tax, currency=currency)] if tax else []

    discount = order.applied_discount
    coupon_id = stripe_coupon_id(discount=discount, currency=currency) if discount else None

    line_items = [
        gateway.LineItem(
            name=order_item.item.name,
            description=order_item.item.description,
            unit_amount=to_minor_units(order_item.item.price, currency),
            quantity=order_item.quantity,
            tax_rate_ids=tax_rate_ids,
        )
        for order_item in order.order_items.all()
    ]

    return gateway.create_checkout_session(
        currency=currency,
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        coupon_id=coupon_id,
        customer_email=order.customer_email,
        metadata={"order_id": str(order.id)},
    )


def create_payment_intent_for_order(*, order: Order) -> gateway.PaymentIntent:
    """
    Charge a whole order with a Payment Intent instead of a Checkout Session.

    A Payment Intent is a single amount - it has no line items, coupons or tax
    rates - so the discount and the tax are applied by us (see `order_totals`)
    before the amount is sent to Stripe.
    """
    totals = order_totals(order=order)

    return gateway.create_payment_intent(
        currency=totals.currency,
        amount=to_minor_units(totals.total, totals.currency),
        description=f"Order #{order.id}",
        receipt_email=order.customer_email,
        metadata={"order_id": str(order.id)},
    )


def stripe_coupon_id(*, discount: Discount, currency: str) -> str:
    """
    Return the Stripe Coupon for a discount, creating it on first use.

    Stripe objects belong to a single Stripe account, and the account depends
    on the currency - hence a cache per currency. The percentage is part of the
    cache key because a Stripe Coupon is immutable: editing the discount in the
    admin has to produce a new coupon.
    """
    cache_key = f"{currency}:{discount.percent_off:.2f}"
    coupon_id = discount.stripe_coupon_ids.get(cache_key)

    if coupon_id:
        return coupon_id

    coupon_id = gateway.create_coupon(
        currency=currency,
        name=discount.name,
        percent_off=discount.percent_off,
    )

    discount.stripe_coupon_ids[cache_key] = coupon_id
    discount.save(update_fields=["stripe_coupon_ids", "updated_at"])

    return coupon_id


def stripe_tax_rate_id(*, tax: Tax, currency: str) -> str:
    """Return the Stripe Tax Rate for a tax, creating it on first use."""
    cache_key = f"{currency}:{tax.percentage:.2f}:{'inclusive' if tax.is_inclusive else 'exclusive'}"
    tax_rate_id = tax.stripe_tax_rate_ids.get(cache_key)

    if tax_rate_id:
        return tax_rate_id

    tax_rate_id = gateway.create_tax_rate(
        currency=currency,
        name=tax.name,
        percentage=tax.percentage,
        is_inclusive=tax.is_inclusive,
    )

    tax.stripe_tax_rate_ids[cache_key] = tax_rate_id
    tax.save(update_fields=["stripe_tax_rate_ids", "updated_at"])

    return tax_rate_id
