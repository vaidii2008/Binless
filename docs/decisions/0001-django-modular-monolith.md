# 1. Django as a modular monolith

Date: October 2026

## Context

Binless needs a web app with a database, an admin and later sign-up and multi-tenancy, plus forecasting code that also runs in a nightly batch and in benchmark scripts. I know Express and React better than any Python framework, but the forecasting stack (pandas, LightGBM) is Python.

## Decision

I use one Django project with server-rendered templates and HTMX, and keep the forecasting code in a separate plain Python package, `forecasting/`, that never imports Django. Django apps (`pages`, `orders`) call into it, never the other way round. A test fails if the forecasting package imports Django, and another fails if web code imports pandas, NumPy, LightGBM or the forecasting package.

## Consequences

- One language and one repository for the web app, the batch and the experiments.
- Django gives me migrations, the admin, an ORM and, later, django-allauth for accounts, so I write less plumbing.
- HTMX lets the slider update the table without a separate JavaScript front end.
- The forecasting package can be tested and benchmarked without a database or a web server.
- I'm learning Django's conventions as I go, which costs time compared with Express.
