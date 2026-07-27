from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, redirect, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
INVESTOR_DIST = BASE_DIR / "investor-ui" / "dist"


def register_production_portal(app: Flask) -> None:
    if "agroq_production_portal_registered" in app.extensions:
        return
    app.extensions["agroq_production_portal_registered"] = True

    @app.get("/healthz")
    def healthz() -> Any:
        return jsonify(
            {
                "ok": True,
                "service": "agroq-living-systems-lab",
                "deployment_mode": os.environ.get(
                    "AGROQ_DEPLOYMENT_MODE",
                    "development",
                ),
                "professional_ui_built": (
                    INVESTOR_DIST / "index.html"
                ).is_file(),
            }
        )

    @app.get("/professional")
    def professional_redirect() -> Response:
        return redirect("/app/", code=302)

    @app.get("/app")
    @app.get("/app/")
    @app.get("/app/<path:asset_path>")
    def professional_app(asset_path: str = "") -> Response:
        index_path = INVESTOR_DIST / "index.html"
        if not index_path.is_file():
            return Response(
                "The professional frontend has not been built. "
                "Run npm run build -- --base=/app/.",
                status=503,
                mimetype="text/plain",
            )

        if asset_path:
            requested = (INVESTOR_DIST / asset_path).resolve()
            try:
                requested.relative_to(INVESTOR_DIST.resolve())
            except ValueError:
                return Response("Invalid asset path.", status=400)

            if requested.is_file():
                return send_from_directory(
                    INVESTOR_DIST,
                    asset_path,
                    max_age=31536000 if "assets/" in asset_path else 0,
                )

        return send_from_directory(
            INVESTOR_DIST,
            "index.html",
            max_age=0,
        )

    @app.after_request
    def production_security_headers(response: Response) -> Response:
        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "X-Frame-Options",
            "DENY",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=()"
            ),
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            (
                "default-src 'self'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "object-src 'none'; "
                "img-src 'self' data: blob:; "
                "font-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; "
                "connect-src 'self' "
                "https://eutils.ncbi.nlm.nih.gov; "
                "worker-src 'self' blob:; "
                "manifest-src 'self'"
            ),
        )
        if os.environ.get(
            "AGROQ_DEPLOYMENT_MODE",
            "development",
        ) == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response
