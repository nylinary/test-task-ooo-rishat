from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import Client

from shop.core.money import Currency
from shop.integrations.stripe.gateway import CheckoutSession, PaymentIntent
from shop.tests.factories import DiscountFactory, ItemFactory, OrderItemFactory, TaxFactory

pytestmark = pytest.mark.django_db


class TestItemCheckoutSessionApi:
    def test_returns_session_id(self, client: Client):
        item = ItemFactory(price=Decimal("12.34"), currency=Currency.USD)

        with patch("shop.payments.services.gateway.create_checkout_session") as create_session:
            create_session.return_value = CheckoutSession(id="cs_test_123", url="https://stripe.test/cs")

            response = client.get(f"/buy/{item.id}")

        assert response.status_code == 200
        assert response.json() == {"id": "cs_test_123", "url": "https://stripe.test/cs"}

        kwargs = create_session.call_args.kwargs
        assert kwargs["currency"] == "usd"
        assert kwargs["line_items"][0].unit_amount == 1234
        assert kwargs["metadata"] == {"item_id": str(item.id)}
        assert "{CHECKOUT_SESSION_ID}" in kwargs["success_url"]

    def test_unknown_item_is_404(self, client: Client):
        response = client.get("/buy/999")

        assert response.status_code == 404
        assert response.json()["message"]

    def test_inactive_item_is_404(self, client: Client):
        item = ItemFactory(is_active=False)

        response = client.get(f"/buy/{item.id}")

        assert response.status_code == 404


class TestOrderCheckoutSessionApi:
    def test_passes_discount_and_tax_to_stripe(self, client: Client):
        order_item = OrderItemFactory(
            item__price=Decimal("100.00"),
            quantity=2,
            order__discount=DiscountFactory(),
            order__tax=TaxFactory(),
        )
        order = order_item.order

        with (
            patch("shop.payments.services.gateway.create_checkout_session") as create_session,
            patch("shop.payments.services.gateway.create_coupon", return_value="coupon_123"),
            patch("shop.payments.services.gateway.create_tax_rate", return_value="txr_123"),
        ):
            create_session.return_value = CheckoutSession(id="cs_test_456", url="")

            response = client.get(f"/orders/{order.id}/buy")

        assert response.status_code == 200
        assert response.json()["id"] == "cs_test_456"

        kwargs = create_session.call_args.kwargs
        assert kwargs["coupon_id"] == "coupon_123"
        assert kwargs["line_items"][0].tax_rate_ids == ["txr_123"]
        assert kwargs["line_items"][0].quantity == 2

        # Stripe object ids are cached on the models per currency.
        order.discount.refresh_from_db()
        order.tax.refresh_from_db()
        assert "usd:10.00" in order.discount.stripe_coupon_ids
        assert "usd:20.00:exclusive" in order.tax.stripe_tax_rate_ids

    def test_mixed_currency_order_is_a_400(self, client: Client):
        order_item = OrderItemFactory(item__currency=Currency.USD)
        OrderItemFactory(order=order_item.order, item__currency=Currency.EUR)

        response = client.get(f"/orders/{order_item.order.id}/buy")

        assert response.status_code == 400
        assert "currency" in response.json()["message"]


class TestOrderPaymentIntentApi:
    def test_charges_the_discounted_and_taxed_total(self, client: Client):
        order_item = OrderItemFactory(
            item__price=Decimal("100.00"),
            order__discount=DiscountFactory(percent_off=Decimal("10.00")),
            order__tax=TaxFactory(percentage=Decimal("20.00")),
        )

        with patch("shop.payments.services.gateway.create_payment_intent") as create_intent:
            create_intent.return_value = PaymentIntent(
                id="pi_123", client_secret="pi_123_secret", amount=10800, currency="usd"
            )

            response = client.get(f"/orders/{order_item.order.id}/payment-intent")

        assert response.status_code == 200
        assert response.json() == {
            "id": "pi_123",
            "client_secret": "pi_123_secret",
            "amount": 10800,
            "currency": "usd",
        }

        # 100 - 10% = 90, +20% tax = 108.00 -> 10800 minor units.
        assert create_intent.call_args.kwargs["amount"] == 10800


class TestWebPages:
    def test_item_page_renders_buy_button(self, client: Client, settings):
        settings.STRIPE_ACCOUNTS = {
            "usd": {"publishable_key": "pk_test_x", "secret_key": "sk_test_x"},
        }
        item = ItemFactory(name="Blue Widget")

        response = client.get(f"/item/{item.id}")

        content = response.content.decode()
        assert response.status_code == 200
        assert "Blue Widget" in content
        assert 'id="buy-button"' in content
        assert "pk_test_x" in content

    def test_item_page_shows_error_when_keys_are_missing(self, client: Client, settings):
        settings.STRIPE_ACCOUNTS = {"usd": {"publishable_key": "", "secret_key": ""}}
        item = ItemFactory()

        response = client.get(f"/item/{item.id}")

        assert response.status_code == 200
        assert "keypair" in response.content.decode()

    def test_order_page_renders_totals(self, client: Client, settings):
        settings.STRIPE_ACCOUNTS = {
            "usd": {"publishable_key": "pk_test_x", "secret_key": "sk_test_x"},
        }
        order_item = OrderItemFactory(item__price=Decimal("100.00"), order__tax=TaxFactory())

        response = client.get(f"/orders/{order_item.order.id}")

        content = response.content.decode()
        assert response.status_code == 200
        assert "$120.00" in content

    def test_index_lists_items_and_orders(self, client: Client):
        ItemFactory(name="Indexed Item")
        OrderItemFactory()

        response = client.get("/")

        assert response.status_code == 200
        assert "Indexed Item" in response.content.decode()
