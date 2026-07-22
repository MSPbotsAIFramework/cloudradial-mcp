# cloudradial-mcp

**CloudRadial** MCP server — exposes the CloudRadial REST API (client portal / PSA-adjacent MSP platform) as MCP tools.

> **Naming note:** app.mspbots.ai calls this integration **"CloudRadial"** (`sys_integration.subject_code = CLOUDRADIAL`). The vendor's public API is documented at [developers.cloudradial.com](https://developers.cloudradial.com/docs/getting-started) and its Swagger UI at `https://api.us.cloudradial.com/swagger`.

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io/) (Streamable HTTP/SSE transport) and wraps every operation in CloudRadial's official OpenAPI 3.0 spec (v1, 34 operations across 8 resource groups: Company, Article, Feedback, Token, Archive/ArchiveItem, FlexibleAsset, FlexibleAssetType, and the OData v2 metadata endpoint). It follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication.

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

## 授权参数说明 (Authentication)

Every request to `/mcp` must include the following HTTP headers:

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-CloudRadial-Public-Key` | string | 必填 | 无 | 无(自由文本) | HTTP Basic Auth 的用户名部分,对应 CloudRadial 门户 Partner > Settings > Integrations > API 页面生成的 Public Key。 | `X-CloudRadial-Public-Key: 11111111-1111-1111-1111-111111111111` |
| `X-CloudRadial-Private-Key` | string | 必填 | 无 | 无(自由文本) | HTTP Basic Auth 的密码部分,对应同一页面生成的 Private Key;该值只在创建时显示一次,需妥善保存。 | `X-CloudRadial-Private-Key: 22222222-2222-2222-2222-222222222222` |

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

**34 tools** — full coverage of every operation in the official CloudRadial OpenAPI spec.

### Company (1)

| Tool | 功能 | 参数 |
|---|---|---|
| `cloudradial_get_companies` | 列出门户中的公司(客户组织) | `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |

### Article (3)

| Tool | 功能 | 参数 |
|---|---|---|
| `cloudradial_get_articles` | 列出知识库文章 | `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |
| `cloudradial_create_article` | 新建/更新知识库文章(写操作) | `subject`, `body`, `category`, `company_id`, `groups`, 其余可选字段, `id?`(传入则为更新) |
| `cloudradial_delete_article` | 删除知识库文章(写操作) | `company_id`, `id` |

### Feedback (3)

| Tool | 功能 | 参数 |
|---|---|---|
| `cloudradial_get_feedback` | 列出 CSAT/反馈记录 | `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |
| `cloudradial_create_feedback` | 提交反馈/CSAT 记录(写操作) | `feedback`(dict,字段见工具 docstring) |
| `cloudradial_delete_feedback` | 删除反馈记录(写操作) | `id` |

### Token (3) — portal 合并字段变量,与鉴权无关

| Tool | 功能 | 参数 |
|---|---|---|
| `cloudradial_get_tokens` | 列出门户合并字段 token(@变量) | `company_id?` |
| `cloudradial_set_token` | 新建/更新合并字段 token(写操作) | `company_id?`, `token?`, `value?`, `type?` |
| `cloudradial_delete_token` | 删除合并字段 token(写操作) | `company_id?`, `token?`, `value?`, `type?` |

### Archive & Archive Item (6)

