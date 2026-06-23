# PainPoint.io — Codebase Guide

This document explains the full repository structure, how data flows through the system, and what every module and function does.

---

## What this project does

**PainPoint.io** is a backend that:

1. **Scrapes Reddit** for posts that sound like business/developer complaints
2. **Filters** them with **Google Gemini** to keep only real pain points
3. **Generates** two Micro-SaaS ideas per valid pain point
4. **Stores** everything in **MongoDB Atlas**
5. **Serves** the ideas to a frontend via a REST API

In production, the scrape → AI pipeline runs on **AWS Lambda** orchestrated by **AWS Step Functions**, triggered daily by **EventBridge** or manually via the API.

---

## High-level architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Next.js    │────▶│ API Gateway      │────▶│ Lambda (api)    │
│  Frontend   │     │ + FastAPI/Mangum │     │ GET /painpoints │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                    ┌──────────────────┐               │ MongoDB Atlas
                    │ EventBridge      │               │
                    │ (daily 6am UTC)  │               ▼
                    └────────┬─────────┘     ┌─────────────────┐
                             │               │  pain_points    │
                             ▼               │  raw_posts      │
                    ┌──────────────────┐   └─────────────────┘
                    │ Step Functions   │
                    │  1. Scrape       │──────────┐
                    │  2. Map (×N)     │          │
                    └────────┬─────────┘          ▼
                             │          ┌─────────────────┐
                             │          │ Lambda (scrape) │──▶ Reddit API
                             │          └─────────────────┘
                             ▼
                    ┌─────────────────┐
                    │ Lambda (process)│──▶ Gemini API
                    │  (per post)     │
                    └─────────────────┘
```

---

## Repository structure

```
SaaSSpotter/
├── app/                          # Python application source
│   ├── main.py                   # FastAPI app entry point
│   ├── api/                      # HTTP routes & dependency injection
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py         # Combines all v1 routes
│   │       ├── painpoints.py     # GET /painpoints
│   │       └── scraper.py        # POST /trigger-scrape, GET /scrape-status
│   ├── aws/                      # AWS SDK helpers
│   │   ├── secrets.py            # Secrets Manager loader
│   │   └── stepfunctions.py      # Start/describe pipeline executions
│   ├── core/                     # Config & error handling
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── db/                       # MongoDB connection & repositories
│   │   ├── mongodb.py
│   │   └── repositories/
│   │       ├── raw_posts.py
│   │       └── pain_points.py
│   ├── handlers/                 # AWS Lambda entry points
│   │   ├── api_handler.py
│   │   ├── scrape_handler.py
│   │   └── process_handler.py
│   ├── models/                   # Pydantic schemas (validation)
│   │   ├── common.py
│   │   ├── raw_post.py
│   │   └── pain_point.py
│   └── services/                 # Business logic
│       ├── scraper_service.py
│       ├── ai_service.py
│       └── pipeline_service.py
├── infra/
│   ├── stepfunctions/
│   │   └── pipeline.asl.json     # Step Functions state machine definition
│   └── terraform/                # AWS infrastructure as code
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── lambda.tf
│       ├── apigateway.tf
│       ├── stepfunctions.tf
│       ├── eventbridge.tf
│       ├── secrets.tf
│       ├── iam.tf
│       └── cloudwatch.tf
├── scripts/
│   ├── run_local.sh              # Start uvicorn dev server
│   └── build_lambda.sh           # Package app for Lambda deploy
├── requirements.txt
├── .env.example
├── README.md
└── CODEBASE.md                   # This file
```

---

## Data flow (pipeline)

### Stage 1 — Scrape

1. **Trigger:** EventBridge cron (daily) or `POST /api/v1/trigger-scrape`
2. **Step Functions** invokes `scrape_handler` Lambda
3. `PipelineService.scrape_stage()`:
   - Calls `ScraperService.scrape_web()` → Firecrawl search + scrape
   - Upserts posts into `raw_posts` collection (deduped by `source_id`)
   - Returns list of unprocessed post MongoDB IDs

### Stage 2 — Process (parallel)

1. **Step Functions Map state** fans out one Lambda invocation per post ID (max 10 concurrent)
2. Each `process_handler` Lambda calls `PipelineService.process_post_stage(id)`:
   - **Filter:** Gemini decides if post is a real pain point
   - If invalid → mark post processed, skip
   - If valid → **Generate** two SaaS ideas + demand score + industry tag
   - Insert into `pain_points` collection
   - Mark `raw_posts.processed_at`

### Stage 3 — Serve

- Frontend calls `GET /api/v1/painpoints` → paginated list from MongoDB

---

## MongoDB collections

### `raw_posts`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | MongoDB document ID |
| `source` | string | `"firecrawl"` (scraped via Firecrawl) |
| `source_id` | string | Reddit post ID (unique index) |
| `text` | string | Title + body combined |
| `url` | string | Reddit permalink |
| `subreddit` | string | e.g. `"SaaS"` |
| `created_at` | datetime | When post was created on Reddit |
| `scraped_at` | datetime | When we ingested it |
| `processed_at` | datetime \| null | When AI pipeline finished (null = pending) |

### `pain_points`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | MongoDB document ID |
| `original_post_id` | string | FK to `raw_posts._id` (unique) |
| `core_problem` | string | One-sentence problem summary |
| `saas_idea_1` | string | First Micro-SaaS idea |
| `saas_idea_2` | string | Second Micro-SaaS idea |
| `demand_score` | int (1–10) | AI-estimated demand |
| `industry_tag` | string | e.g. `"developer-tools"` |
| `source_url` | string | Original Reddit URL |
| `created_at` | datetime | When idea was generated |

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/painpoints` | Paginated pain points (`page`, `page_size`, `industry_tag`) |
| `POST` | `/api/v1/trigger-scrape` | Start pipeline (Step Functions or local mode) |
| `GET` | `/api/v1/scrape-status/{execution_arn}` | Poll Step Functions execution status |

