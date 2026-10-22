from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("orders/", views.orders, name="orders"),
    path("results/", views.results_page, name="results"),
    path("orders/table", views.order_table, name="order_table"),
    path("shops/", views.shops, name="shops"),
    path("shops/<int:store_id>/", views.shop_orders, name="shop_orders"),
    path("shops/<int:store_id>/table", views.shop_order_table, name="shop_order_table"),
    path("healthz", views.healthz, name="healthz"),
]
