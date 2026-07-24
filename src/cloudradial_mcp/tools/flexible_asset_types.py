import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:
    # Companion tag to flexible_assets.py: defines the custom asset "types"
    # (schemas) and their fields, under the same IT Glue-compatible layer.

    @mcp.tool()
    async def cloudradial_get_flexible_asset_types(
        id: str | None = None,
        name: str | None = None,
        icon: str | None = None,
        enabled: str | None = None,
        page_number: int | None = None,
        page_size: int | None = None,
        include: str | None = None,
        sort: str | None = None,
    ) -> str:
        """List flexible asset types (custom asset schemas).

        API: GET /compatibility/flexible_asset_types

        Args:
            id: Optional filter[id].
            name: Optional filter[name].
            icon: Optional filter[icon].
            enabled: Optional filter[enabled].
            page_number: Optional page[number].
            page_size: Optional page[size].
            include: Optional related-resource include list.
            sort: Optional sort field.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        params = {
            "filter[id]": id,
            "filter[name]": name,
            "filter[icon]": icon,
            "filter[enabled]": enabled,
            "page[number]": page_number,
            "page[size]": page_size,
            "include": include,
            "sort": sort,
        }
        try:
            result = await client.get("/compatibility/flexible_asset_types", params=params)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_create_flexible_asset_type(
        name: str,
        description: str | None = None,
        icon: str | None = None,
        show_in_menu: bool | None = None,
        fields: list[dict] | None = None,
        type: str = "flexible-asset-types",
    ) -> str:
        """Create a flexible asset type (custom asset schema), optionally with its fields.

        API: POST /compatibility/flexible_asset_types

        Args:
            name: Required type name.
            description: Optional description.
            icon: Optional icon identifier.
            show_in_menu: Optional — show this type in the portal menu.
            fields: Optional list of field definitions to create along with
                the type, each a dict with keys: name (required), order
                (required int), kind (required string), required (bool),
                hint, default_value, tag_type, decimals, expiration,
                use_for_title (bool), show_in_list (bool).
            type: JSON:API resource type string. Default "flexible-asset-types".
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        attributes = {
            "name": name,
            "description": description,
            "icon": icon,
            "show-in-menu": show_in_menu,
        }
        data: dict = {"type": type, "attributes": {k: v for k, v in attributes.items() if v is not None}}
        if fields:
            data["relationships"] = {
                "flexible-asset-fields": {
                    "data": [
                        {
                            "type": "flexible-asset-fields",
                            "attributes": _field_attributes(f),
                        }
                        for f in fields
                    ]
                }
            }
        try:
            result = await client.post("/compatibility/flexible_asset_types", json_body={"data": data})
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_get_flexible_asset_type(id: int, include: str | None = None) -> str:
        """Get a single flexible asset type by ID.

        API: GET /compatibility/flexible_asset_types/{id}

        Args:
            id: Required flexible asset type ID.
            include: Optional related-resource include list.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.get(
                f"/compatibility/flexible_asset_types/{id}", params={"include": include} if include else None
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_update_flexible_asset_type(
        id: int,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        show_in_menu: bool | None = None,
        fields: list[dict] | None = None,
        type: str = "flexible-asset-types",
    ) -> str:
        """Update a flexible asset type.

        API: PATCH /compatibility/flexible_asset_types/{id}

        Args:
            id: Required flexible asset type ID to update.
            name: Required — the spec requires name even on update.
            description: Optional description.
            icon: Optional icon identifier.
            show_in_menu: Optional — show this type in the portal menu.
            fields: Optional list of field definitions (same shape as in
                cloudradial_create_flexible_asset_type) to replace/add.
            type: JSON:API resource type string. Default "flexible-asset-types".
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        attributes: dict = {
            "name": name,
            "description": description,
            "icon": icon,
            "show-in-menu": show_in_menu,
        }
        attributes = {k: v for k, v in attributes.items() if v is not None}
        if fields:
            attributes["fields"] = [_field_attributes(f) for f in fields]
        body = {"data": {"id": id, "type": type, "attributes": attributes}}
        try:
            result = await client.patch(f"/compatibility/flexible_asset_types/{id}", json_body=body)
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_delete_flexible_asset_type(id: int) -> str:
        """Delete a flexible asset type.

        API: DELETE /compatibility/flexible_asset_types/{id}

        Args:
            id: Required flexible asset type ID to delete.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.delete(f"/compatibility/flexible_asset_types/{id}")
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_get_flexible_asset_fields(
        type_id: int,
        id: str | None = None,
        page_number: int | None = None,
        page_size: int | None = None,
        include: str | None = None,
        sort: str | None = None,
    ) -> str:
        """List the field definitions for a flexible asset type.

        API: GET /compatibility/flexible_asset_types/{typeId}/relationships/flexible_asset_fields

        Args:
            type_id: Required flexible asset type ID.
            id: Optional field ID filter.
            page_number: Optional page[number].
            page_size: Optional page[size].
            include: Optional related-resource include list.
            sort: Optional sort field.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        params = {"id": id, "page[number]": page_number, "page[size]": page_size, "include": include, "sort": sort}
        try:
            result = await client.get(
                f"/compatibility/flexible_asset_types/{type_id}/relationships/flexible_asset_fields", params=params
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_create_flexible_asset_field(
        type_id: int,
        name: str,
        order: int,
        kind: str,
        required: bool | None = None,
        hint: str | None = None,
        default_value: str | None = None,
        tag_type: str | None = None,
        decimals: str | None = None,
        expiration: str | None = None,
        use_for_title: bool | None = None,
        show_in_list: bool | None = None,
        type: str = "flexible-asset-fields",
    ) -> str:
        """Add a field definition to an existing flexible asset type.

        API: POST /compatibility/flexible_asset_types/{typeId}/relationships/flexible_asset_fields

        Args:
            type_id: Required flexible asset type ID to add the field to.
            name: Required field name.
            order: Required display order (integer).
            kind: Required field kind (e.g. "Text", "Checkbox", "Tag" — see
                CloudRadial's flexible asset field kind list).
            required: Optional — whether this field is required when creating assets.
            hint: Optional help text shown under the field.
            default_value: Optional default value.
            tag_type: Optional tag type (when kind is a tag field).
            decimals: Optional decimal precision (when kind is numeric).
            expiration: Optional expiration behavior (when kind is a date field).
            use_for_title: Optional — use this field's value as the asset's title.
            show_in_list: Optional — show this field in list views.
            type: JSON:API resource type string. Default "flexible-asset-fields".
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        field = {
            "name": name,
            "order": order,
            "kind": kind,
            "required": required,
            "hint": hint,
            "default_value": default_value,
            "tag_type": tag_type,
            "decimals": decimals,
            "expiration": expiration,
            "use_for_title": use_for_title,
            "show_in_list": show_in_list,
        }
        body = {"data": {"type": type, "attributes": _field_attributes(field)}}
        try:
            result = await client.post(
                f"/compatibility/flexible_asset_types/{type_id}/relationships/flexible_asset_fields", json_body=body
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_get_flexible_asset_field(type_id: int, field_id: int) -> str:
        """Get a single field definition of a flexible asset type.

        API: GET /compatibility/flexible_asset_types/{typeId}/relationships/flexible_asset_fields/{fieldId}

        Args:
            type_id: Required flexible asset type ID.
            field_id: Required field ID.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.get(
                f"/compatibility/flexible_asset_types/{type_id}/relationships/flexible_asset_fields/{field_id}"
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"


def _field_attributes(f: dict) -> dict:
    """Map a caller-supplied field dict (snake_case) to the kebab-case attribute keys the API expects."""
    mapping = {
        "name": "name",
        "order": "order",
        "kind": "kind",
        "required": "required",
        "hint": "hint",
        "default_value": "default-value",
        "tag_type": "tag-type",
        "decimals": "decimals",
        "expiration": "expiration",
        "use_for_title": "use-for-title",
        "show_in_list": "show-in-list",
    }
    return {mapping.get(k, k): v for k, v in f.items() if v is not None}