**Auth:** If `ADMIN_API_KEY` is set, `POST /trigger-scrape` requires header `X-Admin-Key: <value>`.

---

## Module reference

### `app/main.py` — Application entry point

| Function | What it does |
|----------|--------------|
| `lifespan(app)` | Async context manager run at startup/shutdown. Loads AWS secrets, creates MongoDB indexes, closes DB on exit. |
| `create_app()` | Builds and configures the FastAPI app: CORS, exception handlers, `/health` route, mounts `/api/v1` router. |
| `health()` | Returns `{"status": "ok", "mode": "api"}`. Used by ALB/API Gateway health checks. |

**Global:** `app = create_app()` — imported by uvicorn locally and Mangum in Lambda.

---

### `app/core/config.py` — Settings

#### Class: `Settings`

Loads all configuration from `.env` and environment variables via pydantic-settings.

| Member | What it does |
|--------|--------------|
| `validate_post_limit(v)` | Clamps `SCRAPE_POST_LIMIT` between 1 and 500. |
| `is_lambda` (property) | `True` when `AWS_LAMBDA_FUNCTION_NAME` env var is set. |
| `scrape_target_list` (property) | Parses comma-separated `SCRAPE_TARGETS` into a list. |
| `keyword_list` (property) | Parses comma-separated `SCRAPE_KEYWORDS` into a list. |
| `cors_origin_list` (property) | Parses comma-separated `CORS_ORIGINS` into a list. |
| `apply_secrets(secrets)` | Merges a dict from AWS Secrets Manager into settings fields. |

| Function | What it does |
|----------|--------------|
| `get_settings()` | Returns cached singleton `Settings` instance. |

**Global:** `settings = get_settings()`

---

### `app/core/exceptions.py` — Errors

| Class / Function | What it does |
|------------------|--------------|
| `AppError` | Base exception with `message` and `status_code`. |
| `NotFoundError` | 404 variant of `AppError`. |
| `ServiceUnavailableError` | 503 variant (e.g. DB down, AWS unavailable). |
| `register_exception_handlers(app)` | Registers handler that converts `AppError` → JSON `{"detail": "..."}`. |

---

### `app/aws/secrets.py` — AWS Secrets Manager

| Function | What it does |
|----------|--------------|
| `load_secrets()` | Fetches JSON secret from AWS Secrets Manager (if `AWS_SECRETS_MANAGER_SECRET_NAME` is set). Caches result. Returns `{}` locally. |
| `init_settings_from_secrets()` | Calls `load_secrets()` then `settings.apply_secrets()`. |
| `get_boto3_session()` | Returns cached boto3 Session for the configured AWS region. |

---

### `app/aws/stepfunctions.py` — Pipeline orchestration

