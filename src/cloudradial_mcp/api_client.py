from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.us.cloudradial.com"


class CloudRadialError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"CloudRadial API error {status_code}: {message}")


class CloudRadialClient:
    """Async httpx client wrapping the CloudRadial REST API.

    Auth is HTTP Basic: the Public Key is the username and the Private Key
    is the password (per CloudRadial's "Getting Started" docs — both are
    generated under Partner > Settings > Integrations > API). This server
    receives both per request via headers and never persists them.
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

    async def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: Any = None,
    ) -> Any:
        target = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=30.0, auth=self._auth) as client:
                resp = await client.request(
                    method,
                    target,
                    headers=self._headers(),
                    params=self._clean_params(params),
                    json=json_body,
                )
        except httpx.RequestError as e:
            raise CloudRadialError(0, f"Could not reach {target!r}: {e or type(e).__name__}") from None

        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            raise CloudRadialError(resp.status_code, str(detail)[:500])

        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return {"raw_response": resp.text}

    async def get(self, path: str, params: dict | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, params: dict | None = None, json_body: Any = None) -> Any:
        return await self.request("POST", path, params=params, json_body=json_body)

    async def patch(self, path: str, params: dict | None = None, json_body: Any = None) -> Any:
        return await self.request("PATCH", path, params=params, json_body=json_body)

    async def delete(self, path: str, params: dict | None = None, json_body: Any = None) -> Any:
        return await self.request("DELETE", path, params=params, json_body=json_body)
