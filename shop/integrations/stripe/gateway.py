"""
Thin, typed wrappers around the Stripe HTTP API.

Everything in this module speaks Stripe (minor units, coupon ids, session
params) and knows nothing about our models - the mapping between the two lives
in `shop.payments.services`.
"""

import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal

import stripe
from stripe.params import CouponCreateParams, PaymentIntentCreateParams, TaxRateCreateParams
from stripe.params.checkout import (
    SessionCreateParams,
    SessionCreateParamsLineItem,
    SessionCreateParamsLineItemPriceDataProductData,
)

from shop.core.exceptions import ApplicationError
from shop.integrations.stripe.client import get_stripe_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LineItem:
    name: str
    description: str
    unit_amount: int
    quantity: int
    tax_rate_ids: Sequence[str] = ()


@dataclass(frozen=True)
class CheckoutSession:
    id: str
    url: str


@dataclass(frozen=True)
class PaymentIntent:
    id: str
    client_secret: str
    amount: int
    currency: str


@contextmanager
def _stripe_call(action: str) -> Iterator[None]:
    try:
        yield
    except stripe.StripeError as exc:
        # Full details go to the server log only. Raw Stripe messages are not
        # safe for clients - e.g. an AuthenticationError spells out fragments
        # of the secret key. The stable machine-readable code is safe.
        logger.exception("Stripe call failed: %s", action)

        raise ApplicationError(
            f"Payment provider error while {action}.",
            extra={"stripe_error_code": exc.code} if exc.code else None,
        ) from exc


def _session_line_item(line_item: LineItem, *, currency: str) -> SessionCreateParamsLineItem:
    product_data: SessionCreateParamsLineItemPriceDataProductData = {"name": line_item.name}

    if line_item.description:
        product_data["description"] = line_item.description

    params: SessionCreateParamsLineItem = {
        "price_data": {
            "currency": currency,
            "unit_amount": line_item.unit_amount,
            "product_data": product_data,
        },
        "quantity": line_item.quantity,
    }

    if line_item.tax_rate_ids:
        params["tax_rates"] = list(line_item.tax_rate_ids)

    return params


def create_checkout_session(
    *,
    currency: str,
    line_items: Sequence[LineItem],
    success_url: str,
    cancel_url: str,
    coupon_id: str | None = None,
    customer_email: str = "",
    metadata: dict[str, str] | None = None,
) -> CheckoutSession:
    client = get_stripe_client(currency=currency)

    params: SessionCreateParams = {
        "mode": "payment",
        "line_items": [_session_line_item(line_item, currency=currency) for line_item in line_items],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": metadata or {},
    }

    if coupon_id:
        params["discounts"] = [{"coupon": coupon_id}]

    if customer_email:
        params["customer_email"] = customer_email

    with _stripe_call("creating a checkout session"):
        session = client.v1.checkout.sessions.create(params=params)

    return CheckoutSession(id=session.id, url=session.url or "")


def create_payment_intent(
    *,
    currency: str,
    amount: int,
    description: str,
    receipt_email: str = "",
    metadata: dict[str, str] | None = None,
) -> PaymentIntent:
    client = get_stripe_client(currency=currency)

    params: PaymentIntentCreateParams = {
        "amount": amount,
        "currency": currency,
        "description": description,
        "automatic_payment_methods": {"enabled": True},
        "metadata": metadata or {},
    }

    if receipt_email:
        params["receipt_email"] = receipt_email

    with _stripe_call("creating a payment intent"):
        payment_intent = client.v1.payment_intents.create(params=params)

    return PaymentIntent(
        id=payment_intent.id,
        client_secret=payment_intent.client_secret or "",
        amount=payment_intent.amount,
        currency=payment_intent.currency,
    )


def create_coupon(*, currency: str, name: str, percent_off: Decimal) -> str:
    client = get_stripe_client(currency=currency)

    params: CouponCreateParams = {"name": name, "percent_off": float(percent_off), "duration": "once"}

    with _stripe_call("creating a coupon"):
        coupon = client.v1.coupons.create(params=params)

    return coupon.id


def create_tax_rate(*, currency: str, name: str, percentage: Decimal, is_inclusive: bool) -> str:
    client = get_stripe_client(currency=currency)

    params: TaxRateCreateParams = {
        "display_name": name,
        "percentage": float(percentage),
        "inclusive": is_inclusive,
    }

    with _stripe_call("creating a tax rate"):
        tax_rate = client.v1.tax_rates.create(params=params)

    return tax_rate.id
