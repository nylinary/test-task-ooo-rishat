from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import stripe

from shop.core.exceptions import ApplicationError
from shop.integrations.stripe import gateway


@pytest.fixture
def stripe_client():
    with patch("shop.integrations.stripe.gateway.get_stripe_client") as get_client:
        yield get_client.return_value


class TestCreateCheckoutSession:
    def test_builds_the_stripe_params(self, stripe_client):
        stripe_client.v1.checkout.sessions.create.return_value = MagicMock(id="cs_1", url="https://stripe/cs")

        session = gateway.create_checkout_session(
            currency="usd",
            line_items=[
                gateway.LineItem(
                    name="Widget",
                    description="A nice widget.",
                    unit_amount=1050,
                    quantity=2,
                    tax_rate_ids=["txr_1"],
                )
            ],
            success_url="https://shop/success",
            cancel_url="https://shop/cancel",
            coupon_id="coupon_1",
            customer_email="customer@example.com",
            metadata={"order_id": "1"},
        )

        assert session == gateway.CheckoutSession(id="cs_1", url="https://stripe/cs")

        params = stripe_client.v1.checkout.sessions.create.call_args.kwargs["params"]
        assert params["mode"] == "payment"
        assert params["success_url"] == "https://shop/success"
        assert params["cancel_url"] == "https://shop/cancel"
        assert params["discounts"] == [{"coupon": "coupon_1"}]
        assert params["customer_email"] == "customer@example.com"
        assert params["metadata"] == {"order_id": "1"}
        assert params["line_items"] == [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 1050,
                    "product_data": {"name": "Widget", "description": "A nice widget."},
                },
                "quantity": 2,
                "tax_rates": ["txr_1"],
            }
        ]

    def test_omits_the_optional_params(self, stripe_client):
        stripe_client.v1.checkout.sessions.create.return_value = MagicMock(id="cs_1", url=None)

        session = gateway.create_checkout_session(
            currency="eur",
            line_items=[gateway.LineItem(name="Widget", description="", unit_amount=100, quantity=1)],
            success_url="https://shop/success",
            cancel_url="https://shop/cancel",
        )

        # A missing session URL is normalized to an empty string.
        assert session.url == ""

        params = stripe_client.v1.checkout.sessions.create.call_args.kwargs["params"]
        line_item = params["line_items"][0]
        assert "description" not in line_item["price_data"]["product_data"]
        assert "tax_rates" not in line_item
        assert "discounts" not in params
        assert "customer_email" not in params

    def test_stripe_error_becomes_a_generic_application_error(self, stripe_client):
        stripe_client.v1.checkout.sessions.create.side_effect = stripe.InvalidRequestError(
            "Request req_123: No such coupon: 'coupon_1'", "coupon", code="resource_missing"
        )

        with pytest.raises(ApplicationError) as exc_info:
            gateway.create_checkout_session(
                currency="usd",
                line_items=[gateway.LineItem(name="W", description="", unit_amount=1, quantity=1)],
                success_url="https://shop/success",
                cancel_url="https://shop/cancel",
            )

        # The raw Stripe message (request ids, params) stays out of the error.
        assert exc_info.value.message == "Payment provider error while creating a checkout session."
        assert exc_info.value.extra == {"stripe_error_code": "resource_missing"}


class TestCreatePaymentIntent:
    def test_builds_the_stripe_params(self, stripe_client):
        stripe_client.v1.payment_intents.create.return_value = MagicMock(
            id="pi_1", client_secret="pi_1_secret", amount=10800, currency="usd"
        )

        payment_intent = gateway.create_payment_intent(
            currency="usd",
            amount=10800,
            description="Order #1",
            receipt_email="customer@example.com",
            metadata={"order_id": "1"},
        )

        assert payment_intent == gateway.PaymentIntent(
            id="pi_1", client_secret="pi_1_secret", amount=10800, currency="usd"
        )

        assert stripe_client.v1.payment_intents.create.call_args.kwargs["params"] == {
            "amount": 10800,
            "currency": "usd",
            "description": "Order #1",
            "automatic_payment_methods": {"enabled": True},
            "metadata": {"order_id": "1"},
            "receipt_email": "customer@example.com",
        }

    def test_omits_receipt_email_when_blank(self, stripe_client):
        stripe_client.v1.payment_intents.create.return_value = MagicMock(
            id="pi_1", client_secret="s", amount=100, currency="usd"
        )

        gateway.create_payment_intent(currency="usd", amount=100, description="Order #1")

        params = stripe_client.v1.payment_intents.create.call_args.kwargs["params"]
        assert "receipt_email" not in params


class TestCreateCouponAndTaxRate:
    def test_coupon_params(self, stripe_client):
        stripe_client.v1.coupons.create.return_value = MagicMock(id="coupon_1")

        coupon_id = gateway.create_coupon(currency="usd", name="Welcome", percent_off=Decimal("10.00"))

        assert coupon_id == "coupon_1"
        assert stripe_client.v1.coupons.create.call_args.kwargs["params"] == {
            "name": "Welcome",
            "percent_off": 10.0,
            "duration": "once",
        }

    def test_tax_rate_params(self, stripe_client):
        stripe_client.v1.tax_rates.create.return_value = MagicMock(id="txr_1")

        tax_rate_id = gateway.create_tax_rate(
            currency="usd", name="VAT", percentage=Decimal("20.00"), is_inclusive=True
        )

        assert tax_rate_id == "txr_1"
        assert stripe_client.v1.tax_rates.create.call_args.kwargs["params"] == {
            "display_name": "VAT",
            "percentage": 20.0,
            "inclusive": True,
        }
