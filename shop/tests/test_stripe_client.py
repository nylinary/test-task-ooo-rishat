import pytest

from shop.core.exceptions import ApplicationError
from shop.integrations.stripe.client import (
    get_publishable_key,
    get_stripe_account,
    get_stripe_client,
)


class TestStripeAccountSelection:
    def test_returns_the_keypair_of_the_currency(self, settings):
        settings.STRIPE_ACCOUNTS = {
            "usd": {"publishable_key": "pk_usd", "secret_key": "sk_usd"},
            "eur": {"publishable_key": "pk_eur", "secret_key": "sk_eur"},
        }

        assert get_stripe_account(currency="usd").secret_key == "sk_usd"
        assert get_publishable_key(currency="eur") == "pk_eur"

    def test_currency_lookup_is_case_insensitive(self, settings):
        settings.STRIPE_ACCOUNTS = {"usd": {"publishable_key": "pk_usd", "secret_key": "sk_usd"}}

        assert get_stripe_account(currency="USD").publishable_key == "pk_usd"

    def test_unsupported_currency_lists_the_supported_ones(self, settings):
        settings.STRIPE_ACCOUNTS = {
            "usd": {"publishable_key": "pk", "secret_key": "sk"},
            "eur": {"publishable_key": "pk", "secret_key": "sk"},
        }

        with pytest.raises(ApplicationError) as exc_info:
            get_stripe_account(currency="gbp")

        assert exc_info.value.extra == {"supported_currencies": ["eur", "usd"]}

    def test_missing_keypair_names_the_env_variables(self, settings):
        settings.STRIPE_ACCOUNTS = {"usd": {"publishable_key": "", "secret_key": ""}}

        with pytest.raises(ApplicationError) as exc_info:
            get_stripe_account(currency="usd")

        assert "STRIPE_USD_SECRET_KEY" in exc_info.value.message

    def test_clients_are_cached_per_secret_key(self, settings):
        settings.STRIPE_ACCOUNTS = {
            "usd": {"publishable_key": "pk", "secret_key": "sk_cache_test_1"},
            "eur": {"publishable_key": "pk", "secret_key": "sk_cache_test_2"},
        }

        assert get_stripe_client(currency="usd") is get_stripe_client(currency="usd")
        assert get_stripe_client(currency="usd") is not get_stripe_client(currency="eur")
