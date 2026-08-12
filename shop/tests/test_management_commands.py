import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from shop.catalog.models import Item
from shop.orders.models import Discount, Order, Tax

pytestmark = pytest.mark.django_db


class TestSeedDemoData:
    def test_creates_the_demo_catalog(self):
        call_command("seed_demo_data")

        assert Item.objects.count() == 4
        assert Order.objects.count() == 2
        assert Discount.objects.count() == 1
        assert Tax.objects.count() == 1

    def test_is_idempotent(self):
        call_command("seed_demo_data")
        call_command("seed_demo_data")

        assert Item.objects.count() == 4
        assert Order.objects.count() == 2


class TestEnsureSuperuser:
    def test_skips_when_credentials_are_not_configured(self, monkeypatch):
        monkeypatch.delenv("DJANGO_SUPERUSER_USERNAME", raising=False)
        monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)

        call_command("ensure_superuser")

        assert get_user_model().objects.count() == 0

    def test_creates_and_rotates_the_account(self, monkeypatch):
        monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin")
        monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "first-password")

        call_command("ensure_superuser")

        user = get_user_model().objects.get(username="admin")
        assert user.is_superuser
        assert user.is_staff
        assert user.check_password("first-password")

        # A second run with a new password updates the same account.
        monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "rotated-password")
        call_command("ensure_superuser")

        user.refresh_from_db()
        assert user.check_password("rotated-password")
        assert get_user_model().objects.count() == 1
