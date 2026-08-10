from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # JSON API (`/buy/<item_id>`).
    path("", include(("shop.payments.urls", "payments"), namespace="payments")),
]
