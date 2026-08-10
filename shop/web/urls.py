from django.urls import path

from shop.web import views

urlpatterns = [
    path("", views.index, name="index"),
    path("item/<int:item_id>", views.item_detail, name="item-detail"),
    path("orders/<int:order_id>", views.order_detail, name="order-detail"),
    path("payment/success", views.payment_success, name="payment-success"),
]
