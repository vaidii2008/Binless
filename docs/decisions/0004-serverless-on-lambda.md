# 4. Serverless deployment on Lambda with Neon Postgres

Date: October 2026

## Context

The app has almost no traffic and needs to stay up for months for recruiters and an assessment centre, on a budget close to zero. I don't want to patch a server.

## Decision

The Django app runs in a container image on AWS Lambda behind an API Gateway HTTP API, using the Lambda Web Adapter so Gunicorn serves it as an ordinary web app. A second image from the same Dockerfile runs the nightly batch as a plain Lambda handler. The database is Neon's serverless Postgres in London, the same region as the Lambdas, reached through its pooled endpoint. Secrets live in SSM Parameter Store. One SAM template defines everything, and the Lambdas run outside a VPC so there's no NAT gateway charge.

## Consequences

- Idle costs are close to nothing, since Lambda bills per request and Neon suspends when unused.
- The same images run on my laptop with `docker run`, so production isn't a different code path.
- The first request after a quiet spell is slow: the Lambda start-up took 3.8 and 6.2 seconds in the two cold starts I measured, plus Neon waking up.
- Lambda's disk is read-only apart from `/tmp`, so the app writes logs to stdout and the batch downloads models to `/tmp`.
- Neon's pooler uses transaction pooling, so Django's server-side cursors are turned off.
