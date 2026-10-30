---
name: search-indexing
description: Elasticsearch conventions - index naming with aliases, explicit mappings, analyzers, keeping the index in sync with Postgres via Kafka/outbox, zero-downtime reindexing, and query patterns. Use when creating or changing indexes, mappings, sync pipelines, or search queries.
---

# Elasticsearch search indexing

TODO(team): confirm Elasticsearch (vs OpenSearch) and version, and the Java client in use.

## Indexes and aliases

- Physical index: `<entity>-v<n>` (e.g. `products-v3`). Applications only ever read/write through an **alias** (`products`).
- Mappings and settings live in the repo as JSON (e.g. `search/indexes/products-v3.json`), never created implicitly.
- `dynamic: strict` on mappings so unexpected fields fail loudly instead of polluting the mapping.

## Mapping guidance

- Full-text fields: `text` with a sub-field `keyword` for sorting/aggregations when needed.
- IDs, enums, codes: `keyword`.
- Dates: `date`. Money/quantities: `scaled_float` or `long` in minor units.
- Only index fields you search, filter, sort, or display in results. Postgres stays the source of truth.

## Keeping it in sync

- Source of truth is Postgres. The index is a projection.
- Sync via events (outbox -> Kafka -> indexer consumer) or CDC. Not by dual-writing from request handlers.
- The indexer is idempotent: index by document ID = entity ID, and use external versioning (`version_type=external` with the entity's version/updated_at) so out-of-order events cannot overwrite newer data.
- Deletes are events too.

## Zero-downtime reindex

1. Create `<entity>-v<n+1>` with the new mapping.
2. Backfill from Postgres in batches (data-engineer), while the live indexer dual-writes to both versions (or replays from Kafka offsets after backfill).
3. Verify document counts and spot-check queries.
4. Atomically swap the alias (`_aliases` with remove + add in one request).
5. Delete the old index after a safety window.

## Queries

- Use `bool` with `filter` for exact matches (cacheable, no scoring) and `must`/`should` for relevance.
- Paginate with `search_after` + a tiebreaker sort on ID for deep pages. Avoid `from` beyond ~10k.
- Never build query JSON by string concatenation from user input.

## Checklist

- [ ] Mapping file in repo, `dynamic: strict`
- [ ] App uses the alias, not the physical index
- [ ] Indexer idempotent with external versioning
- [ ] Reindex plan documented if the mapping changed
- [ ] Integration test with Testcontainers Elasticsearch
