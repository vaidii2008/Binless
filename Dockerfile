
FROM python:3.12-slim AS web

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0 /lambda-adapter /opt/extensions/lambda-adapter

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AWS_LWA_PORT=8080 \
    AWS_LWA_READINESS_CHECK_PATH=/healthz

WORKDIR /app
COPY requirements/web.txt requirements/web.txt
RUN pip install --no-cache-dir -r requirements/web.txt
COPY manage.py ./
COPY config config
COPY pages pages

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1", "--no-control-socket"]
