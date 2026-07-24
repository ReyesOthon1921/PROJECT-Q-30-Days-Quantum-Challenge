from __future__ import annotations

import os

from werkzeug.middleware.proxy_fix import ProxyFix

from app import app


IS_PRODUCTION = (
    os.environ.get("AGROQ_DEPLOYMENT_MODE", "development")
    == "production"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
    PREFERRED_URL_SCHEME="https" if IS_PRODUCTION else "http",
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
)

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_port=1,
)
