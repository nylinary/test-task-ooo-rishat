from django.urls import path

from shop.payments.apis import ItemCheckoutSessionApi

urlpatterns = [
    path("buy/<int:item_id>", ItemCheckoutSessionApi.as_view(), name="item-checkout-session"),
]
