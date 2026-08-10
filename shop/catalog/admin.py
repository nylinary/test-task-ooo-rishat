from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from shop.catalog.models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "currency", "is_active", "buy_page")
    list_filter = ("currency", "is_active")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Buy page")
    def buy_page(self, obj: Item) -> str:
        url = reverse("web:item-detail", kwargs={"item_id": obj.id})

        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
