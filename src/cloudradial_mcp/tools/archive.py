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
    async def cloudradial_get_archives(
        skip: Annotated[int | None, Field(description="Records to skip (pagination offset). Default 0.")] = None,
        take: Annotated[int | None, Field(description="Records to return (default 10, max 200).")] = None,
        order: Annotated[str | None, Field(description="Field name to sort by.")] = None,
        direction: Annotated[str | None, Field(description='Sort direction: "a" (ascending) or "d" (descending).')] = None,
        filter_field: Annotated[str | None, Field(description='Field name to filter on (e.g. "name").')] = None,
        condition: Annotated[str | None, Field(description='Filter condition: "eq" or "contains".')] = None,
        value: Annotated[str | None, Field(description="Value to test the filter against.")] = None,
    ) -> str:
        """List report archives (containers for uploaded/synced reports)."""
        client = client_factory()
        if client is None:
            return NO_CREDS
        if take is not None:
            take = min(take, _MAX_TAKE)
        try:
            result = await client.get(
                "/api/beta/archive",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool()
    async def cloudradial_create_archive(
        archive: Annotated[
            dict[str, object],
            Field(
                description=(
                    "Archive fields (camelCase keys, matching the CloudRadial "
                    "Archive schema). None are required by the spec, but a "
                    "useful definition typically includes: name, companyId, "
                    "category, retainForDays, inboundAddress (the "
                    "archive-unique upload email), estimatedTime, "
                    "warnOnPastDays, lastErrorDays, lastErrorKeywords, "
                    "alertKeywords, requiredKeywords, isSendOnEveryError, "
                    "isShowMessage, isSendToPsa + psaBoard/psaCategory/"
                    "psaType/psaSubType/psaPriority/psaSource/psaStatus/"
                    "psaItem (PSA ticket-routing fields), emailNoticeList, "
                    "partnerEmailList, slackWebhook/slackPartnerWebhook, "
                    "teamsWebhook/teamsPartnerWebhook, flowPartnerWebhook, "
                    "jsonPartnerWebhook, companyGroups, userGroups, id (set "
                    "to update)."
                )
            ),
        ],
    ) -> str:
        """Create (or, with id set, update) a report archive definition."""
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.post("/api/beta/archive", json_body=archive)
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
    async def cloudradial_delete_archive(
        archive_id: Annotated[int, Field(description="Required archive ID to delete.")],
        confirm: Annotated[bool, Field(description="Required — must be set to true to proceed.")] = False,
    ) -> str:
        """Delete a report archive and its contained items.

        Destructive and irreversible — also removes every item inside the
        archive. Requires confirm=true.
        """
        if not confirm:
            return error_envelope(
                "invalid_argument", "destructive operation requires confirm=true", False
            )
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.delete(f"/api/beta/archive/{archive_id}")
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def cloudradial_get_archive_items(
        archive_id: Annotated[int, Field(description="Required archive ID.")],
        skip: Annotated[int | None, Field(description="Records to skip (pagination offset). Default 0.")] = None,
        take: Annotated[int | None, Field(description="Records to return (default 10, max 200).")] = None,
        order: Annotated[str | None, Field(description="Field name to sort by.")] = None,
        direction: Annotated[str | None, Field(description='Sort direction: "a" (ascending) or "d" (descending).')] = None,
        filter_field: Annotated[str | None, Field(description="Field name to filter on.")] = None,
        condition: Annotated[str | None, Field(description='Filter condition: "eq" or "contains".')] = None,
        value: Annotated[str | None, Field(description="Value to test the filter against.")] = None,
    ) -> str:
        """List items (individual uploaded/received reports) inside an archive."""
        client = client_factory()
        if client is None:
            return NO_CREDS
        if take is not None:
            take = min(take, _MAX_TAKE)
        try:
            result = await client.get(
                f"/api/beta/archive/{archive_id}/item",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool()
    async def cloudradial_create_archive_item(
        archive_id: Annotated[int, Field(description="Required archive ID to add the item to.")],
        item: Annotated[
            dict[str, object],
            Field(
                description=(
                    "Payload for the archive item. CloudRadial does not publish "
                    "a schema for this request body (uploads via the portal "
                    "support drag-and-drop, an archive-unique email address, or "
                    "this API connection — see 'Using Report Archives' in "
                    "CloudRadial's support docs, which notes API uploads are "
                    "limited to 128MB). Pass whatever the caller's integration "
                    "expects — typically report content plus metadata (e.g. "
                    "fileName, content, contentType, dateReceived). Verify the "
                    "exact shape with CloudRadial support or by inspecting a "
                    "successful portal-side upload before relying on this in "
                    "production."
                )
            ),
        ],
    ) -> str:
        """Add an item (report) to an archive."""
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.post(f"/api/beta/archive/{archive_id}/item", json_body=item)
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
    async def cloudradial_delete_archive_item(
        archive_id: Annotated[int, Field(description="Required archive ID.")],
        item_id: Annotated[int, Field(description="Required item ID to delete.")],
        confirm: Annotated[bool, Field(description="Required — must be set to true to proceed.")] = False,
    ) -> str:
        """Delete a single item from an archive.

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
            result = await client.delete(f"/api/beta/archive/{archive_id}/item/{item_id}")
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()
