"""A simulated Irish corner shop for the Binless demo.

Every product, price and sales pattern here is invented for illustration. None of
it comes from a real shop.
"""

from dataclasses import dataclass
from datetime import date
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from forecasting.ordering import Costs
from forecasting.stockouts import TRADING_HOURS


STORE_NAME = "Rowan Street Grocer (simulated)"
SHOP_TIMEZONE = ZoneInfo("Europe/Dublin")


@dataclass(frozen=True)
class Category:
    """How a simulated category sells.

    weekday_factors run Monday to Sunday. hourly_weights cover the 16 trading hours
    from 06:00 to 21:00. heat_lift is the extra demand per degree above 14°C.
    """

    category_id: int
    weekday_factors: tuple[float, ...]
    hourly_weights: tuple[float, ...]
    heat_lift: float
    costs: Costs


CATEGORIES = {
    "Bread": Category(
        1,
        (0.9, 0.9, 0.95, 1.0, 1.1, 1.3, 1.15),
        (3, 6, 8, 8, 7, 6, 6, 5, 5, 5, 6, 7, 6, 4, 3, 2),
        0.0,
        Costs(price=2.20, unit_cost=1.10),
    ),
    "Dairy": Category(
        2,
        (1.0, 0.95, 0.95, 1.0, 1.05, 1.15, 1.1),
        (2, 5, 7, 6, 5, 5, 5, 5, 6, 7, 8, 8, 7, 5, 4, 3),
        0.0,
        Costs(price=2.30, unit_cost=1.70, salvage=1.20),
    ),
    "Deli": Category(
        3,
        (1.15, 1.1, 1.1, 1.1, 1.05, 0.75, 0.6),
        (4, 9, 10, 8, 5, 8, 10, 7, 3, 2, 3, 3, 2, 1, 1, 1),
        0.0,
        Costs(price=4.50, unit_cost=1.80),
    ),
    "Salads": Category(
        4,
        (1.1, 1.05, 1.05, 1.0, 0.95, 0.85, 0.8),
        (0, 1, 2, 3, 4, 8, 12, 10, 5, 4, 4, 5, 4, 3, 2, 1),
        0.04,
        Costs(price=4.00, unit_cost=2.00),
    ),
    "Fruit": Category(
        5,
        (0.95, 0.95, 1.0, 1.0, 1.05, 1.2, 1.1),
        (2, 4, 6, 7, 7, 7, 7, 6, 6, 6, 7, 7, 6, 4, 3, 2),
        0.03,
        Costs(price=3.00, unit_cost=1.50, salvage=0.50),
    ),
}

# Name, category and the units sold on an ordinary day.
PRODUCTS = [
    ("White sliced pan", "Bread", 24),
    ("Brown soda bread", "Bread", 14),
    ("Sourdough loaf", "Bread", 8),
    ("Wholemeal pan", "Bread", 12),
    ("Bagels, 4 pack", "Bread", 6),
    ("Whole milk, 2 litres", "Dairy", 30),
    ("Low-fat milk, 2 litres", "Dairy", 18),
    ("Fresh cream, 250 ml", "Dairy", 7),
    ("Breakfast roll", "Deli", 28),
    ("Chicken fillet roll", "Deli", 32),
    ("Ham and cheese sandwich", "Deli", 12),
    ("Tuna and sweetcorn wrap", "Deli", 9),
    ("Caesar salad bowl", "Salads", 8),
    ("Pasta salad", "Salads", 6),
    ("Coleslaw tub", "Salads", 5),
    ("Strawberries, punnet", "Fruit", 10),
    ("Bananas, bunch", "Fruit", 16),
    ("Blueberries, punnet", "Fruit", 7),
    ("Apples, 4 pack", "Fruit", 9),
    ("Fruit salad pot", "Fruit", 6),
]


