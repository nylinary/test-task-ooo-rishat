from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from shop.core.models import BaseModel
from shop.core.money import CURRENCY_SYMBOLS, Currency


class Item(BaseModel):
    name = models.CharField("название", max_length=255)
    description = models.TextField("описание", blank=True)
    price = models.DecimalField(
        "цена",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(
        "валюта",
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
        help_text="Определяет, какой Stripe-кейпар используется для оплаты этого товара.",
    )
    is_active = models.BooleanField("активен", default=True)

    class Meta:
        ordering = ("id",)
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self) -> str:
        return f"{self.name} - {self.display_price}"

    @property
    def display_price(self) -> str:
        return f"{CURRENCY_SYMBOLS.get(self.currency, '')}{self.price:.2f}"
