from django.urls import path

from shop.payments.apis import (
    ItemCheckoutSessionApi,
    OrderCheckoutSessionApi,
    OrderPaymentIntentApi,
)

urlpatterns = [
    path("buy/<int:item_id>", ItemCheckoutSessionApi.as_view(), name="item-checkout-session"),
    path("orders/<int:order_id>/buy", OrderCheckoutSessionApi.as_view(), name="order-checkout-session"),
    path(
        "orders/<int:order_id>/payment-intent",
        OrderPaymentIntentApi.as_view(),
        name="order-payment-intent",
    ),
]
