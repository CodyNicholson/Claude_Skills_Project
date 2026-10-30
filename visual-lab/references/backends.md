# Choosing and building the backend

Pick the language the tool is native to, so the demos show real, idiomatic usage:

| Tool kind | Backend | Starter | Example lab |
|---|---|---|---|
| Python library / framework (LangChain, pandas, Pydantic, Celery, …) | FastAPI, Python 3.12 | `--backend python-fastapi` | LangChain_LangGraph_Visual_Project |
| JS/TS server-side library (Prisma, BullMQ, Socket.IO, Zod, …) | Express 5, Node 22 | `--backend node-express` | – |
| JVM tool or Java client (Kafka, Flink, Spring, Hibernate, …) | Spring Boot 3, Java 21, Maven | `--backend none`, then the Spring section below | Redis, Kafka, Flink labs |
| Server / database / broker with clients in many languages (Redis, Postgres, NATS, Elasticsearch, …) | Whichever client is most mature; Spring Boot or FastAPI are both fine | either | Redis lab |
| Go / Rust tool | A small Go (`net/http`) or Rust (`axum`) service in the same shape | `--backend none` | – |
| Browser-only library (D3, Three.js, GSAP, Chart.js, …) | No backend: the demos run in the page | `--backend none`, then delete the `backend` service, the `backend-net` network and nginx `/api/` block | – |

Whatever the language: one route per feature under `/api/demos/...` returning the
DemoResult (`references/conventions.md`), `/api/health`, input clamping, a Dockerfile with
`test` and `runtime` stages, and tests that call every demo route and fail on any failed
check.

## The tool itself as a service

When the tool is a server (database, broker, cache, search engine, stream processor), run
the official image in `docker-compose.yml` with a pinned version tag, a healthcheck, a
named volume, and the backend `depends_on: { tool: { condition: service_healthy } }`.
Configure it to show off features (Redis lab: `--appendonly yes`,
`--notify-keyspace-events Ex`). Put it only on `backend-net` (internal). Expose host ports
only where poking at it from the host is useful, always bound to `127.0.0.1`
(`"127.0.0.1:6379:6379"`), and drop them in `docker-compose.test.yml` with `ports: !reset []`.
Passwords for it come from `.env` with no compose fallback (`${REDIS_PASSWORD:?…}`) and go in
`GENERATED_SECRETS` in `pipeline-run.sh`. Add each such
service to `docker-compose.test.yml` with a renamed `container_name`.

## Python (FastAPI)

- `app/lab.py` has `Demo` (records commands and checks) and `clamp`. Group demos by
  category in `app/demos/<category>.py` with an `APIRouter` each, included in `main.py`.
- Pin exact versions in `requirements.txt` after checking what is current:
  `docker run --rm python:3.12-slim pip index versions <package>`.
- Tests run in the image build (`docker build --target test backend`). If they need the
  real service, run them against the isolated compose stack instead
  (`docker compose -p <slug>-test ... run --rm backend python -m pytest`, with the dev
  requirements installed in that stage).

## Node (Express)

- `src/app.js` holds routes; list every demo route in `DEMO_ROUTES` so `test/api.test.js`
  runs them all. Check versions with `docker run --rm node:22-alpine npm view <pkg> version`.
- Generate `package-lock.json` inside Docker (`docker run --rm -v "$PWD":/app -w /app
  node:22-alpine npm install`) so `npm ci` works and builds are reproducible. Do the same
  for the frontend.

## Spring Boot (Java 21)

Copy the shape of `Redis_Visual_Lab_Project/backend` (or Kafka/Flink):

```
backend/
├── Dockerfile          # maven:3.9-eclipse-temurin-21 build → eclipse-temurin:21-jre runtime
├── pom.xml             # spring-boot-starter-web, the tool's client, testcontainers for tests
└── src/main/java/com/example/<slug>/
    ├── <Tool>LabApplication.java
    ├── controller/LabController.java   # @RestController @RequestMapping("/api/demos")
    ├── service/…Service.java           # one per category
    ├── model/DemoResult.java           # record DemoResult(String demo, List<String> commands,
    │                                   #   Map<String,Object> data, List<Check> checks, double elapsedMs)
    └── config/…Config.java
```

Dockerfile (rename the last stage `runtime` to match the compose `target`):

```dockerfile
FROM maven:3.9.8-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B dependency:go-offline
COPY src ./src
RUN mvn -B clean package -DskipTests

FROM build AS test
RUN mvn -B test

FROM eclipse-temurin:21-jre AS runtime
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

If the tests use Testcontainers they need a Docker socket, so run them outside the image
build, as the Redis README shows:
`docker run --rm --network host -v /var/run/docker.sock:/var/run/docker.sock -v "$PWD":/app -w /app -e TESTCONTAINERS_HOST_OVERRIDE=localhost maven:3.9.8-eclipse-temurin-21 mvn -B test`.

Compose healthcheck for a JRE image without curl: expose Spring Actuator and use
`["CMD-SHELL", "bash -c ':> /dev/tcp/localhost/8080' || exit 1"]`, or add `curl` to the
runtime image. Set `JAVA_TOOL_OPTIONS: -Xmx768m`.

## Live event streams (SSE)

For asynchronous tools, push each real step to the browser as it happens:
FastAPI `StreamingResponse` with `text/event-stream`, Express `res.write('event: lab-event\ndata: …\n\n')`,
Spring `SseEmitter` (Kafka lab `TelemetryService`). Send a `hello` event on connect and a
comment heartbeat every 15 s so proxies keep the stream open. Then set `LIVE_EVENTS = true`
in `App.jsx` and read events in visuals with `useLiveEvents()`.

## Browser-only libraries

Delete the `backend` service from both compose files and the `location /api/` block from
`nginx.conf`. Install the library in `frontend/package.json` (pinned). Each demo's actions
run local functions instead of HTTP calls: give actions a `run: (inputs) => DemoResult`
function and change `runAction` in `api.js` to call `action.run(inputs)` when present.
Keep `test` entries pointing at those local runs and update `TestRunner` / the catalog test
and the `smoke` step of `test-isolated.sh` (it then only checks `/`).
