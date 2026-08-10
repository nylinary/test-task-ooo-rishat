"""
Server-rendered pages.

Views stay thin: they read through selectors and never talk to Stripe
themselves - the pages only need a publishable key, everything else happens
through the JSON API in `shop.payments.apis`.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from shop.catalog.selectors import item_get, item_list
from shop.core.exceptions import ApplicationError
from shop.integrations.stripe.client import get_publishable_key


def _publishable_key(*, currency: str) -> tuple[str, str]:
    """Return `(publishable_key, error_message)` so a page can render either."""
    try:
        return get_publishable_key(currency=currency), ""
    except ApplicationError as exc:
        return "", exc.message


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "web/index.html", {"items": item_list()})


def item_detail(request: HttpRequest, item_id: int) -> HttpResponse:
    item = item_get(item_id=item_id)
    publishable_key, stripe_error = _publishable_key(currency=item.currency)

    return render(
        request,
        "web/item_detail.html",
        {"item": item, "stripe_publishable_key": publishable_key, "stripe_error": stripe_error},
    )


def payment_success(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "web/payment_success.html",
        {
            # Stripe appends these when it redirects back.
            "session_id": request.GET.get("session_id", ""),
            "payment_intent_id": request.GET.get("payment_intent", ""),
            "redirect_status": request.GET.get("redirect_status", ""),
        },
    )
