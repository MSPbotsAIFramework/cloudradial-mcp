import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:
    # Note: these are CloudRadial portal "tokens" — @-prefixed merge-field
    # variables used inside Articles/Automations/Messages (see "Understanding
    # Tokens" / "Using Tokens in Articles and Messages" in CloudRadial's
    # support docs). They are unrelated to API authentication.

    @mcp.tool()
    async def cloudradial_get_tokens(company_id: int | None = None) -> str:
        """List portal merge-field tokens (@-prefixed variables used in Articles/Automations).

        API: GET /api/beta/token

        Args:
            company_id: Optional — scope to a specific company's tokens.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.get(
                "/api/beta/token", params={"companyId": company_id} if company_id is not None else None
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_set_token(
        company_id: int | None = None,
        token: str | None = None,
        value: str | None = None,
        type: str | None = None,
    ) -> str:
        """Create or update a portal merge-field token value.

        API: POST /api/beta/token

        Args:
            company_id: Optional company ID to scope the token to.
            token: Token/variable name (without the leading @).
            value: Value to assign to the token.
            type: Optional token type.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        payload = {"companyId": company_id, "token": token, "value": value, "type": type}
        try:
            result = await client.post("/api/beta/token", json_body={k: v for k, v in payload.items() if v is not None})
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_delete_token(
        company_id: int | None = None,
        token: str | None = None,
        value: str | None = None,
        type: str | None = None,
    ) -> str:
        """Delete a portal merge-field token.

        API: DELETE /api/beta/token

        Args:
            company_id: Optional company ID the token is scoped to.
            token: Token/variable name to delete.
            value: Optional value (some deployments key on value + token).
            type: Optional token type.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        payload = {"companyId": company_id, "token": token, "value": value, "type": type}
        try:
            result = await client.delete(
                "/api/beta/token", json_body={k: v for k, v in payload.items() if v is not None}
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"
