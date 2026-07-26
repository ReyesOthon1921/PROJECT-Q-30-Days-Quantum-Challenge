from staging_acceptance_cli import PUBLIC_ROUTES, public_smoke, url


class FakeClient:
    def request(self, method, path, payload=None, form=None):
        assert method == "GET"
        return 200, path.encode("utf-8"), {}


def test_url_joining():
    assert url("https://staging.example", "/healthz") == (
        "https://staging.example/healthz"
    )


def test_public_smoke_covers_required_public_routes():
    results = public_smoke(FakeClient())
    assert len(results) == len(PUBLIC_ROUTES)
    assert all(item["passed"] for item in results)
    assert {item["check_code"] for item in results} == {
        "backend_health",
        "frontend_overview",
        "access_community",
    }
