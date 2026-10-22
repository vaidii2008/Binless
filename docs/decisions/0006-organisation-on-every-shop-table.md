# 6. Every shop table carries its organisation

Date: October 2026

## Context

In Phase 2 more than one business uses Binless. A wholesaler rolling it out to its independent retailers needs each shop's sales and orders kept away from every other shop, and one owner may run several shops. A single query that forgot to filter would show a shop owner another shop's figures.

## Decision

Organisations own shops. A user belongs to an organisation through a membership with a role: owner, manager or staff. Shops, products and forecasts each have their own organisation column, inherited from one abstract model, and their manager offers two ways in: `for_organisation(organisation)` and `for_user(user)`. A product takes its organisation from its shop, and a forecast from its product, whenever it's saved, so the column can't disagree with the shop. All organisations share one database and one schema.

A data migration moved the simulated shop into a sample organisation flagged `is_sample`. The public pages read only that organisation's shop.

## Consequences

- Every query filters on the organisation column directly, with no join back to the shop.
- The tests check each table, a user with and without memberships, and the public pages against a second organisation's data.
- The organisation on products and forecasts repeats what the shop already says. The save method keeps it in step, but bulk updates and raw SQL would skip it.
- Nothing stops code calling `Store.objects.all()`. The rule is that views start from `for_user` or `for_organisation`, and the tests and code review enforce it.
- One shared schema costs nothing extra on Neon's free plan and needs one migration for everyone. A schema or database per organisation would isolate more strongly, at the cost of migrating each one.
