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
from shop.orders.selectors import order_get, order_list, order_totals


def _publishable_key(*, currency: str) -> tuple[str, str]:
    """Return `(publishable_key, error_message)` so a page can render either."""
    try:
        return get_publishable_key(currency=currency), ""
    except ApplicationError as exc:
        return "", exc.message


def _error_page(request: HttpRequest, message: str) -> HttpResponse:
    return render(request, "web/error.html", {"message": message}, status=400)


def index(request: HttpRequest) -> HttpResponse:
    orders = []

    for order in order_list():
        try:
            orders.append({"order": order, "totals": order_totals(order=order)})
        except ApplicationError as exc:
            orders.append({"order": order, "totals": None, "error": exc.message})

    return render(request, "web/index.html", {"items": item_list(), "orders": orders})


def item_detail(request: HttpRequest, item_id: int) -> HttpResponse:
    item = item_get(item_id=item_id)
    publishable_key, stripe_error = _publishable_key(currency=item.currency)

    return render(
        request,
        "web/item_detail.html",
        {"item": item, "stripe_publishable_key": publishable_key, "stripe_error": stripe_error},
    )


def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    order = order_get(order_id=order_id)

    try:
        totals = order_totals(order=order)
    except ApplicationError as exc:
        return _error_page(request, exc.message)

    publishable_key, stripe_error = _publishable_key(currency=totals.currency)

    return render(
        request,
        "web/order_detail.html",
        {
            "order": order,
            "totals": totals,
            "stripe_publishable_key": publishable_key,
            "stripe_error": stripe_error,
        },
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
