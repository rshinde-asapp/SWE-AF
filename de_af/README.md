<div align="center">

# DE-AF

### Autonomous Data Engineering Team Runtime Built on [AgentField](https://github.com/Agent-Field/agentfield)

**Pronounced:** _"dee-AF"_

[![Public Beta](https://img.shields.io/badge/status-public%20beta-0ea5e9?style=for-the-badge)](#)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-16a34a?style=for-the-badge)](LICENSE)
[![Built with AgentField](https://img.shields.io/badge/Built%20with-AgentField-0A66C2?style=for-the-badge)](https://github.com/Agent-Field/agentfield)

**One API call → full data engineering team → shipped data pipeline.**

<p>
  <a href="#quick-start">Quick Start</a> •
  <a href="#why-de-af">Why DE-AF</a> •
  <a href="#use-cases">Use Cases</a> •
  <a href="#example-goals">Example Goals</a> •
  <a href="#data-engineering-factory-architecture">Architecture</a> •
  <a href="#operating-modes">Operating Modes</a> •
  <a href="#benchmark">Benchmark</a> •
  <a href="#api-reference">API</a>
</p>

</div>

One API call spins up a full autonomous data engineering team — product managers, architects, data engineers, QA validators, schema reviewers — that scopes, builds, tests, and ships end-to-end data pipelines.

DE-AF is a specialized fork of [SWE-AF](https://github.com/Agent-Field/swe-af) adapted for data platform workflows: ETL/ELT pipelines, data quality validation, schema evolution, and infrastructure provisioning.

## One-Call DX

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Build customer 360 pipeline from PostgreSQL to Snowflake with SCD Type 2",
    "repo_url": "https://github.com/user/data-platform",
    "config": {
      "runtime": "claude_code",
      "models": {
        "default": "sonnet",
        "coder": "opus"
      }
    }
  }
}
JSON
```

## What DE-AF Produces

Given a data pipeline goal, DE-AF delivers:

1. **Working pipeline code**: SQL transformations, dbt models, Airflow/Prefect DAGs, Spark jobs
2. **Data quality tests**: Great Expectations suites, dbt tests, SQL assertions
3. **Schema definitions**: DDL with types, constraints, partitioning, indexes
4. **Infrastructure config**: Terraform/Pulumi for warehouses, storage, orchestrators
5. **Integration tests**: End-to-end validation with fixture data
6. **Documentation**: Data catalog entries, lineage diagrams, runbooks

## Use Cases

### ETL/ELT Pipeline Development
- **Batch data ingestion**: APIs → data lake, databases → data warehouse, files → cloud storage
- **Transformation logic**: SQL window functions, dbt incremental models, Spark aggregations
- **Data pipeline orchestration**: Airflow DAGs, Prefect flows, dbt Cloud jobs
- **Change data capture**: Incremental loads with watermarks, merge/upsert patterns

### Data Quality Implementation
- **Test generation**: Unique/not-null checks, referential integrity, business rule validation
- **Data profiling**: Row counts, null percentages, distribution analysis
- **PII detection**: Regex validation for email/SSN/phone, masking strategies
- **Anomaly detection**: Distribution drift, outlier identification, freshness monitoring

### Schema Evolution
- **Backward-compatible changes**: Add nullable columns, expand enums, create indexes
- **Multi-phase migrations**: Add column → backfill → enforce constraint
- **Impact analysis**: Identify affected downstream pipelines
- **Version control**: Schema DDL history, migration scripts, rollback procedures

### Infrastructure Provisioning
- **Data warehouse setup**: Snowflake databases/schemas, BigQuery datasets, Redshift clusters
- **Storage configuration**: S3 buckets, GCS paths, ADLS containers
- **Access control**: IAM roles, service accounts, row-level security
- **Cost optimization**: Auto-suspend warehouses, partition pruning, clustering

## Example Goals

DE-AF accepts natural language goals describing data pipeline work:

```bash
# Customer 360 pipeline with SCD Type 2 dimensions
"Build a customer 360 pipeline from PostgreSQL to Snowflake with SCD Type 2 dimensions"

# PII masking for compliance
"Add PII masking to user_events table for email and SSN columns"

# Incremental dbt model
"Convert fct_orders from full refresh to incremental with order_date watermark"

# Great Expectations data quality suite
"Create Great Expectations suite for customer_dim validating email format and US states"

# Schema migration
"Add customer_tier column to dim_customers with Bronze/Silver/Gold values"

# Infrastructure provisioning
"Provision Snowflake warehouse for analytics workloads with auto-suspend"

# Airflow DAG for multi-step ETL
"Build Airflow DAG for daily customer data sync: extract from API → stage in S3 → load to Snowflake"

# dbt medallion architecture
"Implement bronze/silver/gold medallion layers for user events pipeline"
```

## Why DE-AF

Most data orchestration tools just schedule jobs. DE-AF is an autonomous engineering factory that designs, implements, tests, and validates complete data pipelines.

- **Data-aware execution** — understands schemas, lineage, data quality, and backward compatibility
- **Quality-first** — generates data quality tests alongside transformation logic (not as an afterthought)
- **Schema-safe** — validates migrations for backward compatibility, enforces constraint sequencing
- **Framework-native** — produces idiomatic dbt models, Airflow DAGs, Spark jobs (not generic glue code)
- **Infra-included** — provisions warehouses, buckets, IAM roles via Terraform/Pulumi
- **Multi-model, multi-provider** — assign different models per role (`coder: opus`, `qa: haiku`). Works with Claude, OpenRouter, OpenAI, and Google.
- **Continual learning** — with `enable_learning=true`, conventions and failure patterns discovered early are injected into downstream issues.
- **Agent-scale parallelism** — dependency-level scheduling + isolated git worktrees allow large fan-out without branch collisions.

## Data Engineering Factory Architecture

DE-AF preserves SWE-AF's multi-agent coordination while specializing agents for data engineering workflows:

### Planning Agents
1. **Product Manager** — translates data pipeline goals into precise requirements with schemas, SLAs, and quality expectations
2. **Architect** — designs data flow (source → staging → transformation → serving), schema DDL, quality checkpoints, infrastructure components
3. **Sprint Planner** — decomposes work into dependency-ordered issue DAG for parallel execution

### Execution Agents
1. **Coder** — generates SQL transformations, dbt models, Airflow DAGs, Spark jobs, Terraform modules
2. **Data Quality Validator** — verifies test coverage for critical columns, PII detection, schema validation
3. **QA** — runs data quality tests, validates schema adherence, checks pipeline idempotency
4. **Schema Reviewer** — validates backward compatibility, migration safety, index coverage, partitioning strategy

### Governance Agents
1. **Issue Advisor** — adapts failed issues (retry with feedback, split work, accept with debt, or escalate)
2. **Replanner** — restructures remaining issue DAG when failures escalate
3. **Schema Migrator** — coordinates multi-phase schema migrations (add nullable → backfill → enforce constraint)
4. **Merger** — integrates branches from parallel issues
5. **Verifier** — validates final pipeline against acceptance criteria from PRD

### Specialized Data Engineering Agents

- **Data Quality Validator**: Runs after coder to verify test coverage for critical columns (keys, amounts, dates), PII detection tests, schema validation logic, and data profiling for new tables
- **Schema Reviewer**: Validates schema changes for backward compatibility, migration safety, index coverage, and partitioning strategy before merge
- **Schema Migrator**: Plans and coordinates multi-phase schema evolution to avoid breaking downstream pipelines

### Control Loops

DE-AF uses three nested control loops to adapt to task difficulty in real time:

| Loop        | Scope         | Trigger              | Action                                                                             |
| ----------- | ------------- | -------------------- | ---------------------------------------------------------------------------------- |
| Inner loop  | Single issue  | QA/review fails      | Coder retries with feedback                                                        |
| Middle loop | Single issue  | Inner loop exhausted | `run_issue_advisor` retries with a new approach, splits work, or accepts with debt |
| Outer loop  | Remaining DAG | Escalated failures   | `run_replanner` restructures remaining issues and dependencies                     |

This is the core factory-control behavior: control agents supervise worker agents and continuously reshape the plan as reality changes.

## Operating Modes

DE-AF works in two modes: point it at a single data repository, or orchestrate coordinated changes across multiple repos in one build.

### Single-Repository Mode

The default. Pass `repo_url` (remote) or `repo_path` (local) and DE-AF handles everything:

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "goal": "Add incremental processing to user_events dbt model",
      "repo_url": "https://github.com/org/data-platform"
    }
  }'
```

### Multi-Repository Mode

When your work spans multiple codebases — a primary dbt project plus shared macro library, monorepo sub-projects, or dependent data services — pass `config.repos` as an array with roles:

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "goal": "Implement PII masking macro and apply to user tables",
      "config": {
        "repos": [
          {
            "repo_url": "https://github.com/org/dbt-project",
            "role": "primary"
          },
          {
            "repo_url": "https://github.com/org/dbt-macros",
            "role": "dependency"
          }
        ]
      }
    }
  }'
```

**Roles:**
- `primary` — The main data platform project. Changes here drive the build; failures block progress.
- `dependency` — Shared libraries, macros, or utilities modified to support the primary repo. Failures are captured but don't block.

**Use cases:**
- Primary dbt project + shared dbt macros library
- Data warehouse DDL repo + pipeline orchestration repo
- Feature spanning multiple data services (e.g., ingestion pipeline + transformation service)

## Benchmark

**Autonomous ETL Pipeline Build**: Simple CSV → Parquet pipeline with data quality validation (built autonomously).

This is a data pipeline project demonstrating end-to-end ETL with quality checks, not a software application. The pipeline extracts data from CSV files, transforms it with SQL and dbt, validates quality with Great Expectations, and loads to Parquet format in cloud storage.

| Artifact Type              | Count | Examples                                      |
| -------------------------- | ----- | --------------------------------------------- |
| SQL transformations        | 5     | staging, dimension tables, fact tables        |
| dbt models + tests         | 7     | stg_users.sql, schema.yml, custom tests       |
| Airflow DAG tasks          | 5     | extract, transform, load, test, validate      |
| Terraform modules          | 3     | data warehouse, S3 bucket, IAM roles          |
| Great Expectations suite   | 1     | 5 expectations (unique, regex, date range)    |
| Integration tests          | 1     | End-to-end with fixture data                  |
| Data quality validations   | 12    | Null checks, uniqueness, referential integrity|

**Pipeline characteristics:**
- Idempotent: Safely rerunnable without duplicating data
- Incremental: Processes only new/changed records after initial load
- Tested: Data quality validated at each stage
- Documented: Schema DDL, lineage diagrams, runbook

See full example: [`examples/simple-etl/README.md`](examples/simple-etl/README.md)

## Quick Start

### 1. Requirements

- Python 3.12+
- AgentField control plane (`af`)
- AI provider API key (Anthropic, OpenRouter, OpenAI, or Google)

### 2. Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Run

```bash
af                 # starts AgentField control plane on :8080
python -m de_af    # registers node id "de-planner"
```

### 4. Trigger a build

```bash
# Default (uses Claude)
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Build customer 360 pipeline with SCD Type 2 dimensions",
    "repo_url": "https://github.com/user/data-platform"
  }
}
JSON