PROMOTION_CHANCE = 0.08
PROMOTION_DISCOUNT = 0.8
PROMOTION_LIFT = 1.35
RAIN_EFFECT = 0.92
# The simulated owner stocks 95% to 130% of expected demand each morning, so some
# days sell out, as they do in a real shop.
STOCK_RANGE = (0.95, 1.3)
BANK_HOLIDAYS = {date(2026, 6, 1), date(2026, 8, 3), date(2026, 10, 26)}


def simulate_weather(dates: pd.DatetimeIndex, rng: np.random.Generator) -> pd.DataFrame:
    """Return invented daily weather with an Irish seasonal shape: mild and often wet."""
    n_days = len(dates)
    seasonal = 11 + 5 * np.cos(2 * np.pi * (dates.dayofyear.to_numpy() - 200) / 365)
    rainy = rng.random(n_days) < 0.55
    return pd.DataFrame(
        {
            "date": dates,
            "temperature": seasonal + rng.normal(0, 1.5, n_days),
            "precipitation": np.where(rainy, rng.gamma(2.0, 2.0, n_days), 0.0),
            "humidity": np.clip(rng.normal(80, 7, n_days), 50, 100),
            "wind_level": rng.uniform(1, 5, n_days),
            "holiday": [int(day.date() in BANK_HOLIDAYS) for day in dates],
        }
    )


def simulate_day(
    expected: float, weights: np.ndarray, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return one product-day's hourly demand, hourly sales and hourly stock flags."""
    demand = np.zeros(24)
    sales = np.zeros(24)
    out_of_stock = np.zeros(24, dtype=int)
    demand[TRADING_HOURS] = rng.multinomial(rng.poisson(expected), weights)
    stock = round(expected * rng.uniform(*STOCK_RANGE))
    cumulative = np.cumsum(demand[TRADING_HOURS])
    sales[TRADING_HOURS] = np.diff(np.minimum(cumulative, stock), prepend=0)
    out_of_stock[TRADING_HOURS] = cumulative >= stock
    return demand, sales, out_of_stock


def simulate_demo_store(
    end_date: date, n_days: int = 120, seed: int = 42
) -> pd.DataFrame:
    """Return n_days of simulated daily sales for every demo product, up to end_date.

    true_demand is what customers wanted, and sales is what they could buy before
    the shelf ran out.
    """
    rng = np.random.default_rng(seed)
    weather = simulate_weather(pd.date_range(end=end_date, periods=n_days), rng)
    rows = []
    for product_id, (name, category_name, base) in enumerate(PRODUCTS, start=1):
        category = CATEGORIES[category_name]
        weights = np.array(category.hourly_weights) / sum(category.hourly_weights)
        for day in weather.itertuples():
            # Bank holidays sell like Sundays.
            weekday = 6 if day.holiday else day.date.dayofweek
            on_promotion = rng.random() < PROMOTION_CHANCE
            expected = (
                base
                * category.weekday_factors[weekday]
                * (PROMOTION_LIFT if on_promotion else 1.0)
                * (1 + category.heat_lift * max(day.temperature - 14, 0))
                * (RAIN_EFFECT if day.precipitation > 2 else 1.0)
            )
            demand, sales, out_of_stock = simulate_day(expected, weights, rng)
            rows.append(
                {
                    "store_id": 1,
                    "product_id": product_id,
                    "product_name": name,
                    "category": category_name,
                    "category_id": category.category_id,
                    "date": day.date,
                    "true_demand": int(demand.sum()),
                    "sales": int(sales.sum()),
                    "stockout_hours": int(out_of_stock[TRADING_HOURS].sum()),
                    "hourly_sales": sales,
                    "hourly_out_of_stock": out_of_stock,
                    "discount": PROMOTION_DISCOUNT if on_promotion else 1.0,
                    "activity": int(on_promotion),
                    "holiday": day.holiday,
                    "precipitation": day.precipitation,
                    "temperature": day.temperature,
                    "humidity": day.humidity,
                    "wind_level": day.wind_level,
                }
            )
    return pd.DataFrame(rows)