| Tool | 功能 | 参数 |
|---|---|---|
| `cloudradial_get_archives` | 列出报表归档定义 | `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |
| `cloudradial_create_archive` | 新建/更新归档定义(写操作) | `archive`(dict,字段见工具 docstring) |
| `cloudradial_delete_archive` | 删除归档定义(写操作) | `archive_id` |
| `cloudradial_get_archive_items` | 列出归档内的条目(报表) | `archive_id`, `skip?`, `take?`, `order?`, `direction?`, `filter_field?`, `condition?`, `value?` |
| `cloudradial_create_archive_item` | 向归档添加条目(写操作,body 结构未公开,见 Known Gaps) | `archive_id`, `item`(dict) |
| `cloudradial_delete_archive_item` | 删除归档中的单个条目(写操作) | `archive_id`, `item_id` |

### FlexibleAsset — IT Glue 兼容层 (8)

| Tool | 功能 | 参数 |
|---|---|---|
| `cloudradial_get_flexible_assets` | 按资产类型列出自定义资产记录 | `flexible_asset_type_id`, `organization_id?`, `name?`, `page_number?`, `page_size?`, `include?`, `sort?` |
| `cloudradial_create_flexible_asset` | 新建自定义资产记录(写操作) | `flexible_asset_type_id`, `traits`, `organization_id?`, `archived?`, `type="flexible-assets"` |
| `cloudradial_update_flexible_assets` | 批量更新自定义资产记录(写操作) | `assets`(list,JSON:API 形状,见 docstring) |
| `cloudradial_delete_flexible_assets` | 批量删除自定义资产记录(写操作) | `ids`(list), `type="flexible-assets"` |
| `cloudradial_get_flexible_asset` | 按 ID 查自定义资产记录 | `id`, `include?` |
| `cloudradial_delete_flexible_asset` | 删除单个自定义资产记录(写操作) | `id` |
| `cloudradial_update_flexible_asset` | 更新单个自定义资产记录(写操作) | `id`, `flexible_asset_type_id?`, `archived?`, `traits?`, `organization_id?`, `type="flexible-assets"` |
| `cloudradial_create_organization_flexible_assets` | 在指定公司下批量新建自定义资产(写操作) | `org_id`, `assets`(list) |

### FlexibleAssetType — 自定义资产类型定义 (8)

| Tool | 功能 | 参数 |
|---|---|---|
| `cloudradial_get_flexible_asset_types` | 列出自定义资产类型 | `id?`, `name?`, `icon?`, `enabled?`, `page_number?`, `page_size?`, `include?`, `sort?` |
| `cloudradial_create_flexible_asset_type` | 新建自定义资产类型(可同时创建字段,写操作) | `name`, `description?`, `icon?`, `show_in_menu?`, `fields?`(list) |
| `cloudradial_get_flexible_asset_type` | 按 ID 查自定义资产类型 | `id`, `include?` |
| `cloudradial_update_flexible_asset_type` | 更新自定义资产类型(写操作) | `id`, `name`, `description?`, `icon?`, `show_in_menu?`, `fields?`(list) |
| `cloudradial_delete_flexible_asset_type` | 删除自定义资产类型(写操作) | `id` |
| `cloudradial_get_flexible_asset_fields` | 列出资产类型下的字段定义 | `type_id`, `id?`, `page_number?`, `page_size?`, `include?`, `sort?` |
| `cloudradial_create_flexible_asset_field` | 为资产类型新增字段定义(写操作) | `type_id`, `name`, `order`, `kind`, 其余可选字段 |
| `cloudradial_get_flexible_asset_field` | 按 ID 查单个字段定义 | `type_id`, `field_id` |

### Metadata — OData v2 (2)

| Tool | 功能 | 参数 |
|---|---|---|
| `cloudradial_get_odata_metadata` | 获取 OData $metadata 文档 | 无 |
| `cloudradial_query_odata` | 查询 OData v2 端点 | `raw_query?`(原始 OData 查询字符串,如 `$filter=...&$top=10`) |

## 测试示例 (Test Example)

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

- Not yet tested against a live CloudRadial account — only protocol-level verification (health check, 401 on missing credentials, `tools/list` returning all 34 tools) has been done so far.
- `cloudradial_create_archive_item`'s request body shape is not published in CloudRadial's OpenAPI spec (the schema is empty) — CloudRadial's docs describe archive item uploads via drag-and-drop, an archive-unique email address, or "an API connection" (up to 128MB), but do not document the exact JSON field names. Verify the correct payload shape with CloudRadial support or by inspecting a successful portal-side upload before relying on this tool in production.
- The `Token` API (`cloudradial_get_tokens`/`cloudradial_set_token`/`cloudradial_delete_token`) manages CloudRadial's portal merge-field variables (`@`-prefixed tokens used in Articles/Automations/Messages) — it is unrelated to authentication, despite the name.
- The `FlexibleAsset`/`FlexibleAssetType` tools wrap a JSON:API-shaped, IT Glue-compatible layer (`/compatibility/...`); bulk update/create-under-organization tools accept pre-shaped JSON:API list payloads rather than fully flattened arguments, since the nesting (`data[].attributes.{...}`) doesn't flatten cleanly into named parameters.
- `cloudradial_query_odata` accepts a raw OData query string rather than typed parameters, since the spec does not declare `$filter`/`$select`/etc. as typed Swagger parameters (standard for OData v4 endpoints).