| Function | What it does |
|----------|--------------|
| `_client()` | Creates boto3 Step Functions client. |
| `start_pipeline_execution(name, input_payload)` | Starts the state machine. Returns execution ARN. Raises 409 if name already exists, 503 on AWS errors. |
| `start_daily_pipeline_execution()` | Starts execution named `painpoint-YYYY-MM-DD` (prevents duplicate daily runs). |
| `describe_execution(execution_arn)` | Returns `{execution_arn, status, start_date, stop_date}` for polling. |
| `json_dumps(payload)` | Serializes dict to JSON string for Step Functions input. |

---

### `app/db/mongodb.py` — Database connection

| Function | What it does |
|----------|--------------|
| `get_client()` | Returns singleton `MongoClient` (reused across Lambda warm starts). |
| `get_database()` | Returns the configured database (`MONGODB_DB_NAME`). |
| `close_client()` | Closes connection and resets singleton. Called on app shutdown. |
| `ensure_indexes()` | Creates indexes on `raw_posts` and `pain_points` collections. |

---

### `app/db/repositories/raw_posts.py` — Raw post data access

#### Class: `RawPostRepository`

| Method | What it does |
|--------|--------------|
| `__init__(db)` | Binds to `db.raw_posts` collection. |
| `upsert_many(posts)` | Inserts new posts only (`$setOnInsert`). Dedupes by `source_id`. Returns count of newly inserted docs. |
| `find_unprocessed(limit)` | Returns posts where `processed_at` is `null`. |
| `find_by_id(post_id)` | Looks up a single post by MongoDB ObjectId string. Returns `None` if not found. |
| `mark_processed(post_id)` | Sets `processed_at` to current UTC time. |
| `_to_read(doc)` | Converts MongoDB dict → `RawPostRead` Pydantic model. |

---

### `app/db/repositories/pain_points.py` — Pain point data access

#### Class: `PainPointRepository`

| Method | What it does |
|--------|--------------|
| `__init__(db)` | Binds to `db.pain_points` collection. |
| `insert_one(pain_point)` | Inserts a `PainPointCreate` document. Returns new `_id` as string. |
| `find_paginated(page, page_size, industry_tag)` | Returns `(items, total_count)` sorted by `created_at` descending. Optional filter by `industry_tag`. |
| `_to_read(doc)` | Converts MongoDB dict → `PainPointRead` Pydantic model. |

---

### `app/models/` — Pydantic schemas

#### `common.py`

| Class / Function | What it does |
|------------------|--------------|
| `MongoModel` | Base model with `populate_by_name=True` for `_id` ↔ `id` aliasing. |
| `PaginatedResponse[T]` | Generic wrapper: `items`, `total`, `page`, `page_size`, `has_next`. |
| `ScrapeResult` | Pipeline output: `scraped_count`, `unprocessed_ids[]`. |
| `ProcessResult` | Per-post output: `raw_post_id`, `processed`, `is_valid_pain_point`, `pain_point_id`, `skipped_reason`. |
| `FilterResult` | Gemini filter response: `is_valid`, `confidence`, `reason`. |
| `IdeaResult` | Gemini generator response: `core_problem`, `saas_idea_1`, `saas_idea_2`, `demand_score`, `industry_tag`. |
| `utc_now()` | Returns current UTC datetime (used as default for timestamps). |

#### `raw_post.py`

| Class | What it does |
|-------|--------------|
| `RawPostBase` | Shared fields for a scraped Reddit post. |
| `RawPostCreate` | Schema for inserting a new raw post. |
| `RawPostRead` | Schema for reading from DB (includes `id` aliased from `_id`). |

#### `pain_point.py`

| Class | What it does |
|-------|--------------|
| `PainPointBase` | Shared fields for a generated pain point + ideas. |
| `PainPointCreate` | Schema for inserting a new pain point. |
| `PainPointRead` | Schema for API responses (includes `id`). |

---

### `app/services/scraper_service.py` — Web scraping (Firecrawl)

#### Class: `ScraperService`

| Method | What it does |
|--------|--------------|
| `__init__(settings)` | Stores settings; lazily creates Firecrawl client. |
| `_get_client()` | Creates and caches `Firecrawl` client from `FIRECRAWL_API_KEY`. |
| `scrape_web()` | Loops targets × keywords, runs Firecrawl `search()` with markdown scrape, dedupes by URL hash, stops at `SCRAPE_POST_LIMIT`. |
| `scrape_subreddits()` | Backward-compatible alias for `scrape_web()`. |
| `_build_search_query(target, keyword)` | Builds `site:{target} {keyword}` search query. |
| `_iter_web_results(results)` | Normalizes Firecrawl search response into a list of web results. |
| `_result_to_post(item, target)` | Converts a search result to `RawPostCreate` (title + markdown/description). |
| `_get_field(item, key)` | Reads a field from dict or object result. |
| `_parse_created_at(item)` | Parses publish date from result metadata if available. |

