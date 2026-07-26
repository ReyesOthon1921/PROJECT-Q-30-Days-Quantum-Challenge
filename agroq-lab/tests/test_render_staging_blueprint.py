from pathlib import Path


def test_staging_blueprint_has_separate_services_and_persistent_backend():
    test_path = Path(__file__).resolve()
    root = test_path.parents[2]
    if not (root / "render.staging.yaml").is_file():
        root = test_path.parents[1]
    blueprint = (root / "render.staging.yaml").read_text(encoding="utf-8")
    assert "name: agroq-controlled-beta-backend" in blueprint
    assert "name: agroq-controlled-beta-frontend" in blueprint
    assert "mountPath: /var/data" in blueprint
    assert "AGROQ_DB_PATH" in blueprint
    assert "value: /var/data/agroq.db" in blueprint
    assert "AGROQ_BACKUP_DIR" in blueprint
    assert 'value: "1"' in blueprint
    assert blueprint.count("autoDeployTrigger: off") == 2
    assert "property: hostport" in blueprint


def test_frontend_proxy_preserves_same_origin_backend_routes():
    root = Path(__file__).resolve().parents[1]
    nginx = (
        root / "deployment" / "staging" / "nginx.conf.template"
    ).read_text(encoding="utf-8")
    dockerfile = (
        root / "deployment" / "staging" / "frontend.Dockerfile"
    ).read_text(encoding="utf-8")
    assert "location /app/" in nginx
    assert "proxy_pass http://${AGROQ_BACKEND_HOSTPORT}" in nginx
    assert "proxy_set_header X-Forwarded-Proto $scheme" in nginx
    assert "npm run build -- --base=/app/" in dockerfile
    assert "/usr/share/nginx/html/app" in dockerfile
