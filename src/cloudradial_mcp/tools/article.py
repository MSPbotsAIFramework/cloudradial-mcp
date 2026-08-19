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
    async def cloudradial_get_articles(
        skip: Annotated[int | None, Field(description="Records to skip (pagination offset). Default 0.")] = None,
        take: Annotated[int | None, Field(description="Records to return (default 10, max 200).")] = None,
        order: Annotated[str | None, Field(description="Field name to sort by.")] = None,
        direction: Annotated[str | None, Field(description='Sort direction: "a" (ascending) or "d" (descending).')] = None,
        filter_field: Annotated[str | None, Field(description="Field name to filter on.")] = None,
        condition: Annotated[str | None, Field(description='Filter condition: "eq" or "contains".')] = None,
        value: Annotated[str | None, Field(description="Value to test the filter against.")] = None,
    ) -> str:
        """List knowledge base articles."""
        client = client_factory()
        if client is None:
            return NO_CREDS
        if take is not None:
            take = min(take, _MAX_TAKE)
        try:
            result = await client.get(
                "/api/beta/article",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool()
    async def cloudradial_create_article(
        subject: Annotated[str, Field(description="Required article title.")],
        body: Annotated[str, Field(description="Required article HTML/text body.")],
        category: Annotated[str, Field(description="Required category name.")],
        company_id: Annotated[int, Field(description="Required company ID this article belongs to.")],
        groups: Annotated[str, Field(description="Required comma-separated list of user/company groups with access.")],
        article_source: Annotated[int | None, Field(description="Optional source enum (0-3).")] = None,
        author: Annotated[str | None, Field(description="Optional author name.")] = None,
        date: Annotated[str | None, Field(description="Optional publish date (ISO 8601).")] = None,
        external_article_id: Annotated[str | None, Field(description="Optional external system ID for this article.")] = None,
        is_front_page: Annotated[bool | None, Field(description="Show on the portal front page.")] = None,
        is_new_window: Annotated[bool | None, Field(description="Open links in a new window.")] = None,
        is_pinned: Annotated[bool | None, Field(description="Pin to the top of listings.")] = None,
        permalink_key: Annotated[str | None, Field(description="Optional permalink slug.")] = None,
        tags: Annotated[str | None, Field(description="Optional comma-separated tags.")] = None,
        url: Annotated[str | None, Field(description="Optional external URL instead of a body.")] = None,
        id: Annotated[int | None, Field(description="Set to update an existing article instead of creating one.")] = None,
    ) -> str:
        """Create (or, with id set, update) a knowledge base article."""
        client = client_factory()
        if client is None:
            return NO_CREDS
        payload = {
            "subject": subject,
            "body": body,
            "category": category,
            "companyId": company_id,
            "groups": groups,
            "articleSource": article_source,
            "author": author,
            "date": date,
            "externalArticleId": external_article_id,
            "isFrontPage": is_front_page,
            "isNewWindow": is_new_window,
            "isPinned": is_pinned,
            "permalinkKey": permalink_key,
            "tags": tags,
            "url": url,
            "id": id,
        }
        try:
            result = await client.post("/api/beta/article", json_body={k: v for k, v in payload.items() if v is not None})
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
    async def cloudradial_delete_article(
        company_id: Annotated[int, Field(description="Required company ID the article belongs to.")],
        id: Annotated[int, Field(description="Required article ID to delete.")],
        confirm: Annotated[bool, Field(description="Required — must be set to true to proceed.")] = False,
    ) -> str:
        """Delete a knowledge base article.

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
            result = await client.delete("/api/beta/article", json_body={"companyId": company_id, "id": id})
            return dump_json_capped(result)
        except CloudRadialError as e:
            return e.to_envelope()
