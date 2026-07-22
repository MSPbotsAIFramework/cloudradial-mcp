import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS, paging_params


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:

    @mcp.tool()
    async def cloudradial_get_archives(
        skip: int | None = None,
        take: int | None = None,
        order: str | None = None,
        direction: str | None = None,
        filter_field: str | None = None,
        condition: str | None = None,
        value: str | None = None,
    ) -> str:
        """List report archives (containers for uploaded/synced reports).

        API: GET /api/beta/archive

        Args:
            skip: Number of records to skip (pagination offset). Default 0.
            take: Number of records to return. Default 10.
            order: Field name to sort by.
            direction: Sort direction: "a" (ascending) or "d" (descending).
            filter_field: Field name to filter on (e.g. "name").
            condition: Filter condition: "eq" (equals) or "contains".
            value: Value to test the filter against.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.get(
                "/api/beta/archive",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_create_archive(archive: dict) -> str:
        """Create (or, with id set, update) a report archive definition.

        API: POST /api/beta/archive

        No field is marked required by the spec, but a useful archive
        definition typically includes: name, companyId, category,
        retainForDays, inboundAddress (the archive-unique upload email),
        estimatedTime, warnOnPastDays, lastErrorDays, lastErrorKeywords,
        alertKeywords, requiredKeywords, isSendOnEveryError, isShowMessage,
        isSendToPsa + psaBoard/psaCategory/psaType/psaSubType/psaPriority/
        psaSource/psaStatus/psaItem (PSA ticket-routing fields),
        emailNoticeList, partnerEmailList, slackWebhook/slackPartnerWebhook,
        teamsWebhook/teamsPartnerWebhook, flowPartnerWebhook,
        jsonPartnerWebhook, companyGroups, userGroups, id (set to update).

        Args:
            archive: Dict of archive fields as listed above (camelCase keys,
                matching the CloudRadial Archive schema).
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.post("/api/beta/archive", json_body=archive)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_delete_archive(archive_id: int) -> str:
        """Delete a report archive (and its contained items).

        API: DELETE /api/beta/archive/{archiveId}

        Args:
            archive_id: Required archive ID to delete.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.delete(f"/api/beta/archive/{archive_id}")
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_get_archive_items(
        archive_id: int,
        skip: int | None = None,
        take: int | None = None,
        order: str | None = None,
        direction: str | None = None,
        filter_field: str | None = None,
        condition: str | None = None,
        value: str | None = None,
    ) -> str:
        """List items (individual uploaded/received reports) inside an archive.

        API: GET /api/beta/archive/{archiveId}/item

        Args:
            archive_id: Required archive ID.
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
                f"/api/beta/archive/{archive_id}/item",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_create_archive_item(archive_id: int, item: dict) -> str:
        """Add an item (report) to an archive.

        API: POST /api/beta/archive/{archiveId}/item

        The CloudRadial spec does not publish a schema for this request body
        (uploads via the portal support drag-and-drop, an archive-unique
        email address, or this API connection — see "Using Report Archives"
        in CloudRadial's support docs, which notes API uploads are limited to
        128MB). Pass whatever the caller's integration expects — this is
        typically the report content plus metadata (e.g. fileName, content,
        contentType, dateReceived). Verify the exact shape with CloudRadial
        support or by inspecting a successful portal-side upload before
        relying on this in production.

        Args:
            archive_id: Required archive ID to add the item to.
            item: Dict payload for the archive item (shape not published by
                the spec — see docstring above).
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.post(f"/api/beta/archive/{archive_id}/item", json_body=item)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_delete_archive_item(archive_id: int, item_id: int) -> str:
        """Delete a single item from an archive.

        API: DELETE /api/beta/archive/{archiveId}/item/{itemId}

        Args:
            archive_id: Required archive ID.
            item_id: Required item ID to delete.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.delete(f"/api/beta/archive/{archive_id}/item/{item_id}")
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"