---

### `app/services/ai_service.py` — Gemini AI

#### Class: `AIService`

| Method | What it does |
|--------|--------------|
| `__init__(settings)` | Stores settings; lazily creates Gemini model. |
| `_get_model()` | Configures `google.generativeai` and returns `GenerativeModel` with JSON output mode. |
| `filter_pain_point(text, subreddit)` | Sends filter prompt to Gemini. Returns `FilterResult` (is it a real pain point?). |
| `generate_ideas(text, subreddit)` | Sends generator prompt to Gemini. Returns `IdeaResult` (problem + 2 ideas + score + tag). |
| `_call_and_parse(prompt, model_class)` | Calls Gemini, parses JSON response, validates with Pydantic. Retries once on failure. |

**Prompts:** `FILTER_PROMPT` and `GENERATE_PROMPT` are module-level templates at the top of the file.

---

### `app/services/pipeline_service.py` — Pipeline orchestration

#### Class: `PipelineService`

| Method | What it does |
|--------|--------------|
| `__init__(settings)` | Wires up repositories, `ScraperService`, and `AIService`. |
| `scrape_stage()` | Scrapes Reddit → upserts to DB → returns `ScrapeResult` with unprocessed post IDs. Used by Step Functions **Scrape** state. |
| `process_post_stage(raw_post_id)` | Loads one post → filter → generate → save (or skip). Idempotent. Returns `ProcessResult`. Used by Step Functions **Map** iterations. |
| `run_local_pipeline()` | Runs `scrape_stage()` then `process_post_stage()` for every ID inline. Used when `LOCAL_PIPELINE_MODE=true`. |

---

### `app/api/deps.py` — Dependency injection

FastAPI `Depends()` providers — create fresh instances per request.

| Function | What it does |
|----------|--------------|
| `get_app_settings()` | Returns `Settings` singleton. |
| `get_pain_point_repo()` | Returns `PainPointRepository` bound to current DB. |
| `get_raw_post_repo()` | Returns `RawPostRepository` bound to current DB. |
| `get_pipeline_service()` | Returns `PipelineService` instance. |

---

### `app/api/v1/painpoints.py` — Read API

| Function | What it does |
|----------|--------------|
| `list_pain_points(page, page_size, industry_tag, repo)` | `GET /api/v1/painpoints`. Queries MongoDB with pagination. Returns 503 if DB is down. |

---

### `app/api/v1/scraper.py` — Pipeline trigger API

| Function | What it does |
|----------|--------------|
| `_verify_admin_key(settings, x_admin_key)` | Dependency: rejects request with 401 if `ADMIN_API_KEY` is set and header doesn't match. |
| `trigger_scrape(settings, pipeline)` | `POST /api/v1/trigger-scrape`. Local mode → runs full pipeline inline. Production → starts Step Functions execution. Returns 202. |
| `scrape_status(execution_arn)` | `GET /api/v1/scrape-status/{arn}`. Polls Step Functions for RUNNING/SUCCEEDED/FAILED status. |

---

### `app/api/v1/router.py` — Route aggregation

Combines `painpoints.router` and `scraper.router` into a single `APIRouter` mounted at `/api/v1`.

---

### `app/handlers/` — Lambda entry points

| File | Handler | What it does |
|------|---------|--------------|
| `api_handler.py` | `handler` | Mangum ASGI adapter wrapping FastAPI `app`. Entry point for API Gateway. `lifespan="off"` for faster cold starts. |
| `scrape_handler.py` | `handler(event, context)` | Loads secrets → ensures indexes → runs `scrape_stage()` → returns `{raw_post_ids, scraped_count}` to Step Functions. |
| `process_handler.py` | `handler(event, context)` | Loads secrets → reads `event["raw_post_id"]` → runs `process_post_stage()` → returns result dict. |

---

## Infrastructure

### `infra/stepfunctions/pipeline.asl.json`

AWS Step Functions **Standard** workflow definition:

| State | Type | What it does |
|-------|------|--------------|
| **Scrape** | Task | Invokes scrape Lambda. Retries 2× on AWS errors. On failure → `ScrapeFailed`. |
| **ProcessPosts** | Map | Iterates `$.raw_post_ids` with max 10 concurrent branches. Tolerates 20% failures. |
| **ProcessPost** | Task (inside Map) | Invokes process Lambda per post ID. Retries 2×. |
| **ScrapeFailed** | Fail | Terminal failure state; triggers CloudWatch alarm. |

