
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
COPY orders orders
# Lambda runs the code as a non-root user, so every file must be readable by all users.
RUN chmod -R a+rX /app

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "0", "--no-control-socket"]

# The batch image has no Web Adapter: Lambda calls the handler directly.
FROM public.ecr.aws/lambda/python:3.12 AS batch

ENV PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings

# LightGBM needs the OpenMP runtime, which the Lambda base image leaves out.
RUN dnf install -y libgomp && dnf clean all
COPY requirements/web.txt requirements/batch.txt requirements/
RUN pip install --no-cache-dir -r requirements/web.txt -r requirements/batch.txt
COPY manage.py ./
COPY config config
COPY pages pages
COPY orders orders
COPY forecasting forecasting
COPY batch batch
RUN chmod -R a+rX /var/task

CMD ["batch.handler.handler"]
