import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:
    # This tag exposes CloudRadial's IT Glue-compatible "Flexible Assets"
    # layer under /compatibility — a JSON:API-shaped surface for custom
    # asset/document types, mirroring the IT Glue Flexible Assets API.

    @mcp.tool()
    async def cloudradial_get_flexible_assets(
        flexible_asset_type_id: int,
        organization_id: str | None = None,
        name: str | None = None,
        page_number: int | None = None,
        page_size: int | None = None,
        include: str | None = None,
        sort: str | None = None,
    ) -> str:
        """List flexible assets (IT Glue-compatible custom asset records) of a given type.

        API: GET /compatibility/flexible_assets

        Args:
            flexible_asset_type_id: Required — filter[flexible-asset-type-id].
            organization_id: Optional — filter[organization-id].
            name: Optional — filter[name].
            page_number: Optional page[number].
            page_size: Optional page[size].
            include: Optional related-resource include list.
            sort: Optional sort field.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        params = {
            "filter[flexible-asset-type-id]": flexible_asset_type_id,
            "filter[organization-id]": organization_id,
            "filter[name]": name,
            "page[number]": page_number,
            "page[size]": page_size,
            "include": include,
            "sort": sort,
        }
        try:
            result = await client.get("/compatibility/flexible_assets", params=params)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_create_flexible_asset(
        flexible_asset_type_id: int,
        traits: dict[str, object],
        organization_id: str | None = None,
        archived: bool | None = None,
        type: str = "flexible-assets",
    ) -> str:
        """Create a flexible asset (IT Glue-compatible custom asset record).

        API: POST /compatibility/flexible_assets

        Args:
            flexible_asset_type_id: Required — the asset type this record belongs to.
            traits: Required dict of field-name -> value for this asset type's custom fields.
            organization_id: Optional organization (company) ID to associate the asset with.
            archived: Optional archived flag.
            type: JSON:API resource type string. Default "flexible-assets".
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        attributes = {
            "flexible-asset-type-id": flexible_asset_type_id,
            "traits": traits,
            "organization-id": organization_id,
            "archived": archived,
        }
        body = {"data": {"type": type, "attributes": {k: v for k, v in attributes.items() if v is not None}}}
        try:
            result = await client.post("/compatibility/flexible_assets", json_body=body)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_update_flexible_assets(assets: list[dict]) -> str:
        """Bulk-update flexible assets.

        API: PATCH /compatibility/flexible_assets

        Args:
            assets: List of full JSON:API resource objects, each shaped as
                {"type": "flexible-assets", "attributes": {"id": <int, required>,
                "flexible-asset-type-id": <str>, "archived": <str>,
                "traits": {...}, "organization-id": <str>}}. Only include the
                attribute keys you want to change (plus id, which is required).
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.patch("/compatibility/flexible_assets", json_body={"data": assets})
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_delete_flexible_assets(ids: list[int], type: str = "flexible-assets") -> str:
        """Bulk-delete flexible assets by ID.

        API: DELETE /compatibility/flexible_assets

        Args:
            ids: Required list of flexible asset IDs to delete.
            type: JSON:API resource type string. Default "flexible-assets".
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        body = {"data": [{"type": type, "attributes": {"id": i}} for i in ids]}
        try:
            result = await client.delete("/compatibility/flexible_assets", json_body=body)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_get_flexible_asset(id: int, include: str | None = None) -> str:
        """Get a single flexible asset by ID.

        API: GET /compatibility/flexible_assets/{id}

        Args:
            id: Required flexible asset ID.
            include: Optional related-resource include list.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.get(
                f"/compatibility/flexible_assets/{id}", params={"include": include} if include else None
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_delete_flexible_asset(id: int) -> str:
        """Delete a single flexible asset by ID.

        API: DELETE /compatibility/flexible_assets/{id}

        Args:
            id: Required flexible asset ID to delete.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.delete(f"/compatibility/flexible_assets/{id}")
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_update_flexible_asset(
        id: int,
        flexible_asset_type_id: str | None = None,
        archived: str | None = None,
        traits: dict[str, object] | None = None,
        organization_id: str | None = None,
        type: str = "flexible-assets",
    ) -> str:
        """Update a single flexible asset by ID.

        API: PATCH /compatibility/flexible_assets/{id}

        Args:
            id: Required flexible asset ID to update.
            flexible_asset_type_id: Optional new asset type ID (as a string per spec).
            archived: Optional archived flag (as a string per spec, e.g. "true"/"false").
            traits: Optional dict of field-name -> value to update.
            organization_id: Optional new organization (company) ID.
            type: JSON:API resource type string. Default "flexible-assets".
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        attributes = {
            "flexible-asset-type-id": flexible_asset_type_id,
            "archived": archived,
            "traits": traits,
            "organization-id": organization_id,
        }
        body = {
            "data": {
                "id": id,
                "type": type,
                "attributes": {k: v for k, v in attributes.items() if v is not None},
            }
        }
        try:
            result = await client.patch(f"/compatibility/flexible_assets/{id}", json_body=body)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_create_organization_flexible_assets(org_id: int, assets: list[dict]) -> str:
        """Bulk-create flexible assets under a specific organization (company).

        API: POST /compatibility/organizations/{orgId}/relationships/flexible_assets

        Args:
            org_id: Required organization (company) ID to attach the assets to.
            assets: Required list of asset objects, each shaped as
                {"type": "flexible-assets", "attributes": {"flexible-asset-type-id":
                <int, required>, "traits": {..., required}, "organization-id": <str>,
                "archived": <bool>}}.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.post(
                f"/compatibility/organizations/{org_id}/relationships/flexible_assets",
                json_body={"data": assets},
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"
