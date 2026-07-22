import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS, paging_params


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:

    @mcp.tool()
    async def cloudradial_get_feedback(
        skip: int | None = None,
        take: int | None = None,
        order: str | None = None,
        direction: str | None = None,
        filter_field: str | None = None,
        condition: str | None = None,
        value: str | None = None,
    ) -> str:
        """List CSAT/feedback records collected from ticket closures or the portal.

        API: GET /api/beta/feedback

        Args:
            skip: Number of records to skip (pagination offset). Default 0.
            take: Number of records to return. Default 10.
            order: Field name to sort by.
            direction: Sort direction: "a" (ascending) or "d" (descending).
            filter_field: Field name to filter on.
            condition: Filter condition: "eq" (equals) or "contains".
            value: Value to test the filter against.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.get(
                "/api/beta/feedback",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_create_feedback(feedback: dict) -> str:
        """Submit a feedback/CSAT record (e.g. from an external PSA ticket-closure survey).

        API: POST /api/beta/feedback

        None of this schema's fields are marked required by the spec, but a
        useful record typically includes: companyId, companyPsaId,
        companyName, userEmail, userFirstName, userLastName, userId,
        userPsaId, agentEmail, agentFirstName, agentLastName, agentPsaId,
        feedbackRating (int), feedbackComment, sentiment (int), source (int),
        date, ticketPsaId, ticketSubject, ticketString, ticketDate, phone,
        feedbackOnWebsite (bool), feedbackReferralClick (bool),
        feedbackWantsFollowUp (bool), feedbackIpAddress, userAgent, id.

        Args:
            feedback: Dict of feedback fields as listed above (camelCase keys,
                matching the CloudRadial Feedback schema).
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.post("/api/beta/feedback", json_body=feedback)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_delete_feedback(id: int) -> str:
        """Delete a feedback record.

        API: DELETE /api/beta/feedback

        Args:
            id: Required feedback record ID to delete.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.delete("/api/beta/feedback", params={"id": id})
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"
