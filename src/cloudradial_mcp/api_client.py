import asyncio
from typing import Any

import httpx

from ._json import error_envelope

DEFAULT_BASE_URL = "https://api.us.cloudradial.com"

_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_MAX_BACKOFF_SECONDS = 20.0

# One shared connection pool for the process lifetime. No credentials are
# ever stored on it — the Basic Auth pair is passed per-instance/per-request
# (see CloudRadialClient.__init__), so this is safe to share across
# tenants/requests (see server.py's contextvar-based credential isolation,
# which is what actually keeps tenants apart).
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True)
    return _http_client


# status_code -> (error code, retryable). status_code 0 means a network/
# connection-level failure (no response at all).
_STATUS_TO_CODE: dict[int, tuple[str, bool]] = {
    0: ("upstream_error", True),
    400: ("invalid_argument", False),
    401: ("unauthorized", False),
    403: ("unauthorized", False),
    404: ("not_found", False),
    422: ("invalid_argument", False),
    429: ("rate_limited", True),
}


def _classify(status_code: int) -> tuple[str, bool]:
    if status_code in _STATUS_TO_CODE:
        return _STATUS_TO_CODE[status_code]
    if status_code >= 500:
        return "upstream_error", True
    return "invalid_argument", False


class CloudRadialError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"CloudRadial API error {status_code}: {message}")

    def to_envelope(self) -> str:
        code, retryable = _classify(self.status_code)
        return error_envelope(code, self.message, retryable)


class CloudRadialClient:
    """Async httpx client wrapping the CloudRadial REST API.

    Auth is HTTP Basic: the Public Key is the username and the Private Key
    is the password (per CloudRadial's "Getting Started" docs — both are
    generated under Partner > Settings > Integrations > API). This server
    receives both per request via headers and never persists them.

    Reuses the module-level connection pool (see _get_http_client) across
    every call made through this instance, rather than opening a new
    connection per request. Requests get limited retry + backoff on
    429/5xx (see _request_with_retry).
    """

    def __init__(self, public_key: str, private_key: str, base_url: str = DEFAULT_BASE_URL):
        self._auth = httpx.BasicAuth(public_key, private_key)
        self._base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _clean_params(self, params: dict | None) -> dict:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    def _retry_delay(self, resp: httpx.Response, attempt: int) -> float:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), _MAX_BACKOFF_SECONDS)
            except ValueError:
                pass
        return min(2**attempt, _MAX_BACKOFF_SECONDS)

    def _parse_body(self, resp: httpx.Response) -> Any:
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return {"raw_response": resp.text}

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
                if isinstance(detail, dict):
                    msg = detail.get("message") or detail.get("error") or str(detail)
                else:
                    msg = str(detail)
            except ValueError:
                msg = resp.text
            raise CloudRadialError(resp.status_code, str(msg)[:500])

    async def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: Any = None,
    ) -> Any:
        client = _get_http_client()
        target = f"{self._base_url}{path}"
        headers = self._headers()
        params = self._clean_params(params)

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await client.request(
                    method,
                    target,
                    headers=headers,
                    params=params,
                    json=json_body,
                    auth=self._auth,
                )
            except httpx.RequestError as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(min(2**attempt, _MAX_BACKOFF_SECONDS))
                    continue
                raise CloudRadialError(0, f"Could not reach {target!r}: {e or type(e).__name__}") from e

            if resp.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES:
                await asyncio.sleep(self._retry_delay(resp, attempt))
                continue

            self._raise_for_status(resp)
            return self._parse_body(resp)

        # Unreachable in practice (loop always returns or raises above), but
        # keeps type checkers happy and guards against future edits.
        if last_exc:
            raise CloudRadialError(0, f"{last_exc}") from last_exc
        raise CloudRadialError(0, "request failed with no response")

    async def get(self, path: str, params: dict | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, params: dict | None = None, json_body: Any = None) -> Any:
        return await self.request("POST", path, params=params, json_body=json_body)

    async def patch(self, path: str, params: dict | None = None, json_body: Any = None) -> Any:
        return await self.request("PATCH", path, params=params, json_body=json_body)

    async def delete(self, path: str, params: dict | None = None, json_body: Any = None) -> Any:
        return await self.request("DELETE", path, params=params, json_body=json_body)
