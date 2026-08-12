from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, QuerySet
from django.forms import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html

from shop.core.exceptions import ApplicationError
from shop.orders.models import Discount, Order, OrderItem, Tax
from shop.orders.selectors import order_totals


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "percent_off", "is_active")
    list_filter = ("is_active",)
    readonly_fields = ("stripe_coupon_ids", "created_at", "updated_at")


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "percentage", "is_inclusive", "is_active")
    list_filter = ("is_active", "is_inclusive")
    readonly_fields = ("stripe_tax_rate_ids", "created_at", "updated_at")


class OrderItemInlineFormSet(BaseInlineFormSet):
    def clean(self) -> None:
        super().clean()

        currencies = {
            form.cleaned_data["item"].currency
            for form in self.forms
            if form.cleaned_data.get("item") and not form.cleaned_data.get("DELETE")
        }

        if len(currencies) > 1:
            raise ValidationError(
                "Заказ не может смешивать валюты: %(currencies)s. "
                "Платёж Stripe всегда проходит в одной валюте.",
                params={"currencies": ", ".join(sorted(c.upper() for c in currencies))},
            )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    formset = OrderItemInlineFormSet
    extra = 1
    autocomplete_fields = ("item",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (OrderItemInline,)
    list_display = ("id", "customer_email", "discount", "tax", "total", "payment_page")
    list_select_related = ("discount", "tax")
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request) -> QuerySet[Order]:
        return (
            super()
            .get_queryset(request)
            .prefetch_related(Prefetch("order_items", queryset=OrderItem.objects.select_related("item")))
        )

    @admin.display(description="Сумма")
    def total(self, obj: Order) -> str:
        try:
            totals = order_totals(order=obj)
        except ApplicationError as exc:
            return exc.message

        return f"{totals.total:.2f} {totals.currency.upper()}"

    @admin.display(description="Страница оплаты")
    def payment_page(self, obj: Order) -> str:
        url = reverse("web:order-detail", kwargs={"order_id": obj.id})

        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
