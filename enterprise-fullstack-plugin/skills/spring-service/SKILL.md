---
name: spring-service
description: Java / Spring Boot service conventions - package layout, controller/service/repository layering, DTO mapping, validation, exception handling to Problem Details, configuration, Redis caching, logging and observability. Use when creating or changing Spring Boot code.
---

# Spring Boot service conventions

TODO(team): set Java and Spring Boot versions and the build tool. Defaults below assume Java 21, Spring Boot 3.x, Gradle.

## Package layout (package-by-feature)

```
com.example.<service>
├── <feature>/                 e.g. orders/
│   ├── OrderController.java   REST layer: HTTP <-> DTOs only
│   ├── OrderService.java      business logic, transactions
│   ├── OrderRepository.java   Spring Data JPA (or JdbcClient)
│   ├── Order.java             entity
│   ├── dto/                   request/response records
│   └── OrderMapper.java       entity <-> DTO
├── common/                    errors, config, security, util
└── Application.java
```

## Layering rules

- Controllers: no business logic, no repositories. Validate with `@Valid` on request records. Return DTOs, never entities.
- Services: own transactions (`@Transactional` on public service methods; `readOnly = true` for reads). Call repositories and other services.
- Repositories: no logic. Prefer derived queries or `@Query` with named parameters. Never concatenate SQL.
- DTOs as Java `record`s. Map explicitly (MapStruct or hand-written). TODO(team): which mapper?
- Constructor injection only (`final` fields, single constructor, no `@Autowired` on fields).

## Errors

- One `@RestControllerAdvice` maps exceptions to RFC 9457 `ProblemDetail` (Spring has built-in support). See the api-design skill for the shape.
- Domain exceptions: `NotFoundException` -> 404, `ConflictException` -> 409, `BusinessRuleException` -> 422. Validation -> 400 with field errors.
- Log 5xx at ERROR with the trace ID. Do not log 4xx at ERROR.

## Configuration

- `application.yml` + profile files (`application-local.yml`). Bind with `@ConfigurationProperties` records, validated with `@Validated`.
- Secrets only via environment variables / secret store, referenced as `${DB_PASSWORD}`.

## Redis caching

- Use Spring Cache abstraction (`@Cacheable`, `@CacheEvict`) for read-through caching of expensive, read-heavy data.
- Every cache has an explicit TTL configured per cache name. No unbounded caches.
- Key format: `<service>:<entity>:<id>[:v<schemaVersion>]`. Bump the version suffix when the cached shape changes.
- Evict on write in the same service method that changes the data. Prefer eviction to update-in-place.
- Never cache per-user authorization decisions unless the key includes the user and the TTL is short.
- Serialize as JSON (not JDK serialization).
- For distributed locks or rate limits, use a proven library (e.g. Redisson / Bucket4j) rather than hand-rolled SETNX logic. TODO(team): confirm library choice.

## Observability

- Structured JSON logs with trace/span IDs (Micrometer Tracing / OpenTelemetry).
- Actuator health, readiness and liveness enabled; custom health indicators for critical dependencies.
- Metrics: timers on external calls, counters for business events.
- Never log secrets, tokens, or PII. TODO(team): list your PII fields.

## Testing

- Unit tests (JUnit 5 + AssertJ + Mockito) for services with logic.
- `@WebMvcTest` slice tests for controllers: status codes, validation, error shapes.
- `@DataJpaTest` with Testcontainers Postgres for non-trivial queries.
- Full-stack integration tests belong to the integration-testing skill.

## Checklist

- [ ] Layering respected; no entities in API responses
- [ ] Validation on every request DTO
- [ ] Errors map to Problem Details
- [ ] Transactions on service methods; read-only where possible
- [ ] Caches have TTLs and eviction on writes
- [ ] Tests added and passing