# With open-source runtime + flat role map
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add PII masking to user events table",
    "repo_url": "https://github.com/user/data-platform",
    "config": {
      "runtime": "open_code",
      "models": {
        "default": "openrouter/minimax/minimax-m2.5"
      }
    }
  }
}
JSON

# Local workspace mode (repo_path) + targeted role override
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Create Great Expectations suite for customer dimension",
    "repo_path": "/path/to/data-platform",
    "config": {
      "runtime": "claude_code",
      "models": {
        "default": "sonnet",
        "coder": "opus",
        "qa": "opus"
      },
      "enable_learning": true
    }
  }
}
JSON
```

## What Happens In One Build

- Architecture is generated and reviewed before coding starts
- Issues are dependency-sorted and run in parallel across isolated worktrees
- Each issue gets dedicated coder, tester, and reviewer passes
- Data quality validator ensures test coverage for critical columns
- Schema reviewer checks backward compatibility and migration safety
- Failed issues trigger advisor-driven adaptation (split, re-scope, or escalate)
- Escalations trigger replanning of the remaining DAG
- End result is merged, integration-tested, and verified against acceptance criteria

> Typical runs spin up 400-500+ agent instances across planning, execution, QA, and verification. For larger DAGs and repeated adaptation/replanning cycles, DE-AF can scale into the high hundreds to thousands of agent invocations in a single build.

## API Reference

<details>
<summary><strong>Agent endpoints</strong></summary>

Core async endpoints (returns an `execution_id` immediately):

```bash
# Full build: plan -> execute -> verify
POST /api/v1/execute/async/de-planner.build

