from dataclasses import dataclass
from functools import cache

import stripe
from django.conf import settings

from shop.core.exceptions import ApplicationError


@dataclass(frozen=True)
class StripeAccount:
    """A Stripe keypair, selected by the currency that is being charged."""

    currency: str
    publishable_key: str
    secret_key: str


def get_stripe_account(*, currency: str) -> StripeAccount:
    currency = currency.lower()
    account = settings.STRIPE_ACCOUNTS.get(currency)

    if account is None:
        raise ApplicationError(
            f"There is no Stripe account configured for {currency.upper()}.",
            extra={"supported_currencies": sorted(settings.STRIPE_ACCOUNTS)},
        )

    if not account["secret_key"] or not account["publishable_key"]:
        raise ApplicationError(
            f"The Stripe keypair for {currency.upper()} is missing. "
            f"Set STRIPE_{currency.upper()}_SECRET_KEY / STRIPE_{currency.upper()}_PUBLISHABLE_KEY "
            "(or the STRIPE_SECRET_KEY / STRIPE_PUBLISHABLE_KEY fallback)."
        )

    return StripeAccount(
        currency=currency,
        publishable_key=account["publishable_key"],
        secret_key=account["secret_key"],
    )


@cache
def _stripe_client(secret_key: str) -> stripe.StripeClient:
    return stripe.StripeClient(api_key=secret_key)


def get_stripe_client(*, currency: str) -> stripe.StripeClient:
    """
    Return a Stripe client bound to the keypair of the given currency.

    Clients are cached per key, so a single `StripeClient` (and its underlying
    HTTP connection pool) is reused per Stripe account.
    """
    return _stripe_client(get_stripe_account(currency=currency).secret_key)


def get_publishable_key(*, currency: str) -> str:
    return get_stripe_account(currency=currency).publishable_key
