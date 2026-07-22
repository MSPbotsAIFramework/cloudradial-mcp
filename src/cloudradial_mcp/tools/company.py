import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS, paging_params


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:

    @mcp.tool()
    async def cloudradial_get_companies(
        skip: int | None = None,
        take: int | None = None,
        order: str | None = None,
        direction: str | None = None,
        filter_field: str | None = None,
        condition: str | None = None,
        value: str | None = None,
    ) -> str:
        """List companies (client organizations) in the CloudRadial portal.

        API: GET /api/beta/company

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
                "/api/beta/company",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"
