from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_every_demo_passes_its_own_checks():
    """Mirrors the UI's "Run all demos": every route under /api/demos must pass its self-checks."""
    routes = [r for r in app.routes if getattr(r, "path", "").startswith("/api/demos/")]
    assert routes
    for route in routes:
        method = sorted(route.methods)[0]
        body = client.request(method, route.path).json()
        assert body["checks"], route.path
        failed = [c for c in body["checks"] if not c["passed"]]
        assert not failed, f"{route.path}: {failed}"


def test_pitfall_mode_shows_the_real_error():
    """Pitfall demos run the wrong way for real: the error must be recorded and the checks still pass."""
    body = client.post("/api/demos/hello", params={"mistake": True}).json()
    assert body["data"]["error"]
    assert all(c["passed"] for c in body["checks"]), body["checks"]
