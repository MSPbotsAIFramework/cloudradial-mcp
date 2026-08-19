"""tools/list snapshot + error-envelope mapping tests.

No network calls: tool enumeration goes through FastMCP's in-process
list_tools(), and the error-code mapping is tested directly against
CloudRadialError, independent of any real HTTP request.
"""

import pytest

from cloudradial_mcp.api_client import CloudRadialError
from cloudradial_mcp.config import Settings
from cloudradial_mcp.server import create_mcp_server

EXPECTED_TOOLS = {
    "cloudradial_get_companies": set(),
    "cloudradial_get_articles": set(),
    "cloudradial_create_article": {"subject", "body", "category", "company_id", "groups"},
    "cloudradial_delete_article": {"company_id", "id"},
    "cloudradial_get_feedback": set(),
    "cloudradial_create_feedback": {"feedback"},
    "cloudradial_delete_feedback": {"id"},
    "cloudradial_get_tokens": set(),
    "cloudradial_set_token": set(),
    "cloudradial_delete_token": set(),
    "cloudradial_get_archives": set(),
    "cloudradial_create_archive": {"archive"},
    "cloudradial_delete_archive": {"archive_id"},
    "cloudradial_get_archive_items": {"archive_id"},
    "cloudradial_create_archive_item": {"archive_id", "item"},
    "cloudradial_delete_archive_item": {"archive_id", "item_id"},
}

# Tool names annotated readOnlyHint=True (list/get tools).
READ_ONLY_TOOLS = {
    "cloudradial_get_companies",
    "cloudradial_get_articles",
    "cloudradial_get_feedback",
    "cloudradial_get_tokens",
    "cloudradial_get_archives",
    "cloudradial_get_archive_items",
}

# Tool names annotated destructiveHint=True (irreversible deletes, gated by confirm).
DESTRUCTIVE_TOOLS = {
    "cloudradial_delete_article",
    "cloudradial_delete_feedback",
    "cloudradial_delete_token",
    "cloudradial_delete_archive",
    "cloudradial_delete_archive_item",
}


@pytest.mark.asyncio
async def test_tools_list_snapshot():
    mcp = create_mcp_server(Settings())
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == set(EXPECTED_TOOLS), f"unexpected tool set: {names}"

    by_name = {t.name: t for t in tools}
    for name, expected_required in EXPECTED_TOOLS.items():
        tool = by_name[name]
        required = set(tool.inputSchema.get("required", []))
        assert required == expected_required, f"{name}: required={required}"
        assert len(tool.description or "") <= 500, f"{name}: description too long"
        assert "API:" not in (tool.description or ""), f"{name}: description leaks implementation detail"
        first_line = (tool.description or "").strip().splitlines()[0]
        assert len(first_line) <= 100, f"{name}: first line too long: {first_line!r}"

        if name in READ_ONLY_TOOLS:
            assert tool.annotations is not None and tool.annotations.readOnlyHint is True
        if name in DESTRUCTIVE_TOOLS:
            assert tool.annotations is not None and tool.annotations.destructiveHint is True
            assert "confirm" in tool.inputSchema.get("properties", {}), f"{name}: missing confirm gate"


@pytest.mark.asyncio
async def test_service_instructions_present_and_bounded():
    mcp = create_mcp_server(Settings())
    assert mcp.instructions
    assert len(mcp.instructions) <= 1500


@pytest.mark.parametrize(
    "status_code,expected_code,expected_retryable",
    [
        (0, "upstream_error", True),
        (400, "invalid_argument", False),
        (401, "unauthorized", False),
        (403, "unauthorized", False),
        (404, "not_found", False),
        (422, "invalid_argument", False),
        (429, "rate_limited", True),
        (500, "upstream_error", True),
        (503, "upstream_error", True),
    ],
)
def test_error_envelope_mapping(status_code, expected_code, expected_retryable):
    import json

    err = CloudRadialError(status_code, "boom")
    envelope = json.loads(err.to_envelope())
    assert envelope["error"]["code"] == expected_code
    assert envelope["error"]["retryable"] is expected_retryable
    assert envelope["error"]["message"] == "boom"


@pytest.mark.asyncio
async def test_destructive_tools_require_confirm_true():
    """Calling a delete tool without confirm=true must short-circuit with an
    invalid_argument envelope, never reaching the API client."""
    import json

    from cloudradial_mcp.tools import archive, article, feedback, token
    from mcp.server.fastmcp import FastMCP

    def _client_factory():
        raise AssertionError("client_factory should not be called when confirm is missing")

    mcp = FastMCP(name="test")
    article.register(mcp, _client_factory)
    feedback.register(mcp, _client_factory)
    token.register(mcp, _client_factory)
    archive.register(mcp, _client_factory)

    calls = [
        ("cloudradial_delete_article", {"company_id": 1, "id": 2}),
        ("cloudradial_delete_feedback", {"id": 1}),
        ("cloudradial_delete_token", {}),
        ("cloudradial_delete_archive", {"archive_id": 1}),
        ("cloudradial_delete_archive_item", {"archive_id": 1, "item_id": 2}),
    ]
    for name, args in calls:
        result = await mcp.call_tool(name, args)
        # call_tool returns (content_blocks, structured_result); the tool's
        # return string is both the first block's .text and structured
        # result's "result" key. Extract via the content block.
        content_blocks = result[0] if isinstance(result, tuple) else result
        text = content_blocks[0].text
        envelope = json.loads(text)
        assert envelope["error"]["code"] == "invalid_argument", f"{name}: {envelope}"
        assert envelope["error"]["retryable"] is False
