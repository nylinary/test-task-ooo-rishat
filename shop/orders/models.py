from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from shop.core.models import BaseModel
from shop.core.money import resolve_single_currency


class Discount(BaseModel):
    """
    A percentage discount applied to a whole order.

    Mapped to a Stripe Coupon (`discounts=[{"coupon": ...}]`) when a Checkout
    Session is created.
    """

    name = models.CharField("название", max_length=255)
    percent_off = models.DecimalField(
        "процент скидки",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("100"))],
    )
    is_active = models.BooleanField(
        "активна", default=True, help_text="Неактивные скидки не применяются к заказам."
    )
    stripe_coupon_ids = models.JSONField(
        default=dict,
        editable=False,
        help_text="Кэш Stripe-купонов, созданных для каждого Stripe-аккаунта (валюты).",
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "скидка"
        verbose_name_plural = "скидки"

    def __str__(self) -> str:
        return f"{self.name} (-{self.percent_off}%)"


class Tax(BaseModel):
    """
    A tax rate applied to an order.

    Mapped to a Stripe Tax Rate, attached to every line item of a Checkout
    Session (`line_items[].tax_rates`).
    """

    name = models.CharField("название", max_length=255)
    percentage = models.DecimalField(
        "ставка, %",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    is_inclusive = models.BooleanField(
        "включён в цену",
        default=False,
        help_text="Инклюзивный налог уже входит в цену товара.",
    )
    is_active = models.BooleanField(
        "активен", default=True, help_text="Неактивные налоги не применяются к заказам."
    )
    stripe_tax_rate_ids = models.JSONField(
        default=dict,
        editable=False,
        help_text="Кэш Stripe-ставок, созданных для каждого Stripe-аккаунта (валюты).",
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "налог"
        verbose_name_plural = "налоги"

    def __str__(self) -> str:
        return f"{self.name} ({self.percentage}%)"


class Order(BaseModel):
    customer_email = models.EmailField(
        "email покупателя", blank=True, help_text="Подставляется в форму Stripe Checkout."
    )
    discount = models.ForeignKey(
        Discount,
        verbose_name="скидка",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    tax = models.ForeignKey(
        Tax,
        verbose_name="налог",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    items = models.ManyToManyField(
        "catalog.Item", verbose_name="товары", through="orders.OrderItem", related_name="orders"
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "заказ"
        verbose_name_plural = "заказы"

    def __str__(self) -> str:
        return f"Заказ №{self.pk}"

    @property
    def currency(self) -> str:
        """
        An order is paid in a single currency, because a Stripe payment happens
        in a single currency (and, here, against a single Stripe account).
        """
        return resolve_single_currency({order_item.item.currency for order_item in self.order_items.all()})

    @property
    def applied_discount(self) -> Discount | None:
        return self.discount if self.discount and self.discount.is_active else None

    @property
    def applied_tax(self) -> Tax | None:
        return self.tax if self.tax and self.tax.is_active else None


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order, verbose_name="заказ", on_delete=models.CASCADE, related_name="order_items"
    )
    item = models.ForeignKey(
        "catalog.Item", verbose_name="товар", on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField("количество", default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ("id",)
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"
        constraints = [
            models.UniqueConstraint(fields=["order", "item"], name="order_item_unique_item_per_order"),
        ]

    def __str__(self) -> str:
        return f"{self.item.name} x {self.quantity}"

    @property
    def amount(self) -> Decimal:
        return self.item.price * self.quantity
