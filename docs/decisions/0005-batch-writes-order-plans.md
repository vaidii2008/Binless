# 5. The batch writes complete order plans and the web app only reads them

Date: October 2026

## Context

The order page's slider changes the order quantity for every product. Working that out per request would need pandas and LightGBM in the web image, which would slow its cold start and grow the image.

## Decision

A nightly batch Lambda, scheduled by EventBridge Scheduler at 02:00 Dublin time, loads a trained model version from S3, forecasts tomorrow and saves one row per product. Each row holds the quantile forecasts, the order for every slider position and the reasons, in JSON columns. A unique constraint on product and date means a rerun replaces that day's rows instead of duplicating them. The web app reads the newest day's rows and never runs a model.

## Consequences

- The web image stays small and has no forecasting libraries.
- Moving the slider is a database read, so it's fast.
- The schema lives only in Django models, because the batch writes through the Django ORM.
- Changing the slider positions means rerunning the batch, since the orders are precomputed.
- If the batch fails, the page keeps showing the last saved day, which goes stale. An alarm on batch failures is planned for Phase 2.
