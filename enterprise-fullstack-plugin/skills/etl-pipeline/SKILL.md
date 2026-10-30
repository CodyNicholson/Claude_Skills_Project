---
name: etl-pipeline
description: Python ETL pipeline conventions - job structure (extract/transform/load), idempotency, incremental loads and watermarks, chunked backfills, data-quality checks, configuration, logging, and testing. Use when writing or changing batch or streaming data jobs, backfills, or data movement between Postgres, Kafka, files, and Elasticsearch.
---

# Python ETL pipelines

TODO(team): confirm Python version, orchestrator (Airflow / Dagster / Prefect / cron / Azure Data Factory / AWS Glue / Step Functions), and dataframe library (pandas / polars / pyspark).

## Job structure

```
pipelines/
├── <job_name>/
│   ├── __init__.py
│   ├── extract.py      read from source -> typed records / dataframe
│   ├── transform.py    pure functions, no I/O  <- most tests live here
│   ├── load.py         write to target (upsert)
│   ├── quality.py      checks on the output
│   ├── job.py          wiring + CLI: --start --end --dry-run
│   └── tests/
├── common/             db connections, kafka clients, logging, config
└── requirements.txt / pyproject.toml
```

- `transform.py` is pure: inputs in, outputs out. That makes it fast to test with small fixtures.
- `job.py` exposes a CLI: `python -m pipelines.<job>.job --start 2026-10-01 --end 2026-10-02 [--dry-run]`.

## Idempotency and incremental loads

- Every run is defined by a window (`start`, `end`) or a watermark. Re-running the same window produces the same result.
- Load with **upserts** keyed on natural/business keys (`INSERT ... ON CONFLICT (...) DO UPDATE`), or write to a staging table and swap/merge. Never blind `INSERT` for re-runnable jobs.
- Store watermarks in a control table (`etl_watermarks(job, last_value, updated_at)`), updated in the same transaction as the load where possible.

## Backfills

- Process in bounded chunks (by date or ID range) with a checkpoint after each chunk so a failure resumes, not restarts.
- Throttle to protect production sources. Run off-peak when large.
- Always do a `--dry-run` first that reports expected row counts.

## Data quality

Run after every load; fail the job (non-zero exit) on violation:
- row count within expected range vs source
- required fields not null
- keys unique
- referential checks for foreign keys that matter
- freshness: max(event_time) is recent enough

## Config, secrets, logging

- Config via environment variables (12-factor) parsed into a typed settings object (pydantic-settings).
- Secrets from env / secret store only.
- Structured JSON logs with `job`, `run_id`, `window`, `rows_read`, `rows_written`, `duration_ms`.

## Code quality

- Type hints everywhere; `mypy` or `pyright` clean. `ruff` for lint + format.
- No module-level side effects (no DB connections at import time).

## Testing

- Unit tests for transforms with tiny, explicit fixtures (including nulls, duplicates, late data, timezone edges).
- Integration test per job with Testcontainers Postgres/Kafka: seed source -> run job -> assert target rows -> run again -> assert unchanged (idempotency).

## Checklist

- [ ] Re-runnable for any window; idempotency test exists
- [ ] Upserts or staging+merge
- [ ] Chunked, checkpointed backfill path with dry-run
- [ ] Quality checks fail the job on violation
- [ ] No secrets in code
