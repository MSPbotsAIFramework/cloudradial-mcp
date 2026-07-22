import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import CloudRadialClient, CloudRadialError
from ._common import NO_CREDS, paging_params


def register(mcp: FastMCP, client_factory: Callable[[], CloudRadialClient | None]) -> None:

    @mcp.tool()
    async def cloudradial_get_articles(
        skip: int | None = None,
        take: int | None = None,
        order: str | None = None,
        direction: str | None = None,
        filter_field: str | None = None,
        condition: str | None = None,
        value: str | None = None,
    ) -> str:
        """List knowledge base articles.

        API: GET /api/beta/article

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
                "/api/beta/article",
                params=paging_params(skip, take, order, direction, filter_field, condition, value),
            )
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_create_article(
        subject: str,
        body: str,
        category: str,
        company_id: int,
        groups: str,
        article_source: int | None = None,
        author: str | None = None,
        date: str | None = None,
        external_article_id: str | None = None,
        is_front_page: bool | None = None,
        is_new_window: bool | None = None,
        is_pinned: bool | None = None,
        permalink_key: str | None = None,
        tags: str | None = None,
        url: str | None = None,
        id: int | None = None,
    ) -> str:
        """Create (or, with id set, upsert) a knowledge base article.

        API: POST /api/beta/article

        Args:
            subject: Required article title.
            body: Required article HTML/text body.
            category: Required category name.
            company_id: Required company ID this article belongs to.
            groups: Required comma-separated list of user/company groups with access.
            article_source: Optional source enum (0-3).
            author: Optional author name.
            date: Optional publish date (ISO 8601).
            external_article_id: Optional external system ID for this article.
            is_front_page: Optional — show on the portal front page.
            is_new_window: Optional — open links in a new window.
            is_pinned: Optional — pin to the top of listings.
            permalink_key: Optional permalink slug.
            tags: Optional comma-separated tags.
            url: Optional external URL instead of a body.
            id: Optional — set to update an existing article instead of creating one.
        """
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
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def cloudradial_delete_article(company_id: int, id: int) -> str:
        """Delete a knowledge base article.

        API: DELETE /api/beta/article

        Args:
            company_id: Required company ID the article belongs to.
            id: Required article ID to delete.
        """
        client = client_factory()
        if client is None:
            return NO_CREDS
        try:
            result = await client.delete("/api/beta/article", json_body={"companyId": company_id, "id": id})
            return json.dumps(result, indent=2)
        except CloudRadialError as e:
            return f"Error: {e}"
