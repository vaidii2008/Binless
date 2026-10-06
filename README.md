# Binless

![CI](https://github.com/vaidii2008/Binless/actions/workflows/ci.yml/badge.svg)

Binless tells an independent grocer how much of each fresh product to order for tomorrow, explains why in plain English, and measures the waste it avoids.

I'm building it as a portfolio project while learning Python. It's a work in progress, and this README describes what exists today.

## Why

Fresh food that isn't sold by its date is thrown away, and a product that sells out loses sales for the rest of the day. Binless gives a shop owner a forecast range for each product and turns it into an order quantity that weighs the cost of waste against the cost of an empty shelf.

## What works so far

- A Django web app with a health check, tested with pytest and checked by GitHub Actions on every push.
- A forecasting package in plain Python, with no Django imports, containing a FreshRetailNet-50K adapter and two baselines: the same day last week, and a 7-day moving average.
- A test that fails if the forecasting package ever imports Django.
- An exploration notebook on a 50-store subset of FreshRetailNet-50K.

## What the data shows

In a random 50-store subset (seed 42), 44.1% of store-product days had at least one out-of-stock trading hour, and 73.1% of days with zero sales were out of stock all day. Recorded sales can understate demand on those days, so Binless corrects for stockouts before training a model.

To reproduce these figures, run `python scripts/download_frn.py`, then run `notebooks/01_explore_frn.ipynb`.

## Planned

- LightGBM quantile forecasts (P50, P80 and P90) trained on stockout-corrected sales.
- An order rule based on the newsvendor critical ratio.
- A backtest of waste and stockout rates against the baselines.
- A deployed demo for a simulated Irish shop, labelled as simulated wherever it appears.

## Run it locally

Requires Python 3.12.

```zsh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements/dev.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Paste the printed key into `.env` as `DJANGO_SECRET_KEY`, then:

```zsh
python -m pytest
python manage.py runserver
```

## Data

The benchmark data is [FreshRetailNet-50K](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K) by Dingdong-Inc, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The download script keeps a random subset of stores and the adapter renames columns to Binless's own names. The dataset's IDs are encoded and its sales are normalised, so no product names from it appear anywhere in Binless.

