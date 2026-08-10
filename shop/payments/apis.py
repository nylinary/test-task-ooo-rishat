from django.urls import reverse
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.catalog.selectors import item_get
from shop.payments.services import create_checkout_session_for_item

# Stripe replaces this placeholder with the real id when redirecting back.
SUCCESS_URL_TEMPLATE = "{success_url}?session_id={{CHECKOUT_SESSION_ID}}"


def _absolute_url(request: Request, view_name: str, **kwargs) -> str:
    return request.build_absolute_uri(reverse(view_name, kwargs=kwargs))


def _success_url(request: Request) -> str:
    return SUCCESS_URL_TEMPLATE.format(success_url=_absolute_url(request, "web:payment-success"))


class CheckoutSessionOutputSerializer(serializers.Serializer):
    id = serializers.CharField()
    url = serializers.CharField()


class ItemCheckoutSessionApi(APIView):
    """
    GET /buy/<item_id>

    Creates a Stripe Checkout Session for a single item and returns its id,
    which the frontend hands over to `stripe.redirectToCheckout()`.
    """

    OutputSerializer = CheckoutSessionOutputSerializer

    def get(self, request: Request, item_id: int) -> Response:
        item = item_get(item_id=item_id)

        session = create_checkout_session_for_item(
            item=item,
            success_url=_success_url(request),
            cancel_url=_absolute_url(request, "web:item-detail", item_id=item.id),
        )

        return Response(self.OutputSerializer(session).data)
