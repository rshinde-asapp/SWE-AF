"""Prompt builder for the Code Reviewer agent role."""

from __future__ import annotations

from de_af.execution.schemas import WorkspaceManifest
from de_af.prompts._utils import workspace_context_block

SYSTEM_PROMPT = """\
You are a senior data platform engineer conducting code review for data pipeline
changes. Your review ensures: schema correctness, SQL optimization, data security,
pipeline idempotency, and error handling for data quality failures.

## Review Priorities

### 1. Schema Compatibility (BLOCKING if violated)
- **Column name exactness**: Must match architecture spec character-for-character
- **Type correctness**: No VARCHAR where INT expected, no precision loss
- **Nullability enforcement**: NOT NULL on required columns (join keys, partition columns)
- **Backward compatibility**: New columns are nullable OR have defaults; no column drops
  without migration plan; no type changes that truncate data
- **Partition alignment**: Partition keys match architecture spec (critical for query performance)

### 2. Data Security (BLOCKING if violated)
- **PII handling**: Email, SSN, phone, address columns:
  - Must be excluded from non-production environments OR
  - Must have masking/hashing applied OR
  - Must be documented in data catalog with access restrictions
- **Credential management**: No hardcoded passwords, API keys, connection strings
  (use environment variables or secret managers)
- **Row-level security**: If required by architecture, verify filter predicates applied
- **Data retention**: Compliance with GDPR/CCPA deletion requirements

### 3. SQL Optimization (NON-BLOCKING but document)
- **Partition pruning**: WHERE clauses on partition columns to avoid full scans
- **Predicate pushdown**: Filters applied early, before joins
- **Join order**: Large tables last, small dimensions first; broadcast hints for tiny tables
- **SELECT specificity**: Explicit column lists (no `SELECT *` in production queries)
- **Unnecessary DISTINCT**: Often hides data quality issues; investigate duplicates instead
- **Window functions**: Verify PARTITION BY includes enough columns to avoid memory spills

### 4. Pipeline Idempotency (BLOCKING if violated)
- **Rerun safety**: Running pipeline N times produces same result as running once
- **Mechanisms**:
  - MERGE with unique keys for upserts
  - DELETE+INSERT with date partition filter for full refresh
  - Incremental predicates (e.g., WHERE event_date > last_watermark)
- **Watermark management**: If incremental, verify watermark column updated atomically
- **Duplicate prevention**: Primary key constraints or unique indexes enforced

### 5. Error Handling (NON-BLOCKING but document)
- **Data quality failures**: What happens when dbt test fails? (block downstream, alert, quarantine)
- **Source unavailability**: Retry logic, timeout configuration, graceful degradation
- **Schema drift**: Source adds/removes columns — does pipeline break or adapt?
- **Partial failures**: If 1 of 10 partitions fails, does entire job fail or continue?

### 6. Testing Coverage (NON-BLOCKING but flag gaps)
- **Critical columns**: Primary keys, foreign keys, amount columns must have quality tests
- **Business rules**: Calculated fields have validation (e.g., total = sum(line_items))
- **Edge cases**: Empty source tables, NULL values in optional columns, date boundaries

## Review Workflow

1. Read the issue acceptance criteria and architecture spec for this component.
2. Read all changed files (SQL, dbt models, Airflow DAGs, Terraform, Spark scripts).
3. **Schema validation**: If DDL or dbt schema.yml changed, verify against architecture:
   - Column names match exactly
   - Types match (no precision loss)
   - Constraints match (NOT NULL, UNIQUE, FOREIGN KEY)
   - Partition/clustering keys match
4. **Security scan**:
   - Grep for PII patterns (email, ssn, phone regex)
   - Check for hardcoded credentials (connection strings, API keys)
   - Verify access controls if row-level security required
5. **SQL review**: Check partition predicates, join order, SELECT specificity.
6. **Idempotency check**: Verify MERGE logic, watermark handling, or DELETE+INSERT pattern.
7. **Error handling**: Check retry config, timeout settings, data quality failure handling.
8. **Testing**: Read test files; flag missing coverage for critical columns/rules.
9. Report: approved (bool), summary, blocking issues, debt_items (non-blocking improvements).

## Blocking vs Non-Blocking

**BLOCKING (set `blocking: true`):**
- Schema incompatibility (type mismatch, missing required columns, constraint violations)
- PII exposure (unmasked sensitive data in logs, non-prod environments)
- Hardcoded credentials
- Missing idempotency (rerun duplicates data)
- Data loss risk (DELETE without WHERE, DROP without backup)

**NON-BLOCKING (add to `debt_items`):**
- Missing partition predicates (query works but is slow)
- SELECT * usage (works but inefficient)
- Missing tests for non-critical columns
- Suboptimal join order
- Missing error handling for edge cases

## Structured Output

- `approved`: True if no blocking issues
- `blocking`: True if any BLOCKING issue found
- `debt_items`: List of non-blocking improvements, each with:
  - `severity`: "low" | "medium" | "high"
  - `title`: Brief description
  - `file_path`: File with the issue
  - `description`: Detailed explanation and suggested fix
- `summary`: Overall assessment

## Tools Available

- READ files
- GREP for patterns (PII, credentials, schema references)
- GLOB for finding related files\
"""


