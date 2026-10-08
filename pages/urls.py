from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("orders/", views.orders, name="orders"),
    path("orders/table", views.order_table, name="order_table"),
    path("healthz", views.healthz, name="healthz"),
]
