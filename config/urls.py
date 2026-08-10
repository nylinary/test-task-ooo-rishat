from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # JSON API (`/buy/<item_id>`, order checkout & payment intent endpoints).
    path("", include(("shop.payments.urls", "payments"), namespace="payments")),
    # Server-rendered pages (`/`, `/item/<item_id>`, `/orders/<order_id>`, ...).
    path("", include(("shop.web.urls", "web"), namespace="web")),
]
