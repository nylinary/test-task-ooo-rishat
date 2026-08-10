from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from shop.core.models import BaseModel
from shop.core.money import CURRENCY_SYMBOLS, Currency


class Item(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
        help_text="Decides which Stripe keypair is used to pay for this item.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.name} - {self.display_price}"

    @property
    def display_price(self) -> str:
        return f"{CURRENCY_SYMBOLS.get(self.currency, '')}{self.price:.2f}"
