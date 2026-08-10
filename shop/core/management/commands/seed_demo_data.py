from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from shop.catalog.models import Item
from shop.core.money import Currency
from shop.orders.models import Discount, Order, OrderItem, Tax

ITEMS = [
    {
        "name": "Mechanical Keyboard",
        "description": "Hot-swappable 75% keyboard with tactile switches.",
        "price": Decimal("129.00"),
        "currency": Currency.USD,
    },
    {
        "name": "4K Webcam",
        "description": "Ultra HD webcam with autofocus and a privacy shutter.",
        "price": Decimal("89.50"),
        "currency": Currency.USD,
    },
    {
        "name": "Ergonomic Mouse",
        "description": "Vertical wireless mouse, three connection modes.",
        "price": Decimal("49.90"),
        "currency": Currency.EUR,
    },
    {
        "name": "Laptop Stand",
        "description": "Aluminium stand with adjustable height and angle.",
        "price": Decimal("39.00"),
        "currency": Currency.EUR,
    },
]


class Command(BaseCommand):
    help = "Fill the database with demo items, discounts, taxes and orders. Safe to run repeatedly."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        items = {}

        for fields in ITEMS:
            item, _ = Item.objects.update_or_create(name=fields["name"], defaults=fields)
            items[item.name] = item

        discount, _ = Discount.objects.update_or_create(
            name="Welcome discount",
            defaults={"percent_off": Decimal("10.00")},
        )
        tax, _ = Tax.objects.update_or_create(
            name="VAT",
            defaults={"percentage": Decimal("20.00"), "is_inclusive": False},
        )

        if not Order.objects.exists():
            usd_order = Order.objects.create(
                customer_email="customer@example.com", discount=discount, tax=tax
            )
            OrderItem.objects.create(order=usd_order, item=items["Mechanical Keyboard"], quantity=1)
            OrderItem.objects.create(order=usd_order, item=items["4K Webcam"], quantity=2)

            eur_order = Order.objects.create(customer_email="customer@example.com")
            OrderItem.objects.create(order=eur_order, item=items["Ergonomic Mouse"], quantity=1)
            OrderItem.objects.create(order=eur_order, item=items["Laptop Stand"], quantity=1)

        self.stdout.write(self.style.SUCCESS("Demo data is in place."))