# Plan only
POST /api/v1/execute/async/de-planner.plan

# Execute a prebuilt plan
POST /api/v1/execute/async/de-planner.execute

# Resume after interruption
POST /api/v1/execute/async/de-planner.resume_build
```

Monitoring:

```bash
curl http://localhost:8080/api/v1/executions/<execution_id>
```

Every specialist is also callable directly:

`POST /api/v1/execute/async/de-planner.<agent>`

</details>

<details>
<summary><strong>Agent execution flow</strong></summary>

| Agent                    | In -> Out                                            |
| ------------------------ | ---------------------------------------------------- |
| `run_product_manager`    | goal -> PRD (with data schemas, SLAs, quality reqs)  |
| `run_architect`          | PRD -> architecture (data flow, DDL, infra)          |
| `run_tech_lead`          | architecture -> review                               |
| `run_sprint_planner`     | architecture -> issue DAG                            |
| `run_issue_writer`       | issue spec -> detailed issue                         |
| `run_coder`              | issue + worktree -> SQL/dbt/Airflow + tests + commit |
| `run_data_quality_validator` | worktree -> test coverage validation             |
| `run_qa`                 | worktree -> data quality test results                |
| `run_schema_reviewer`    | worktree -> schema compatibility review              |
| `run_code_reviewer`      | worktree -> quality/security/optimization review     |
| `run_qa_synthesizer`     | QA + review -> FIX / APPROVE / BLOCK                 |
| `run_issue_advisor`      | failure context -> adapt / split / accept / escalate |
| `run_replanner`          | build state + failures -> restructured plan          |
| `run_schema_migrator`    | schema change -> multi-phase migration plan          |
| `run_merger`             | branches -> merged output                            |
| `run_integration_tester` | merged repo -> integration results                   |
| `run_verifier`           | repo + PRD -> acceptance pass/fail                   |
| `generate_fix_issues`    | failed criteria -> targeted fix issues               |
| `run_github_pr`          | branch -> push + draft PR                            |

</details>

<details>
<summary><strong>Configuration</strong></summary>

Pass `config` to `build` or `execute`. Full schema: [`de_af/execution/schemas.py`](de_af/execution/schemas.py)

| Key                       | Default         | Description                                           |
| ------------------------- | --------------- | ----------------------------------------------------- |
| `runtime`                 | `"claude_code"` | Model runtime: `"claude_code"` or `"open_code"`       |
| `models`                  | `null`          | Flat role-model map (`default` + role keys below)     |
| `max_coding_iterations`   | `5`             | Inner-loop retry budget                               |
| `max_advisor_invocations` | `2`             | Middle-loop advisor budget                            |
| `max_replans`             | `2`             | Build-level replanning budget                         |
| `enable_issue_advisor`    | `true`          | Enable issue adaptation                               |
| `enable_replanning`       | `true`          | Enable global replanning                              |
| `enable_learning`         | `false`         | Enable cross-issue shared memory (continual learning) |
| `agent_timeout_seconds`   | `2700`          | Per-agent timeout                                     |
| `agent_max_turns`         | `150`           | Tool-use turn budget                                  |

</details>

<details>
<summary><strong>Model Role Keys</strong></summary>

`models` supports:

- `default`
- `pm`, `architect`, `tech_lead`, `sprint_planner`
- `coder`, `qa`, `code_reviewer`, `qa_synthesizer`
- `replan`, `retry_advisor`, `issue_writer`, `issue_advisor`
- `verifier`, `git`, `merger`, `integration_tester`

</details>

<details>
<summary><strong>Resolution order</strong></summary>

`runtime defaults` < `models.default` < `models.<role>`

</details>

<details>
<summary><strong>Artifacts</strong></summary>

```text
.artifacts/
├── plan/           # PRD, architecture, issue specs
├── execution/      # checkpoints, per-issue logs, agent outputs
└── verification/   # acceptance criteria results
```

</details>

## Docker

```bash
cp .env.example .env
# Add your API key: ANTHROPIC_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY
# Optionally add GH_TOKEN for draft PR workflow

