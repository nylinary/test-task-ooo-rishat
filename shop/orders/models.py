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

    name = models.CharField(max_length=255)
    percent_off = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("100"))],
    )
    is_active = models.BooleanField(default=True, help_text="Inactive discounts are not applied to orders.")
    stripe_coupon_ids = models.JSONField(
        default=dict,
        editable=False,
        help_text="Cache of the Stripe Coupon created per Stripe account (currency).",
    )

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.name} (-{self.percent_off}%)"


class Tax(BaseModel):
    """
    A tax rate applied to an order.

    Mapped to a Stripe Tax Rate, attached to every line item of a Checkout
    Session (`line_items[].tax_rates`).
    """

    name = models.CharField(max_length=255)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    is_inclusive = models.BooleanField(
        default=False,
        help_text="Inclusive taxes are already part of the item price.",
    )
    is_active = models.BooleanField(default=True, help_text="Inactive taxes are not applied to orders.")
    stripe_tax_rate_ids = models.JSONField(
        default=dict,
        editable=False,
        help_text="Cache of the Stripe Tax Rate created per Stripe account (currency).",
    )

    class Meta:
        ordering = ("id",)
        verbose_name_plural = "taxes"

    def __str__(self) -> str:
        return f"{self.name} ({self.percentage}%)"


class Order(BaseModel):
    customer_email = models.EmailField(blank=True, help_text="Pre-filled in the Stripe Checkout form.")
    discount = models.ForeignKey(
        Discount,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    tax = models.ForeignKey(
        Tax,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    items = models.ManyToManyField("catalog.Item", through="orders.OrderItem", related_name="orders")

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"Order #{self.pk}"

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
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    item = models.ForeignKey("catalog.Item", on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(fields=["order", "item"], name="order_item_unique_item_per_order"),
        ]

    def __str__(self) -> str:
        return f"{self.item.name} x {self.quantity}"

    @property
    def amount(self) -> Decimal:
        return self.item.price * self.quantity
