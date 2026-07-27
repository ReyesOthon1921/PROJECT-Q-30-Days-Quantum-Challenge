import io

from staging_smoke import normalized_url, run_smoke


class FakeResponse:
    def __init__(self, status=200, body=b"ok"):
        self.status = status
        self._body = body

    def read(self, _limit):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def fake_open(request, timeout=20):
    assert timeout == 20
    assert request.full_url.startswith("https://staging.example/")
    return FakeResponse()


def test_normalized_url():
    assert normalized_url(
        "https://staging.example",
        "/healthz",
    ) == "https://staging.example/healthz"


def test_staging_smoke_passes_public_routes():
    report = run_smoke(
        "https://staging.example",
        ("/healthz", "/app/"),
        opener=fake_open,
    )
    assert report["passed"] is True
    assert len(report["checks"]) == 2
