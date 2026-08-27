from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped, error_envelope
from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:
    # Note: these are CloudRadial portal "tokens" — @-prefixed merge-field
    # variables used inside Articles/Automations/Messages (see "Understanding
    # Tokens" / "Using Tokens in Articles and Messages" in CloudRadial's
    # support docs). They are unrelated to API authentication.

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def cloudradial_get_tokens(
        company_id: Annotated[int | None, Field(description="Scope to a specific company's tokens.")] = None,
    ) -> str:
        """List portal merge-field tokens (@-prefixed variables used in
        Articles/Automations/Messages) — unrelated to API authentication
        despite the name; this server has no auth-token management
        capability at all.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.get(
                "/api/beta/token", params={"companyId": company_id} if company_id is not None else None
            )
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool()
    async def cloudradial_set_token(
        company_id: Annotated[int | None, Field(description="Company ID to scope the token to.")] = None,
        token: Annotated[str | None, Field(description="Token/variable name (without the leading @).")] = None,
        value: Annotated[str | None, Field(description="Value to assign to the token.")] = None,
        type: Annotated[str | None, Field(description="Optional token type.")] = None,
    ) -> str:
        """Create or update a portal merge-field token value — unrelated to
        API authentication despite the name.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        payload = {"companyId": company_id, "token": token, "value": value, "type": type}
        try:
            result = await client.post("/api/beta/token", json_body={k: v for k, v in payload.items() if v is not None})
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
    async def cloudradial_delete_token(
        company_id: Annotated[int | None, Field(description="Company ID the token is scoped to.")] = None,
        token: Annotated[str | None, Field(description="Token/variable name to delete.")] = None,
        value: Annotated[str | None, Field(description="Optional value (some deployments key on value + token).")] = None,
        type: Annotated[str | None, Field(description="Optional token type.")] = None,
        confirm: Annotated[bool, Field(description="Required — must be set to true to proceed.")] = False,
    ) -> str:
        """Delete a portal merge-field token — unrelated to API
        authentication despite the name; this is not how to revoke or
        remove an API key/credential.

        Destructive and irreversible. Requires confirm=true.
        """
        if not confirm:
            return error_envelope(
                "invalid_argument", "destructive operation requires confirm=true", False
            )
        client = client_factory()
        if client is None:
            return NO_CREDS
        payload = {"companyId": company_id, "token": token, "value": value, "type": type}
        try:
            result = await client.delete(
                "/api/beta/token", json_body={k: v for k, v in payload.items() if v is not None}
            )
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()
