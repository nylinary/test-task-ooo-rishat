from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from shop.catalog.models import Item


def item_list() -> QuerySet[Item]:
    return Item.objects.filter(is_active=True)


def item_get(*, item_id: int) -> Item:
    return get_object_or_404(Item, id=item_id, is_active=True)
