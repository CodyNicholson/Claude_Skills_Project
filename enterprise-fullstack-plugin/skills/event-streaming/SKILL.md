---
name: event-streaming
description: Kafka conventions - topic naming, partitioning keys, event schemas and versioning, producer settings, idempotent consumers, retries, dead-letter topics, and the transactional outbox pattern. Use when designing events, adding topics, or writing Kafka producers or consumers (Spring Kafka or Python).
---

# Kafka event streaming

## Topics

- Name: `<domain>.<entity>.<event-type>.v<major>` e.g. `orders.order.created.v1`. TODO(team): match your existing naming if different.
- One event type per topic unless ordering across types is required (then one topic per entity with a `type` field).
- Partitions: start at 6-12 unless you know otherwise; key determines ordering.
- Retention and compaction are explicit decisions in the spec (`events.md`). Compacted topics need a non-null key and tombstones for deletes.
- Topics are created by IaC/config, not auto-created by clients.

## Keys and ordering

- Key = the aggregate ID whose events must stay ordered (e.g. `orderId`). Events for the same key go to the same partition.
- Never use a random key if consumers care about order.

## Event schema

Every event has an envelope:

```json
{
  "eventId": "uuid",
  "eventType": "OrderCreated",
  "eventVersion": 1,
  "occurredAt": "2026-10-30T15:00:00Z",
  "producer": "order-service",
  "traceId": "...",
  "data": { "orderId": "...", "...": "..." }
}
```

- Schemas live in a registry or in the repo. TODO(team): Schema Registry with Avro/JSON Schema/Protobuf, or JSON + schemas in repo?
- Compatibility: only add optional fields within a major version. Removing or renaming fields means a new `.v<major+1>` topic and a migration period with dual publishing.
- Events state facts in past tense (`OrderShipped`), not commands.

## Producing

- `acks=all`, `enable.idempotence=true`.
- **Do not** write to the database and publish to Kafka as two independent steps. Use the **transactional outbox**: write the event to an `outbox` table in the same DB transaction, and publish from the outbox (poller or CDC such as Debezium). TODO(team): which outbox mechanism do you use?

## Consuming

- **Idempotent by design.** Delivery is at-least-once. Track processed `eventId`s (a `processed_events` table with a unique constraint, inserted in the same transaction as the side effect) or make the operation naturally idempotent (upsert by key + version check).
- Commit offsets only after processing succeeds.
- Retries: bounded retries with backoff for transient errors (Spring Kafka `DefaultErrorHandler` + `ExponentialBackOff`), then send to a **dead-letter topic** `<topic>.dlt` with the error and original headers.
- Non-retryable errors (deserialization, validation) go straight to the DLT.
- Consumer group id: `<service>.<purpose>`.
- Handle unknown fields and unknown enum values gracefully.

## Testing

- Integration tests with Testcontainers Kafka: produce -> assert side effect, duplicate delivery -> side effect happens once, poison message -> lands in DLT.

## Checklist

- [ ] Topic, key, schema, retention documented in `events.md`
- [ ] Outbox used for DB + event writes
- [ ] Consumer idempotent; duplicate-delivery test exists
- [ ] Retry + DLT configured; poison-message test exists
- [ ] Schema change is backward compatible or versioned
