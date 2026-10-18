
from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["store", "name"], name="unique_product_name")
        ]

    def __str__(self) -> str:
        return self.name


class Forecast(models.Model):
    """One product's forecast and order options for one day, written by the batch."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="forecasts"
    )
    date = models.DateField()
    # Units by quantile, such as {"p10": 21.4, "p50": 24.8, "p95": 29.0}.
    quantiles = models.JSONField()
    # One entry per slider position: label, units and sell_out_chance.
    orders = models.JSONField()
    reasons = models.JSONField()
    model_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "date"], name="one_forecast_per_product_day"
            )
        ]

    def __str__(self) -> str:
        return f"{self.product} on {self.date}"