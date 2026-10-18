# 3. The newsvendor rule for order quantities

Date: October 2026

## Context

The forecast is a range. The shop needs one number per product, chosen so the expected cost of leftovers and the expected cost of empty shelves balance.

## Decision

I use the newsvendor critical ratio: margin divided by margin plus waste cost, where the waste cost is the unit cost minus any salvage value. The ratio picks a quantile of the forecast, interpolating between the stored quantiles. Prices and costs per category are assumptions held in `forecasting/simulation.py` and labelled as such. The slider multiplies the cost of an empty shelf by 0.5, 1, 2 or 4, so the owner can count customers who may go elsewhere.

## Consequences

- The rule is short enough to explain to a shop owner and to test exactly.
- The owner's slider changes a cost assumption, not the forecast, which keeps the forecast honest.
- The rule assumes unsold stock is thrown away at the end of the day. That fits bread and deli items. For milk and fruit, which keep a few days, a salvage value only approximates the carry-over.
