from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:

    @mcp.tool()
    async def cloudradial_get_odata_metadata() -> str:
        """Get the OData $metadata document describing the CloudRadial OData v2 model.

        API: GET /v2/odata/$metadata
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.get("/v2/odata/$metadata")
            return str(result)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_query_odata(raw_query: str | None = None) -> str:
        """Query the CloudRadial OData v2 endpoint.

        API: GET /v2/odata

        The endpoint does not declare typed parameters in its spec — it
        follows standard OData v4 query conventions. Pass an OData query
        string (without the leading "?") to filter/select/page results.

        Args:
            raw_query: Optional raw OData query string, e.g.
                "$filter=name eq 'Acme'&$select=id,name&$top=10&$skip=0".
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        path = "/v2/odata"
        if raw_query:
            path = f"{path}?{raw_query}"
        try:
            result = await client.get(path)
            return str(result)
        except CloudRadialError as e:
            return f"Error: {e}"
