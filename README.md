# cloudradial-mcp

**CloudRadial** MCP server — exposes the CloudRadial REST API (client portal / PSA-adjacent MSP platform) as MCP tools.

> **Naming note:** app.mspbots.ai calls this integration **"CloudRadial"** (`sys_integration.subject_code = CLOUDRADIAL`). The vendor's public API is documented at [developers.cloudradial.com](https://developers.cloudradial.com/docs/getting-started) and its Swagger UI at `https://api.us.cloudradial.com/swagger`.

<div align="center">

## MSPbots Connector

**The MCP Gateway built for MSPs: visible, controlled, and your data stays where it belongs.**

[**Get started at connect.mspbots.ai →**](https://connect.mspbots.ai)

</div>

---

MSPbots Connector gives your AI clients one MCP URL to reach your entire MSP stack (RMM, PSA, documentation, security, finance), and gives you control over who can call which tool and a record of everything that was called.

**Hosted service: [connect.mspbots.ai](https://connect.mspbots.ai)** · Free to use.

### Why Connector

![MSPbots Connector](https://stgoss.mspbots.ai/files/mcp/mspbots-mcp.png)

| | |
|---|---|
| **Visible** | Every tool call is logged: who, which vendor, when. Usage dashboard, CSV export, SIEM streaming. |
| **Controlled** | Role-based, per-tool allowlist. Deny by default. |
| **Protected** | Credentials encrypted per record. AI clients never see your vendor passwords or tokens. |
| **MSP-native** | Built for the MSP stack only: RMM, PSA, documentation, security, finance. |

### Quick start

1. **Sign up** at [connect.mspbots.ai](https://connect.mspbots.ai).
2. **Connect your vendors.** Pick from 150+ connectors and authorize each one on the vendor's own page, or bring your own API keys. No extra vendor accounts needed.
3. **Set access.** Create roles and decide which tools each role may call. Nothing is allowed until you allow it.
4. **Add your MCP URL to your AI client.** Copy the URL from your Connector dashboard into Claude, ChatGPT, Cursor, VS Code, Gemini, Codex, or any MCP-capable client.
5. **Ask your AI to do real work**, and watch every call appear in the audit log.

### Features

**Unified gateway**
- One MCP URL for all your AI clients
- 150+ connectors across the MSP stack
- Custom MCP servers supported, free
- Authorization happens on each vendor's own page; the AI never sees passwords or tokens
- Bring your own credentials: use the vendor API keys you already have
- Multiple accounts per app; connect once, reuse across AI clients
- Tool search: finds the right action for the task
- One sign-in; vendor credentials are injected behind the scenes and OAuth tokens refresh automatically

**Visibility**
- Audit log for every tool call (who, which vendor, when)
- Usage dashboard: call volume, top vendors, error rate, per-user activity
- Export audit logs to CSV, or stream to Loki, Graylog, or LogScale (SIEM)
- Optional recording of tool arguments and result summaries (off by default, enabled per organization)

**Control**
- Per-role, per-tool allowlist, deny by default
- owner / admin / member roles
- SCIM provisioning with Entra ID, Okta, JumpCloud, and Google Workspace

**Security**
- Credentials encrypted one record at a time (AES-256-GCM, per-record key)
- AI clients authenticate with OAuth 2.1 + PKCE
- Vendor responses are scanned for prompt-injection patterns and returned as structured data. This is one layer of defense, not a guarantee against every attack.
- Static egress IP for customer firewall and API allowlisting

### Pricing

**Free.**

Links: [connect.mspbots.ai](https://connect.mspbots.ai) · [mspbots.ai](https://mspbots.ai)

---

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io/) (Streamable HTTP/SSE transport) and wraps **16 tools** across 5 resource groups (Company, Article, Feedback, Token, Archive/ArchiveItem), trimmed down on 2026-08-04 from an original 34-operation full-API build (which additionally covered FlexibleAsset, FlexibleAssetType, and the OData v2 metadata endpoint). MSPbots' own stored integration config for this vendor calls exactly those 5 kept resource groups (confirmed via `web/int/sys/integration/api/list` against integration id `1579382881663623169`: Company, Article, Feedback, Token, Archive, Archive Item) — all 16 tools in those groups were already tight core CRUD (`get`/`create`/`delete`, no bloat), so no per-tool trimming was needed within them; `FlexibleAsset`, `FlexibleAssetType`, and OData (18 tools total) were removed entirely as unused by MSPbots. If a removed group is needed later, the vendor's OpenAPI spec (linked below) still documents its exact operations and they can be re-added the same way the kept tools were generated. It follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication.

The underlying API authenticates via **HTTP Basic Auth**: the Public Key is the username and the Private Key is the password (both generated under *Partner > Settings > Integrations > API* in the CloudRadial portal). This matches how the existing CloudRadial integration on app.mspbots.ai is configured (`authType: 0`, custom Key/Secret credential fields) — this server receives both values per request via headers and never persists them.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

The server starts on `http://localhost:8080`.

### Local (uv)

```bash
uv sync
python -m cloudradial_mcp
```

## Health Check

```bash
curl http://localhost:8080/health
# {"status": "ok", "service": "cloudradial-mcp", "transport": "http"}
```

No credentials are required for the health endpoint.

## Authentication parameters (Authentication)

Every request to `/mcp` must include the following HTTP headers:

| Header | Type | Required | Default | Allowed values | Description | Example |
|---|---|---|---|---|---|---|
| `X-CloudRadial-Public-Key` | string | Yes | None | None (free text) | Username part of HTTP Basic Auth; corresponds to the Public Key generated on the CloudRadial portal's Partner > Settings > Integrations > API page. | `X-CloudRadial-Public-Key: 11111111-1111-1111-1111-111111111111` |
| `X-CloudRadial-Private-Key` | string | Yes | None | None (free text) | Password part of HTTP Basic Auth; corresponds to the Private Key generated on the same page. This value is shown only once at creation, so keep it safe. | `X-CloudRadial-Private-Key: 22222222-2222-2222-2222-222222222222` |

Missing either header returns `401 Unauthorized`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_PORT` | `8080` | Listening port |
| `MCP_HTTP_HOST` | `0.0.0.0` | Listening host |
| `CLOUDRADIAL_BASE_URL` | `https://api.us.cloudradial.com` | CloudRadial API base URL |

## MCP Endpoint

```
POST http://localhost:8080/mcp
```

Connect your MCP client with:
- Transport: `http` (Streamable HTTP / SSE)
- Headers: `X-CloudRadial-Public-Key: <public_key>` (required), `X-CloudRadial-Private-Key: <private_key>` (required)

## Tool List

**16 tools**, trimmed down from an original 34-operation full-API build (2026-08-04) — see Overview above for the exact rationale.

### Company (1)

| Tool | Function | Parameters |
|---|---|---|
| `cloudradial_get_companies` | List companies (customer organizations) in the portal | `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |

### Article (3)

| Tool | Function | Parameters |
|---|---|---|
| `cloudradial_get_articles` | List knowledge base articles | `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |
| `cloudradial_create_article` | Create/update a knowledge base article (write operation) | `subject`, `body`, `category`, `company_id`, `groups`, other optional fields, `id?` (if provided, it is an update) |
| `cloudradial_delete_article` | Delete a knowledge base article (write operation) | `company_id`, `id` |

### Feedback (3)

| Tool | Function | Parameters |
|---|---|---|
| `cloudradial_get_feedback` | List CSAT/feedback records | `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |
| `cloudradial_create_feedback` | Submit a feedback/CSAT record (write operation) | `feedback` (dict; see the tool docstring for fields) |
| `cloudradial_delete_feedback` | Delete a feedback record (write operation) | `id` |

### Token (3) — portal merge-field variables, unrelated to authentication

| Tool | Function | Parameters |
|---|---|---|
| `cloudradial_get_tokens` | List portal merge-field tokens (@variables) | `company_id?` |
| `cloudradial_set_token` | Create/update a merge-field token (write operation) | `company_id?`, `token?`, `value?`, `type?` |
| `cloudradial_delete_token` | Delete a merge-field token (write operation) | `company_id?`, `token?`, `value?`, `type?` |

### Archive & Archive Item (6)

| Tool | Function | Parameters |
|---|---|---|
| `cloudradial_get_archives` | List report archive definitions | `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |
| `cloudradial_create_archive` | Create/update an archive definition (write operation) | `archive` (dict; see the tool docstring for fields) |
| `cloudradial_delete_archive` | Delete an archive definition (write operation) | `archive_id` |
| `cloudradial_get_archive_items` | List items (reports) in an archive | `archive_id`, `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |
| `cloudradial_create_archive_item` | Add an item to an archive (write operation; body structure not public, see Known Gaps) | `archive_id`, `item`(dict) |
| `cloudradial_delete_archive_item` | Delete a single item from an archive (write operation) | `archive_id`, `item_id` |


## Test Example

List companies:

```json
{
  "method": "tools/call",
  "params": { "name": "cloudradial_get_companies", "arguments": { "take": 10 } }
}
```

Equivalent `curl` against the running server (streamable HTTP MCP endpoint):

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-CloudRadial-Public-Key: <public_key>" \
  -H "X-CloudRadial-Private-Key: <private_key>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "cloudradial_get_companies", "arguments": { "take": 10 } }
  }'
```

## API Reference

- Getting started: https://developers.cloudradial.com/docs/getting-started
- Swagger UI: https://api.us.cloudradial.com/swagger
- Base URL: `https://api.us.cloudradial.com`

## Known Gaps / Not Yet Verified

- **Trimmed from 34 to 16 tools on 2026-08-04.** The original build covered
  every operation in the official OpenAPI spec. A later scope decision cut
  this back to MSPbots' actually-used 5 resource groups (Company, Article,
  Feedback, Token, Archive/ArchiveItem) — see Overview above for the exact
  rationale. `FlexibleAsset`, `FlexibleAssetType`, and the OData v2
  metadata endpoint (18 tools total) were removed entirely as unused. If a
  removed group is needed later, the vendor's OpenAPI spec (linked below)
  still documents its exact operations and they can be re-added the same
  way the kept tools were generated.
- Not yet tested against a live CloudRadial account — only protocol-level verification (health check, 401 on missing credentials, `tools/list` returning all 16 tools) has been done so far.
- `cloudradial_create_archive_item`'s request body shape is not published in CloudRadial's OpenAPI spec (the schema is empty) — CloudRadial's docs describe archive item uploads via drag-and-drop, an archive-unique email address, or "an API connection" (up to 128MB), but do not document the exact JSON field names. Verify the correct payload shape with CloudRadial support or by inspecting a successful portal-side upload before relying on this tool in production.
- The `Token` API (`cloudradial_get_tokens`/`cloudradial_set_token`/`cloudradial_delete_token`) manages CloudRadial's portal merge-field variables (`@`-prefixed tokens used in Articles/Automations/Messages) — it is unrelated to authentication, despite the name.
