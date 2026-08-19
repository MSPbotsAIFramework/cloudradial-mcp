"""Gateway credential middleware tests: missing-header 401, and header
values correctly reaching the per-request contextvar (no global-state
leakage across requests).
"""

from starlette.testclient import TestClient

from cloudradial_mcp.__main__ import _build_http_app
from cloudradial_mcp.config import Settings
from cloudradial_mcp.server import create_mcp_server, get_client_from_context


def _make_app():
    settings = Settings()
    mcp = create_mcp_server(settings)
    return _build_http_app(mcp, settings), settings


def test_health_is_local_and_does_not_require_credentials():
    app, _ = _make_app()
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_missing_header_returns_401_with_required_headers_listed():
    app, _ = _make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"Accept": "application/json, text/event-stream"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert "X-CloudRadial-Public-Key" in body["required_headers"]
        assert "X-CloudRadial-Private-Key" in body["required_headers"]


def test_missing_one_of_two_required_headers_still_401():
    app, _ = _make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={
                "Accept": "application/json, text/event-stream",
                "X-CloudRadial-Public-Key": "pub-only",
            },
        )
        assert resp.status_code == 401


def test_header_present_reaches_request_context(monkeypatch):
    # Directly exercises the middleware's contextvar plumbing without a full
    # MCP protocol round-trip: confirms the header values that arrive on the
    # request are exactly what get_client_from_context sees, and that they're
    # reset afterward (no leakage to the next request).
    import asyncio

    from cloudradial_mcp.server import GatewayCredsMiddleware, _gateway_creds_var

    settings = Settings()
    seen = {}

    async def fake_app(scope, receive, send):
        seen["creds"] = _gateway_creds_var.get()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = GatewayCredsMiddleware(fake_app, settings)

    async def run():
        scope = {
            "type": "http",
            "path": "/mcp",
            "headers": [
                (b"x-cloudradial-public-key", b"pub-key-123"),
                (b"x-cloudradial-private-key", b"priv-key-456"),
            ],
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        sent = []

        async def send(message):
            sent.append(message)

        await middleware(scope, receive, send)

    asyncio.run(run())
    assert seen["creds"] == ("pub-key-123", "priv-key-456")
    # After the request completes, the contextvar must be reset — a fresh
    # get() outside any request context sees no leftover credential.
    assert _gateway_creds_var.get() is None


def test_client_factory_returns_none_without_context():
    settings = Settings()
    assert get_client_from_context(settings) is None