Terraform replaces `${scrape_lambda_arn}` and `${process_lambda_arn}` with real Lambda ARNs at deploy time.

### `infra/terraform/` — AWS resources

| File | Resources created |
|------|-------------------|
| `main.tf` | AWS provider, caller identity |
| `variables.tf` | Input variables (credentials, region, zip paths) |
| `outputs.tf` | `api_gateway_url`, `state_machine_arn`, etc. |
| `lambda.tf` | 3 Lambda functions (api, scrape, process) + shared dependency layer |
| `apigateway.tf` | HTTP API → api Lambda proxy integration |
| `stepfunctions.tf` | State machine from ASL JSON |
| `eventbridge.tf` | Daily cron `cron(0 6 * * ? *)` → start state machine |
| `secrets.tf` | Secrets Manager secret with all app credentials |
| `iam.tf` | IAM roles for Lambda, Step Functions, EventBridge |
| `cloudwatch.tf` | Log groups (14-day retention) + alarm on failed executions |

**No VPC, no ECS, no SQS** — fully serverless.

---

## Scripts

### `scripts/run_local.sh`

Activates nothing (assumes venv is active) and runs:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### `scripts/build_lambda.sh`

1. `pip install -r requirements.txt` into `build/layer/python/`
2. Copies `app/` into `build/lambda/`
3. Creates `build/api.zip` (app code) and `build/layer.zip` (dependencies)

These zips are referenced by Terraform when deploying Lambda.

---

## Environment variables

See `.env.example` for the full list. Key variables:

| Variable | Purpose |
|----------|---------|
| `MONGODB_URI` | MongoDB Atlas connection string |
| `GEMINI_API_KEY` | Google Gemini API key |
| `FIRECRAWL_API_KEY` | Firecrawl API key |
| `SCRAPE_TARGETS` | Comma-separated sites for `site:` search (e.g. `reddit.com/r/SaaS`) |
| `SCRAPE_KEYWORDS` | Comma-separated search keywords |
| `LOCAL_PIPELINE_MODE` | `true` = run pipeline inline without AWS |
| `STEP_FUNCTIONS_STATE_MACHINE_ARN` | ARN for production pipeline trigger |
| `ADMIN_API_KEY` | Optional auth for `POST /trigger-scrape` |

---

## How to read a request end-to-end

### Example: `GET /api/v1/painpoints?page=1&page_size=10`

```
API Gateway → api_handler (Mangum) → FastAPI app
  → v1 router → painpoints.list_pain_points()
    → Depends(get_pain_point_repo)
      → PainPointRepository.find_paginated()
        → MongoDB pain_points collection
  ← PaginatedResponse[PainPointRead] JSON
```

### Example: `POST /api/v1/trigger-scrape` (production)

```
API Gateway → scraper.trigger_scrape()
  → _verify_admin_key() (if configured)
  → start_pipeline_execution()
    → AWS Step Functions StartExecution
      → Scrape Lambda → scrape_stage() → Reddit + MongoDB
      → Map (×N) → Process Lambda → process_post_stage() → Gemini + MongoDB
  ← 202 {"status": "started", "execution_arn": "..."}
```

---

## Local vs production behavior

| Concern | Local (`./scripts/run_local.sh`) | Production (AWS) |
|---------|----------------------------------|------------------|
| API server | uvicorn | Lambda + API Gateway |
| Secrets | `.env` file | Secrets Manager + env vars |
| Pipeline trigger | Step Functions ARN or `LOCAL_PIPELINE_MODE` | Step Functions |
| MongoDB | Atlas or local | MongoDB Atlas |
| Scheduling | Manual trigger | EventBridge daily cron |

---

## Adding new features — where to look

| I want to… | Edit… |
|------------|-------|
| Add a new API endpoint | `app/api/v1/` + register in `router.py` |
| Change Reddit search logic | `app/services/scraper_service.py` |
| Change AI prompts or model | `app/services/ai_service.py` |
| Change DB schema | `app/models/` + `app/db/repositories/` |
| Add a pipeline step | `pipeline_service.py` + `pipeline.asl.json` + new handler |
| Change AWS resources | `infra/terraform/` |
| Add env variable | `app/core/config.py` + `.env.example` |