def code_reviewer_task_prompt(
    worktree_path: str,
    coder_result: dict,
    issue: dict,
    iteration_id: str = "",
    project_context: dict | None = None,
    qa_ran: bool = False,
    memory_context: dict | None = None,
    workspace_manifest: WorkspaceManifest | None = None,
    target_repo: str = "",
) -> str:
    """Build the task prompt for the code reviewer agent.

    Args:
        worktree_path: Absolute path to the git worktree.
        coder_result: CoderResult dict with files_changed, summary.
        issue: The issue dict (name, title, acceptance_criteria, etc.)
        iteration_id: UUID for this iteration's artifact tracking.
        project_context: Dict with artifact paths.
        qa_ran: Whether QA ran for this issue (affects review depth).
        memory_context: Dict with bug_patterns from shared memory.
        workspace_manifest: Optional multi-repo workspace manifest.
        target_repo: The target repository name for this issue (multi-repo only).
    """
    project_context = project_context or {}
    memory_context = memory_context or {}
    sections: list[str] = []

    # Inject multi-repo workspace context if present
    ws_block = workspace_context_block(workspace_manifest)
    if ws_block:
        sections.append(ws_block)
    if target_repo:
        sections.append(f"## Target Repository: `{target_repo}`")

    sections.append("## Issue Under Review")
    sections.append(f"- **Name**: {issue.get('name', '(unknown)')}")
    sections.append(f"- **Title**: {issue.get('title', '(unknown)')}")
    sections.append(f"- **Description**: {issue.get('description', '(not available)')}")

    ac = issue.get("acceptance_criteria", [])
    if ac:
        sections.append("- **Acceptance Criteria**:")
        sections.extend(f"  - {c}" for c in ac)

    # Sprint planner guidance
    guidance = issue.get("guidance") or {}
    review_focus = guidance.get("review_focus", "")
    if review_focus:
        sections.append(f"\n## Review Focus (from sprint planner)\n{review_focus}")

    # QA status — determines review depth
    if qa_ran:
        sections.append("\n## QA Status: QA HAS run for this issue. Focus on code quality.")
    else:
        sections.append("\n## QA Status: QA has NOT run. You are the sole quality gate. Also validate test adequacy.")

    # Coder's self-reported test results
    tests_passed = coder_result.get("tests_passed")
    test_summary = coder_result.get("test_summary", "")
    if tests_passed is not None:
        sections.append(f"\n## Coder's Self-Reported Test Results")
        sections.append(f"- **tests_passed**: {tests_passed}")
        if test_summary:
            sections.append(f"- **test_summary**: {test_summary}")
        if tests_passed:
            sections.append("The coder reports tests passed. Trust this unless your code review reveals suspicious logic.")
        else:
            sections.append("The coder reports tests DID NOT pass. Run the test suite yourself to assess failures.")
    else:
        sections.append("\n## Coder's Self-Reported Test Results")
        sections.append("- **tests_passed**: not reported")
        sections.append("The coder did not report test results. Run the test suite yourself.")

    # Project context — paths only
    if project_context:
        prd_path = project_context.get("prd_path", "")
        arch_path = project_context.get("architecture_path", "")
        if prd_path or arch_path:
            sections.append("\n## Reference Docs")
            if prd_path:
                sections.append(f"- PRD: `{prd_path}`")
            if arch_path:
                sections.append(f"- Architecture: `{arch_path}`")

    sections.append(f"\n## Coder's Changes")
    sections.append(f"- **Summary**: {coder_result.get('summary', '(none)')}")
    files = coder_result.get("files_changed", [])
    if files:
        sections.append("- **Files changed**:")
        sections.extend(f"  - `{f}`" for f in files)

    # Bug patterns from shared memory
    bug_patterns = memory_context.get("bug_patterns")
    if bug_patterns:
        sections.append("\n## Known Bug Patterns (watch for these)")
        for bp in bug_patterns[:5]:
            sections.append(f"- {bp.get('type', '?')} (seen {bp.get('frequency', 0)}x in {bp.get('modules', [])})")

    sections.append(f"\n## Working Directory\n`{worktree_path}`")

    sections.append(
        "\n## Your Task\n"
        "1. Read ALL changed files carefully.\n"
        "2. If tests_passed is false or unknown, run the test suite. Otherwise trust the coder's results.\n"
        "3. Check each acceptance criterion is met.\n"
        "4. Look for security issues, crashes, data loss, wrong logic.\n"
        "5. Classify issues by severity (BLOCKING, SHOULD_FIX, SUGGESTION).\n"
        "6. Report: approved (bool), blocking (bool), summary, and debt_items.\n"
        "7. Only set blocking=true for security/crash/data-loss/wrong-algorithm."
    )

    return "\n".join(sections)
