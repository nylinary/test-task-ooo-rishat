from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from shop.catalog.models import Item
from shop.core.money import Currency
from shop.orders.models import Discount, Order, OrderItem, Tax

ITEMS = [
    {
        "name": "Механическая клавиатура",
        "description": "Клавиатура 75% с тактильными переключателями и горячей заменой.",
        "price": Decimal("129.00"),
        "currency": Currency.USD,
    },
    {
        "name": "Веб-камера 4K",
        "description": "Камера Ultra HD с автофокусом и шторкой приватности.",
        "price": Decimal("89.50"),
        "currency": Currency.USD,
    },
    {
        "name": "Эргономичная мышь",
        "description": "Вертикальная беспроводная мышь, три режима подключения.",
        "price": Decimal("49.90"),
        "currency": Currency.EUR,
    },
    {
        "name": "Подставка для ноутбука",
        "description": "Алюминиевая подставка с регулировкой высоты и наклона.",
        "price": Decimal("39.00"),
        "currency": Currency.EUR,
    },
]


class Command(BaseCommand):
    help = "Наполняет базу демо-товарами, скидками, налогами и заказами. Можно запускать повторно."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        items = {}

        for fields in ITEMS:
            item, _ = Item.objects.update_or_create(name=fields["name"], defaults=fields)
            items[item.name] = item

        discount, _ = Discount.objects.update_or_create(
            name="Приветственная скидка",
            defaults={"percent_off": Decimal("10.00")},
        )
        tax, _ = Tax.objects.update_or_create(
            name="НДС",
            defaults={"percentage": Decimal("20.00"), "is_inclusive": False},
        )

        if not Order.objects.exists():
            usd_order = Order.objects.create(
                customer_email="customer@example.com", discount=discount, tax=tax
            )
            OrderItem.objects.create(order=usd_order, item=items["Механическая клавиатура"], quantity=1)
            OrderItem.objects.create(order=usd_order, item=items["Веб-камера 4K"], quantity=2)

            eur_order = Order.objects.create(customer_email="customer@example.com")
            OrderItem.objects.create(order=eur_order, item=items["Эргономичная мышь"], quantity=1)
            OrderItem.objects.create(order=eur_order, item=items["Подставка для ноутбука"], quantity=1)

        self.stdout.write(self.style.SUCCESS("Демо-данные загружены."))
