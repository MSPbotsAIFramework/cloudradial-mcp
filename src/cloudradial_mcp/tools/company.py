from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS, paging_params

_MAX_TAKE = 200


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def cloudradial_get_companies(
        skip: Annotated[int | None, Field(description="Records to skip (pagination offset). Default 0.")] = None,
        take: Annotated[int | None, Field(description="Records to return (default 10, max 200).")] = None,
        order: Annotated[str | None, Field(description="Field name to sort by.")] = None,
        direction: Annotated[str | None, Field(description='Sort direction: "a" (ascending) or "d" (descending).')] = None,
        filter_field: Annotated[str | None, Field(description='Field name to filter on (e.g. "name").')] = None,
        condition: Annotated[str | None, Field(description='Filter condition: "eq" or "contains".')] = None,
        value: Annotated[str | None, Field(description="Value to test the filter against.")] = None,
    ) -> str:
        """List companies (client organizations) in the CloudRadial portal.

        Use this to find a company_id before scoping articles, feedback,
        or tokens to a specific client.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        if take is not None:
            take = min(take, _MAX_TAKE)
        try:
            result = await client.get(
                "/api/beta/company",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()
