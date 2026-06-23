# SaaSSpotter Backend

Serverless FastAPI backend that scrapes the web for business pain points via Firecrawl, filters noise with Gemini, and generates Micro-SaaS ideas.

## Stack

- **API:** FastAPI + Mangum on AWS Lambda + API Gateway HTTP API
- **Pipeline:** AWS Step Functions (scrape → Map → process)
- **Schedule:** EventBridge daily cron
- **Database:** MongoDB Atlas (pymongo)
- **AI:** Google Gemini
- **Scraping:** Firecrawl (web search + scrape)

## Quick Start (Local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials

chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

Visit `http://localhost:8000/health` and `http://localhost:8000/docs`.

### Local pipeline mode

Set `LOCAL_PIPELINE_MODE=true` in `.env` to run the full scrape + AI pipeline inline when calling `POST /api/v1/trigger-scrape` (no AWS required).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/painpoints` | Paginated pain points (`page`, `page_size`, `industry_tag`) |
| POST | `/api/v1/trigger-scrape` | Start pipeline (Step Functions or local mode) |
| GET | `/api/v1/scrape-status/{execution_arn}` | Poll Step Functions execution status |

Optional header: `X-Admin-Key` when `ADMIN_API_KEY` is set.

## Deploy to AWS

### 1. Build Lambda packages

```bash
chmod +x scripts/build_lambda.sh
./scripts/build_lambda.sh
```

### 2. Configure Terraform variables

Create `infra/terraform/terraform.tfvars`:

```hcl
mongodb_uri          = "mongodb+srv://..."
gemini_api_key       = "..."
firecrawl_api_key    = "..."
admin_api_key        = "your-secret-key"
```

### 3. Apply infrastructure

```bash
cd infra/terraform
terraform init
terraform apply
```

### 4. Note outputs

- `api_gateway_url` — your API base URL
- `state_machine_arn` — Step Functions pipeline

### 5. Automatic deploy (GitHub Actions)

On push to `main` or `dev`, the workflow in `.github/workflows/deploy.yml` builds Lambda zips and runs `terraform apply`.

**One-time setup:** add GitHub Actions secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `MONGODB_URI`, `GEMINI_API_KEY`, `FIRECRAWL_API_KEY`, `ADMIN_API_KEY`). See [`.github/DEPLOY_SETUP.md`](.github/DEPLOY_SETUP.md) for details and pricing (free tier: 2000 min/mo private, unlimited public repos).

**Manual deploy from your machine** (same as CI):

```bash
./scripts/build_lambda.sh
cd infra/terraform && terraform apply
```

## Project Structure

```
app/
  api/          # FastAPI routers
  aws/          # Secrets Manager, Step Functions helpers
  core/         # Config, exceptions
  db/           # MongoDB + repositories
  handlers/     # Lambda entry points
  models/       # Pydantic schemas
  services/     # Scraper, AI, pipeline logic
infra/
  stepfunctions/  # ASL state machine definition
  terraform/      # AWS infrastructure
scripts/
  build_lambda.sh
  run_local.sh
```

## Estimated Monthly Cost (MVP)

~$6/mo all-in (AWS Lambda + API Gateway + Step Functions + Atlas M0 + Gemini).
