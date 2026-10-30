---
name: local-env
description: Docker and Docker Compose conventions for local development and CI - Dockerfile best practices for Java, Node, and Python services, the compose stack (Postgres, Kafka, Redis, Elasticsearch), health checks, seed data, and env files. Use when containerizing a service, adding or changing a local dependency, or debugging the local stack.
---

# Local environment: Docker + Compose

Start from `templates/docker-compose.yml` for a new stack. TODO(team): pin the image versions you run in production.

## Compose conventions

- One `docker-compose.yml` at repo root for infrastructure dependencies. App services can be in a `docker-compose.apps.yml` override or run from the IDE.
- Every service has a `healthcheck`; dependents use `depends_on: { svc: { condition: service_healthy } }`.
- Pin image tags (`postgres:16.4`), never `latest`.
- Named volumes for data; `docker compose down -v` resets everything.
- Configuration via `.env` (committed `.env.example`, real `.env` gitignored).
- Seed data: SQL in `docker/postgres/init/` (mounted to `/docker-entrypoint-initdb.d`) or a `seed` one-shot service. Flyway still owns the schema; seeds only insert data.
- Use `profiles:` for optional heavy services (e.g. `search` for Elasticsearch, `tools` for Kafka UI / pgAdmin).

## Dockerfile conventions

- Multi-stage: build stage with the full toolchain, runtime stage minimal.
- Pinned base images. Run as a non-root user. `HEALTHCHECK` or orchestrator probes.
- Copy dependency manifests first and install, then copy source (layer caching).
- `.dockerignore` excludes `.git`, `node_modules`, `build/`, `target/`, `.venv`, `.env`.

Java (Spring Boot) runtime stage example:
```dockerfile
FROM eclipse-temurin:21-jre
RUN useradd -r -u 10001 app
WORKDIR /app
COPY --from=build /src/build/libs/app.jar app.jar
USER app
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
```

Node (static frontend) runtime: build with `node:<ver>` then serve `dist/` with `nginx:<ver>-alpine` (non-root config).

Python: `python:<ver>-slim`, `pip install --no-cache-dir -r requirements.txt`, non-root user.

## Verifying changes

```bash
docker compose config -q            # validate syntax
docker compose up -d
docker compose ps                   # all services healthy?
docker compose logs -f <service>    # if not
```

## Checklist

- [ ] Image tags pinned
- [ ] Health checks and healthy-dependency ordering
- [ ] No secrets in compose or Dockerfiles; `.env.example` updated
- [ ] Non-root runtime user
- [ ] Stack comes up healthy from a clean `down -v`
