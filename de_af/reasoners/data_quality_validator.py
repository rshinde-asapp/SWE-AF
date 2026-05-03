"""Data Quality Validator agent for DE-AF.

Runs after coder to verify data quality test coverage is adequate:
- Critical column coverage (primary keys, foreign keys, amounts, dates)
- Schema validation logic exists (DDL matches architecture)
- Data profiling configured for new tables
- PII detection tests present for sensitive columns
"""

from __future__ import annotations

from de_af.execution.schemas import WorkspaceManifest
from de_af.prompts._utils import workspace_context_block


def data_quality_validator_prompt(
    worktree_path: str,
    coder_result: dict,
    issue: dict,
    iteration_id: str = "",
    project_context: dict | None = None,
    workspace_manifest: WorkspaceManifest | None = None,
    target_repo: str = "",
) -> tuple[str, str]:
    """Build prompts for the data quality validator agent.

    Args:
        worktree_path: Absolute path to the git worktree.
        coder_result: CoderResult dict with files_changed, summary.
        issue: The issue dict with data_validation_strategy field.
        iteration_id: UUID for this iteration's artifact tracking.
        project_context: Dict with prd_summary, architecture_summary, artifact paths.
        workspace_manifest: Optional multi-repo workspace manifest.
        target_repo: The target repository name for this issue.

    Returns:
        Tuple of (system_prompt, task_prompt)
    """
    project_context = project_context or {}

    system_prompt = """\
You are a Data Quality Validator in an autonomous data pipeline factory. Your job
is to verify that the coder implemented adequate data quality tests for the issue.

## Validation Checklist

### 1. Critical Column Coverage
For every table created or modified, verify tests exist for:
- **Primary keys**: unique + not_null tests
- **Foreign keys**: relationships test to parent table
- **Amount/numeric columns**: non-negative constraints, range checks
- **Date columns**: date range validation, not in future (unless valid)
- **Required business columns**: not_null on columns marked required in architecture

### 2. Schema Validation
If DDL or dbt schema.yml was created:
- Column names match architecture spec exactly (case-sensitive)
- Data types match (no VARCHAR where INT expected)
- Nullability correct (NOT NULL on required columns)
- Partition/clustering keys defined as specified

### 3. Data Profiling Setup
For new tables (especially staging/raw):
- Great Expectations suite exists OR
- dbt schema.yml has description + basic tests OR
- SQL profiling script generates row counts, null%, distinct counts

### 4. PII Detection
If table has PII columns (email, ssn, phone, address):
- Regex validation tests exist (e.g., email format check)
- Columns marked as PII in data catalog/schema.yml
- Masking or exclusion documented for non-prod environments

### 5. Framework Usage
Verify data_validation_strategy from issue was followed:
- If "dbt tests" specified → schema.yml tests exist
- If "Great Expectations" specified → expectation suite created
- If "SQL assertions" specified → validation query scripts exist

## Output

Report as structured JSON:
- `validation_passed`: bool (all critical checks passed)
- `missing_tests`: list of critical columns without tests
- `schema_mismatches`: list of schema inconsistencies with architecture
- `pii_gaps`: list of PII columns without validation
- `summary`: brief assessment

If validation fails, suggest specific tests to add (test type, column, expected constraint).
"""

    sections: list[str] = []

    # Inject multi-repo workspace context if present
    ws_block = workspace_context_block(workspace_manifest)
    if ws_block:
        sections.append(ws_block)
    if target_repo:
        sections.append(f"## Target Repository: `{target_repo}`")

    sections.append("## Issue")
    sections.append(f"- **Name**: {issue.get('name', '(unknown)')}")
    sections.append(f"- **Title**: {issue.get('title', '(unknown)')}")

    data_val_strategy = issue.get("data_validation_strategy", "")
    if data_val_strategy:
        sections.append(f"- **Data Validation Strategy**: {data_val_strategy}")

    if project_context:
        arch_path = project_context.get("architecture_path", "")
        if arch_path:
            sections.append(f"\n## Architecture Reference\n`{arch_path}`")

    sections.append(f"\n## Coder's Changes")
    sections.append(f"- **Summary**: {coder_result.get('summary', '(none)')}")
    files = coder_result.get("files_changed", [])
    if files:
        sections.append("- **Files changed**:")
        sections.extend(f"  - `{f}`" for f in files)

    sections.append(f"\n## Working Directory\n`{worktree_path}`")

    sections.append(
        "\n## Your Task\n"
        "1. Read all changed files (SQL, dbt models, schema.yml, Terraform).\n"
        "2. Identify new/modified tables and critical columns.\n"
        "3. Verify data quality tests exist for all critical columns.\n"
        "4. Check schema definitions match architecture spec.\n"
        "5. Validate PII columns have appropriate tests.\n"
        "6. Confirm data_validation_strategy was followed.\n"
        "7. Report validation results with specific gaps listed."
    )

    task_prompt = "\n".join(sections)

    return system_prompt, task_prompt
