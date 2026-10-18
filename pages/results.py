"""Benchmark figures shown on the results page.

Each figure is copied from a run of the command named next to it, as reported in
the README. Nothing here is computed by the web app.
"""

# python -m scripts.benchmark: last 4 weeks of the 50-store sample, fully stocked days.
ORDER_POLICIES = [
    {"policy": "Last week's sales", "waste": 20.6, "short": 43.6, "served": 78.2},
    {"policy": "7-day average", "waste": 16.4, "short": 45.3, "served": 82.9},
    {"policy": "Binless median (P50)", "waste": 14.6, "short": 47.4, "served": 83.7},
    {"policy": "Binless P80", "waste": 28.3, "short": 19.6, "served": 94.5},
    {"policy": "Binless P90", "waste": 35.8, "short": 10.9, "served": 97.2},
]

# python -m scripts.benchmark: WAPE on all days of the same four weeks.
FORECAST_ERROR = [
    {"method": "Same day last week", "wape": 42.6},
    {"method": "7-day moving average", "wape": 34.7},
    {"method": "Binless median (P50)", "wape": 31.9},
]

# python -m scripts.holdout_eval for mine; Table 3 of arXiv:2505.16319 for the authors'.
HELD_OUT = [
    {"model": "Same day last week", "by": "Mine", "wape": 38.91},
    {"model": "Binless median (P50)", "by": "Mine", "wape": 31.57},
    {"model": "SSA", "by": "Dataset authors", "wape": 31.97},
    {"model": "TFT", "by": "Dataset authors", "wape": 31.75},
    {"model": "DLinear", "by": "Dataset authors", "wape": 31.56},
    {"model": "TFT on recovered demand", "by": "Dataset authors", "wape": 29.02},
]
