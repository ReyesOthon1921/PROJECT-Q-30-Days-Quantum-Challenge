FROM node:24-alpine AS frontend-build

WORKDIR /frontend

COPY agroq-lab/investor-ui/package.json ./
COPY agroq-lab/investor-ui/package-lock.json ./
RUN npm ci

COPY agroq-lab/investor-ui/ ./
RUN npm run build -- --base=/app/


FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AGROQ_DEPLOYMENT_MODE=production \
    AGROQ_BIND_HOST=0.0.0.0 \
    AGROQ_DEBUG=false

WORKDIR /app

RUN groupadd --system agroq \
    && useradd --system --gid agroq --home-dir /app agroq

COPY agroq-lab/requirements.txt ./requirements.txt
COPY agroq-lab/requirements-render.txt ./requirements-render.txt

RUN python -m pip install --no-cache-dir \
    -r requirements-render.txt

COPY agroq-lab/ ./
COPY --from=frontend-build /frontend/dist ./investor-ui/dist

RUN mkdir -p /app/instance /app/backups \
    && chown -R agroq:agroq /app

USER agroq

EXPOSE 10000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-4} --timeout 120 --graceful-timeout 30 --access-logfile - --error-logfile - wsgi:app"]
