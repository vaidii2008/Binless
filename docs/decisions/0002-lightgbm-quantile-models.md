# 2. LightGBM quantile models

Date: October 2026

## Context

A shop owner needs a quantity, but the right quantity depends on how costly waste is compared with an empty shelf, and that differs by product. A single forecast can't express that. The data has tens of thousands of short series (90 days each in FreshRetailNet-50K) with calendar, promotion and weather covariates.

## Decision

I train one global LightGBM model per quantile on sales scaled by each series' recent mean, with lag, rolling, calendar, promotion and weather features. The benchmark uses the 50th, 80th and 90th percentiles. The live shop uses a grid from the 10th to the 95th, so the order rule can pick any point in between.

## Consequences

- One model learns from every product, which suits short series better than a model per product.
- Gradient-boosted trees train in seconds on a laptop and need no GPU, so the nightly batch fits in a small Lambda.
- Per-feature contributions give each forecast plain-English reasons, though I need a separate mean-regression model for them because contributions don't add up for the quantile objective.
- Separate models per quantile can cross, so predictions are sorted per row.
- On the held-out week it matches the dataset authors' deep-learning models trained on recorded sales, at a fraction of the complexity. Their best model, trained on recovered demand, is still 2.55 WAPE points better.
- Comparing it with a pretrained time-series model (Amazon Chronos) is planned for Phase 2.