docker compose up -d
```

Submit a build:

```bash
# Default (Claude)
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Build incremental dbt model for user events",
    "repo_url": "https://github.com/user/data-platform"
  }
}
JSON

# With open-source runtime (set OPENROUTER_API_KEY in .env)
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "goal": "Add data quality tests to customer dimension",
    "repo_url": "https://github.com/user/data-platform",
    "config": {
      "runtime": "open_code",
      "models": {
        "default": "openrouter/minimax/minimax-m2.5"
      }
    }
  }
}
JSON
```

## GitHub Repo Workflow (Clone -> Build -> Draft PR)

Pass `repo_url` instead of `repo_path` to let DE-AF clone and open a draft PR after execution.

```bash
curl -X POST http://localhost:8080/api/v1/execute/async/de-planner.build \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "input": {
    "repo_url": "https://github.com/user/data-platform",
    "goal": "Implement PII masking for email and SSN columns",
    "config": {
      "runtime": "claude_code",
      "models": {
        "default": "sonnet",
        "coder": "opus",
        "qa": "opus"
      }
    }
  }
}
JSON
```

Requirements:

- `GH_TOKEN` in `.env` with `repo` scope
- Repo access for that token

---

### Also built on AgentField

> **[SWE-AF](https://github.com/Agent-Field/swe-af)** — Autonomous software engineering factory. One API call → full engineering team → shipped code.
>
> **[SEC-AF](https://github.com/Agent-Field/sec-af)** — AI-native security auditor. 250 agents per audit, 94% noise reduction, every finding proven exploitable.
>
> **[Contract-AF](https://github.com/Agent-Field/contract-af)** — Legal contract risk analyzer. Agents spawn agents at runtime. Adversarial review catches what solo LLMs miss.

[All repos →](https://github.com/Agent-Field)

---

DE-AF is built on [AgentField](https://github.com/Agent-Field/agentfield) as a specialized data engineering fork of SWE-AF. [See what else we're building →](https://github.com/Agent-Field)
