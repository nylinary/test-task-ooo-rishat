"""
Business logic that turns our models into Stripe payments.

`shop.integrations.stripe.gateway` does the talking to Stripe, this module
decides *what* to send: which keypair (currency) and which line items.
"""

from shop.catalog.models import Item
from shop.core.money import to_minor_units
from shop.integrations.stripe import gateway


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
