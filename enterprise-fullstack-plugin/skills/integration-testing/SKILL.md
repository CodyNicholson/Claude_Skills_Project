---
name: integration-testing
description: Integration, contract, and end-to-end testing conventions - Testcontainers for Postgres/Kafka/Redis/Elasticsearch, Spring Boot integration tests, API contract tests against OpenAPI, async assertions, test data management, and Playwright UI flows. Use when writing or fixing any test that crosses a process or service boundary.
---

# Integration testing

## Test pyramid in this codebase

| Level | Tool | Scope |
|---|---|---|
| Unit | JUnit 5 / Vitest / pytest | single class or function, no I/O |
| Slice | `@WebMvcTest`, `@DataJpaTest` | one layer with real framework wiring |
| Integration | `@SpringBootTest` + Testcontainers | whole service with real Postgres/Kafka/Redis/ES |
| Contract | OpenAPI validation | responses match `openapi.yaml` |
| E2E | Playwright | critical user journeys through the UI |

TODO(team): Gradle task / Maven profile names for integration tests (e.g. `./gradlew integrationTest`), and where Playwright tests live.

## Testcontainers (Java)

- Use Spring Boot's `@ServiceConnection` on container fields so connection properties are wired automatically.
- Share containers across test classes (static containers in a base class or a `@TestConfiguration`) to keep suites fast. Reuse via `testcontainers.reuse.enable=true` locally only.
- Same major versions as production (`postgres:16`, `apache/kafka:3.8`, etc.).
- Flyway runs on startup against the container: this also tests the migrations.

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Testcontainers
abstract class IntegrationTestBase {
  @Container @ServiceConnection
  static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16.4");
  @Container @ServiceConnection
  static KafkaContainer kafka = new KafkaContainer("apache/kafka:3.8.0");
  @Container @ServiceConnection(name = "redis")
  static GenericContainer<?> redis = new GenericContainer<>("redis:7.4").withExposedPorts(6379);
}
```

## Async assertions

- Use Awaitility for anything event-driven: `await().atMost(Duration.ofSeconds(10)).untilAsserted(() -> ...)`.
- Never `Thread.sleep`.

## What every event-driven feature must test

1. Happy path: produce event -> side effect observed.
2. Duplicate delivery: same event twice -> side effect once.
3. Poison message -> lands in `<topic>.dlt`, consumer keeps running.
4. Downstream failure (DB unavailable or timeout) -> retried, then recovered or DLT.

## Contract tests

- Validate real HTTP responses against `openapi.yaml` (e.g. `swagger-request-validator` / Atlassian `openapi4j`-style validators in Java, or `jest-openapi` / Schemathesis). TODO(team): choose one.
- Cover every documented status code at least once, including error shapes.

## Test data

- Each test creates what it needs (builders/factories) and does not rely on other tests' data.
- Clean up with truncation between tests or unique IDs per test. Do not depend on execution order.

## Playwright E2E

- Only critical journeys (login, core create/read flows). Keep the suite small and stable.
- Select by role/label (`getByRole`), not CSS.
- Run against the compose stack with seeded data.

## Python pipelines

- `pytest` + `testcontainers-python` for Postgres/Kafka. Run the job twice and assert the target is unchanged (idempotency).

## Checklist

- [ ] Real dependencies via Testcontainers, no mocked DB/broker in integration tests
- [ ] Event features have duplicate + poison-message tests
- [ ] Contract validated against openapi.yaml
- [ ] No sleeps; deterministic; independent tests
