import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import CloudRadialClient
from .config import Settings

# Per-request credential isolation via contextvars.
# GatewayCredsMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
_gateway_creds_var: contextvars.ContextVar[tuple[str, str] | None] = contextvars.ContextVar(
    "cloudradial_gateway_creds", default=None
)


def get_client_from_context(settings: Settings) -> CloudRadialClient | None:
    """Resolve the active CloudRadialClient for the current request context."""
    creds = _gateway_creds_var.get()
    if not creds:
        return None
    public_key, private_key = creds
    return CloudRadialClient(public_key, private_key, settings.cloudradial_base_url)


class GatewayCredsMiddleware:
    """ASGI middleware.

    Reads X-CloudRadial-Public-Key and X-CloudRadial-Private-Key (both
    required) from request headers and stores them in the contextvar. Header
    names mirror the "Public Key" / "Private Key" fields used by the existing
    CloudRadial integration on app.mspbots.ai. Returns 401 if either header is
    missing on /mcp requests.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        public_key = request.headers.get("x-cloudradial-public-key")
        private_key = request.headers.get("x-cloudradial-private-key")
        if not public_key or not private_key:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": (
                        "This server requires the X-CloudRadial-Public-Key and "
                        "X-CloudRadial-Private-Key headers containing a valid "
                        "CloudRadial API key pair"
                    ),
                    "required_headers": ["X-CloudRadial-Public-Key", "X-CloudRadial-Private-Key"],
                    "optional_headers": [],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        ctx_token = _gateway_creds_var.set((public_key, private_key))
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_creds_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all CloudRadial tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="cloudradial-mcp",
        instructions=(
            "CloudRadial is a client portal / service catalog platform MSPs give "
            "their end customers — knowledge base articles, CSAT/feedback "
            "collection, report archives, and portal merge-field tokens, "
            "organized per company (client organization). Use this server for: "
            "looking up client organizations (cloudradial_get_companies); "
            "reading or publishing knowledge base content "
            "(cloudradial_get_articles / cloudradial_create_article / "
            "cloudradial_delete_article); reviewing customer satisfaction "
            "records (cloudradial_get_feedback / cloudradial_create_feedback / "
            "cloudradial_delete_feedback); managing report archives that "
            "customers or automations upload recurring reports into "
            "(cloudradial_get_archives / cloudradial_create_archive / "
            "cloudradial_delete_archive and the matching "
            "cloudradial_get_archive_items / cloudradial_create_archive_item / "
            "cloudradial_delete_archive_item for items inside an archive); and "
            "managing @-prefixed portal merge-field tokens used inside "
            "articles/automations/messages (cloudradial_get_tokens / "
            "cloudradial_set_token / cloudradial_delete_token — unrelated to "
            "authentication despite the name). Typical flow: "
            "cloudradial_get_companies to find a company_id, then scope "
            "articles/feedback/tokens to it. All delete tools are destructive "
            "and require confirm=true."
        ),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    client_factory: Callable[[], CloudRadialClient | None] = lambda: get_client_from_context(settings)

    from .tools import archive, article, company, feedback, token

    company.register(mcp, client_factory)
    article.register(mcp, client_factory)
    feedback.register(mcp, client_factory)
    token.register(mcp, client_factory)
    archive.register(mcp, client_factory)

    return mcp
