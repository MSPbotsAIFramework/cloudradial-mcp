from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped, error_envelope
from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS, paging_params

_MAX_TAKE = 200


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def cloudradial_get_feedback(
        skip: Annotated[int | None, Field(description="Records to skip (pagination offset). Default 0.")] = None,
        take: Annotated[int | None, Field(description="Records to return (default 10, max 200).")] = None,
        order: Annotated[str | None, Field(description="Field name to sort by.")] = None,
        direction: Annotated[str | None, Field(description='Sort direction: "a" (ascending) or "d" (descending).')] = None,
        filter_field: Annotated[str | None, Field(description="Field name to filter on.")] = None,
        condition: Annotated[str | None, Field(description='Filter condition: "eq" or "contains".')] = None,
        value: Annotated[str | None, Field(description="Value to test the filter against.")] = None,
    ) -> str:
        """List CSAT/feedback records collected from ticket closures or the portal."""
        client = client_factory()
        if client is None:
            return NO_CREDS
        if take is not None:
            take = min(take, _MAX_TAKE)
        try:
            result = await client.get(
                "/api/beta/feedback",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool()
    async def cloudradial_create_feedback(
        feedback: Annotated[
            dict[str, object],
            Field(
                description=(
                    "Feedback fields (camelCase keys, matching the CloudRadial "
                    "Feedback schema). None are required by the spec, but a "
                    "useful record typically includes: companyId, companyPsaId, "
                    "companyName, userEmail, userFirstName, userLastName, "
                    "userId, userPsaId, agentEmail, agentFirstName, "
                    "agentLastName, agentPsaId, feedbackRating (int), "
                    "feedbackComment, sentiment (int), source (int), date, "
                    "ticketPsaId, ticketSubject, ticketString, ticketDate, "
                    "phone, feedbackOnWebsite (bool), feedbackReferralClick "
                    "(bool), feedbackWantsFollowUp (bool), feedbackIpAddress, "
                    "userAgent, id."
                )
            ),
        ],
    ) -> str:
        """Submit a feedback/CSAT record (e.g. from an external PSA ticket-closure survey)."""
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.post("/api/beta/feedback", json_body=feedback)
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
    async def cloudradial_delete_feedback(
        id: Annotated[int, Field(description="Required feedback record ID to delete.")],
        confirm: Annotated[bool, Field(description="Required — must be set to true to proceed.")] = False,
    ) -> str:
        """Delete a feedback record.

        Destructive and irreversible. Requires confirm=true.
        """
        if not confirm:
            return error_envelope(
                "invalid_argument", "destructive operation requires confirm=true", False
            )
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.delete("/api/beta/feedback", params={"id": id})
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()
