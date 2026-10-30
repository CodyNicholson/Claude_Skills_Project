---
name: api-design
description: REST API design conventions and OpenAPI 3 contract authoring - resource naming, versioning, status codes, error format, pagination, filtering, idempotency, and auth. Use when designing, adding, changing, or reviewing any HTTP endpoint or openapi.yaml.
---

# API design

The OpenAPI file is the source of truth. Design it first, then implement against it. Start new specs from `templates/openapi.yaml`.

## Conventions

TODO(team): adjust any of these defaults to match your existing APIs. Consistency with what already exists beats these defaults.

**Resources and paths**
- Plural nouns, kebab-case: `/api/v1/purchase-orders/{orderId}/line-items`
- Max two levels of nesting. Beyond that, promote to a top-level resource with a filter.
- Actions that are not CRUD use a sub-resource verb: `POST /orders/{id}/cancel`.

**Versioning**
- Major version in the path: `/api/v1/...`. Additive changes (new optional fields, new endpoints) do not bump the version.
- Breaking changes (removing/renaming fields, changing types, tightening validation) require a new version or a deprecation plan written in the spec.

**Fields**
- JSON in camelCase. Timestamps ISO-8601 UTC (`2026-10-30T15:00:00Z`). Money as `{ "amount": "12.34", "currency": "USD" }` (string decimal).
- IDs are opaque strings (UUIDs). Never expose database sequence IDs.
- Enums in UPPER_SNAKE_CASE, and clients must tolerate unknown values.

**Status codes**
| Case | Code |
|---|---|
| Read OK | 200 |
| Created | 201 + `Location` header |
| Accepted for async processing | 202 |
| No body (delete, some updates) | 204 |
| Validation failed | 400 |
| Not authenticated | 401 |
| Not allowed | 403 |
| Not found | 404 |
| Conflict / version mismatch | 409 |
| Business rule violated | 422 |
| Rate limited | 429 |

**Errors** - RFC 9457 Problem Details (`application/problem+json`):
```json
{
  "type": "https://errors.example.com/validation",
  "title": "Validation failed",
  "status": 400,
  "detail": "quantity must be greater than 0",
  "instance": "/api/v1/orders",
  "errors": [{ "field": "quantity", "message": "must be greater than 0" }],
  "traceId": "4bf92f3577b34da6"
}
```
Never leak stack traces, SQL, or internal class names.

**Pagination** - cursor-based for anything that can grow:
`GET /orders?limit=50&cursor=<opaque>` -> `{ "items": [...], "nextCursor": "..." | null }`.
Default limit 20, max 100.

**Filtering and sorting** - `?status=OPEN&createdAfter=...&sort=-createdAt`.

**Idempotency** - `POST` endpoints that create money-moving or externally visible side effects accept an `Idempotency-Key` header.

**Concurrency** - updates to contended resources use `ETag` + `If-Match`, returning 412 on mismatch (or a `version` field + 409).

**Auth**
TODO(team): describe the auth scheme (OAuth2/OIDC bearer, scopes/roles) and how authorization is expressed per endpoint.

## Checklist for every endpoint

- [ ] Path, method, and status codes follow the tables above
- [ ] Request and response schemas fully defined (`required`, formats, examples)
- [ ] All error responses documented, referencing the shared Problem schema
- [ ] Pagination on list endpoints
- [ ] Auth requirement declared
- [ ] Breaking-change check done
