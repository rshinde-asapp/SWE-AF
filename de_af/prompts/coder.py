"""Prompt builder for the Coder agent role."""

from __future__ import annotations

from de_af.execution.schemas import WorkspaceManifest
from de_af.prompts._utils import workspace_context_block

SYSTEM_PROMPT = """\
You are a senior data engineer working in a fully autonomous data pipeline coding
pipeline. You receive a well-defined issue with acceptance criteria and must
implement the solution in the codebase.

## Isolation Awareness

You work in an isolated git worktree:
- You have code from all completed prior-level issues (already merged)
- You do NOT have code from sibling issues running in parallel
- The architecture document is your source of truth for all schemas and interfaces
- If you need a table schema or dbt source from the architecture but it's not in
  the codebase yet, implement EXACTLY as the architecture specifies — a sibling
  agent is implementing the other side to the same spec

## Principles

1. **Simplicity first** — write the smallest change that satisfies every
   acceptance criterion. No over-engineering, no speculative features.
2. **One-pass completeness** — every file you create or edit should be complete
   and syntactically valid. Do not leave TODOs or placeholders.
3. **Data quality is mandatory** — for every new table or transformation, create
   corresponding data quality tests (dbt tests, Great Expectations suite, SQL
   assertions). Follow the issue's Testing Strategy exactly.
4. **Schema precision** — match the architecture's DDL exactly. Column names,
   types, nullability, partition keys must be character-for-character identical.
5. **Idempotency by default** — every pipeline component must be safely rerunnable.
   Use MERGE for upserts, DELETE+INSERT for full refresh, or incremental predicates
   for append-only. Document the idempotency mechanism.
6. **Follow existing patterns** — match the project's style: dbt model naming
   (stg_, int_, fct_, dim_), SQL formatting, Airflow DAG structure, file organization.

## Framework-Specific Guidance

### SQL Transformations
- Use CTEs for readability; avoid nested subqueries
- Always specify column lists in SELECT (never `SELECT *` in production code)
- Include comments explaining business logic (not syntax)
- Partition predicates at the top of WHERE clauses for query optimization

### dbt Models
- Model names: `stg_<source>__<entity>`, `int_<entity>`, `fct_<entity>`, `dim_<entity>`
- Materialization: ephemeral for CTEs, view for staging, table/incremental for marts
- Every model needs a `.yml` schema file with column descriptions and tests
- Use `{{ ref('model_name') }}` for dependencies, `{{ source('source', 'table') }}` for raw tables
- Document incremental strategy in model config (unique_key, merge logic)

### Airflow DAGs
- DAG ID: `<domain>_<pipeline>_<frequency>` (e.g., `analytics_customer_360_daily`)
- Use TaskGroups to organize related tasks
- Set proper dependencies with `>>` or `set_upstream()`/`set_downstream()`
- Include SLA monitoring, retries, and timeout configuration
- Tag DAGs for discoverability (`tags=['analytics', 'customer']`)

### Spark Jobs
- Use DataFrames, not RDDs (unless performance critical)
- Partition writes by date column for query performance
- Cache intermediate results only when reused >1 time
- Include broadcast hints for small dimension tables in joins
- Write to staging location, then atomic rename to final path

### Infrastructure as Code (Terraform/Pulumi)
- Module naming: `<resource_type>-<environment>` (e.g., `snowflake-warehouse-prod`)
- Use variables for environment-specific config (never hardcode credentials)
- Output resource identifiers for downstream modules
- Include depends_on for sequencing (database before schema before table)

### Data Quality Tests
- **dbt tests**: Add to schema.yml (unique, not_null, relationships, accepted_values)
- **Great Expectations**: Create suites in `great_expectations/expectations/`
- **Custom SQL assertions**: Use WHERE EXISTS for validation, fail on rows > 0
- Test coverage: critical columns (keys, amounts, dates) + business rules

## Workflow

1. Read the issue description and acceptance criteria carefully.
2. Explore the codebase to understand existing patterns (dbt project structure,
   Airflow DAG conventions, schema locations).
3. Implement the solution: create SQL files, dbt models, Airflow DAGs, Terraform
   modules, or Spark scripts as specified.
4. Create data quality tests: dbt tests in schema.yml, Great Expectations suites,
   or SQL assertion scripts.
5. Run validation: `dbt compile`, `terraform plan`, or syntax checks (if tools available).
6. Review and commit: check `git status`, stage only your intentional changes,
   commit with: `"issue/<name>: <summary>"`. Exclude build artifacts (dbt target/,
   .terraform/, spark-warehouse/).

## Git Rules

- You are working in an isolated worktree (git branch already set up).
- Commit your work when implementation is complete.
- Do NOT push — the merge agent handles that.
- Do NOT create new branches — work on the current branch.
- Do NOT add any `Co-Authored-By` trailers to commit messages.

## Self-Validation

Before committing, run available validation tools:
- dbt: `dbt compile --select <model>` or `dbt run --select <model> --target dev`
- Terraform: `terraform plan`
- SQL linting: `sqlfluff lint <file>` (if available)
- Python: `pytest tests/` for utility scripts

Report:
- `tests_passed`: did validation pass?
- `test_summary`: brief output from validation run

This is informational — the reviewer will independently verify.

## Output

After implementation, report:
- Which files you changed (list of paths)
- A brief summary of what you did
- Whether the implementation is complete
- `tests_passed` and `test_summary` from your self-validation
- `codebase_learnings`: conventions you discovered (dbt model naming, DAG patterns,
  warehouse naming conventions) — these help future coders on this project
- `agent_retro`: briefly note what worked well and any tips for similar issues

## Tools Available

You have full development access:
- READ / WRITE / EDIT files
- BASH for running commands (dbt, terraform, pytest, git)
- GLOB / GREP for searching the codebase\
"""


def coder_task_prompt(
    issue: dict,
    worktree_path: str = "",
    feedback: str = "",
    iteration: int = 1,
    project_context: dict | None = None,
    memory_context: dict | None = None,
    workspace_manifest: WorkspaceManifest | None = None,
    target_repo: str = "",
    architecture: dict | None = None,
) -> str:
    """Build the task prompt for the coder agent.

    Args:
        issue: The issue dict (name, title, description, acceptance_criteria, etc.)
        worktree_path: Absolute path to the git worktree (cwd for the agent).
        feedback: Merged feedback from previous iteration (empty on first pass).
        iteration: Current iteration number (1-based).
        project_context: Dict with artifact paths (prd_path, architecture_path, etc.).
        memory_context: Dict with shared memory (codebase_conventions, failure_patterns,
            dependency_interfaces, bug_patterns) from previous issues.
        workspace_manifest: Optional multi-repo workspace manifest.
        target_repo: The name of the target repository for this issue (multi-repo only).
        architecture: Optional architecture dict (unused, accepted for API compatibility).
    """
    project_context = project_context or {}
    memory_context = memory_context or {}
    sections: list[str] = []

    # Inject multi-repo workspace context if present
    ws_block = workspace_context_block(workspace_manifest)
    if ws_block:
        sections.append(ws_block)

    # Resolve target repo absolute path for multi-repo context
    if target_repo and workspace_manifest is not None:
        repo_obj = next(
            (r for r in workspace_manifest.repos if r.repo_name == target_repo), None
        )
        if repo_obj is not None:
            sections.append(
                f"## Target Repository\n"
                f"- **Name**: {repo_obj.repo_name}\n"
                f"- **Role**: {repo_obj.role}\n"
                f"- **Path**: `{repo_obj.absolute_path}`\n"
                f"- **Branch**: {repo_obj.branch}"
            )

    sections.append("## Issue to Implement")
    sections.append(f"- **Name**: {issue.get('name', '(unknown)')}")
    sections.append(f"- **Title**: {issue.get('title', '(unknown)')}")

    ac = issue.get("acceptance_criteria", [])
    if ac:
        sections.append("- **Acceptance Criteria**:")
        sections.extend(f"  - [ ] {c}" for c in ac)

    deps = issue.get("depends_on", [])
    if deps:
        sections.append(f"- **Dependencies**: {deps}")

    provides = issue.get("provides", [])
    if provides:
        sections.append(f"- **Provides**: {provides}")

    files_create = issue.get("files_to_create", [])
    files_modify = issue.get("files_to_modify", [])
    if files_create:
        sections.append(f"- **Files to create**: {files_create}")
    if files_modify:
        sections.append(f"- **Files to modify**: {files_modify}")

    testing_strategy = issue.get("testing_strategy", "")
    if testing_strategy:
        sections.append(f"- **Testing Strategy**: {testing_strategy}")

    # Sprint planner guidance — proportional testing and review hints
    guidance = issue.get("guidance") or {}
    testing_guidance = guidance.get("testing_guidance", "")
    if testing_guidance:
        sections.append(f"- **Testing Guidance (from sprint planner)**: {testing_guidance}")

    # Project context — file paths only, agents read if needed
    if project_context:
        sections.append("\n## Project Context")
        prd_path = project_context.get("prd_path", "")
        arch_path = project_context.get("architecture_path", "")
        issues_dir = project_context.get("issues_dir", "")
        if prd_path or arch_path or issues_dir:
            sections.append("### Key Files")
            if prd_path:
                sections.append(f"- PRD: `{prd_path}` (read for full requirements)")
            if arch_path:
                sections.append(f"- Architecture: `{arch_path}` (read for design decisions)")
            if issues_dir:
                sections.append(f"- Issue files: `{issues_dir}/` (read your issue file for full details)")

    # Shared memory context — learnings from previous issues
    conventions = memory_context.get("codebase_conventions")
    if conventions:
        sections.append("\n## Codebase Conventions (from prior issues)")
        if isinstance(conventions, dict):
            for k, v in conventions.items():
                sections.append(f"- **{k}**: {v}")
        elif isinstance(conventions, list):
            sections.extend(f"- {c}" for c in conventions)

    failure_patterns = memory_context.get("failure_patterns")
    if failure_patterns:
        sections.append("\n## Known Failure Patterns (avoid these)")
        for fp in failure_patterns[:5]:  # cap at 5 most recent
            sections.append(f"- **{fp.get('pattern', '?')}** ({fp.get('issue', '?')}): {fp.get('description', '')}")

    dep_interfaces = memory_context.get("dependency_interfaces")
    if dep_interfaces:
        sections.append("\n## Dependency Interfaces (completed upstream issues)")
        for iface in dep_interfaces:
            sections.append(f"- **{iface.get('issue', '?')}**: {iface.get('summary', '')}")
            exports = iface.get("exports", [])
            if exports:
                sections.extend(f"  - `{e}`" for e in exports[:5])

    bug_patterns = memory_context.get("bug_patterns")
    if bug_patterns:
        sections.append("\n## Common Bug Patterns in This Build")
        for bp in bug_patterns[:5]:
            sections.append(f"- {bp.get('type', '?')} (seen {bp.get('frequency', 0)}x in {bp.get('modules', [])})")

    # Skills context — domain-specific knowledge for this issue
    skills_context = memory_context.get("skills_context")
    if skills_context:
        sections.append("\n## Applicable Skills")
        sections.append(
            "The following skills are relevant to this issue. "
            "Follow their guidance when implementing:"
        )
        sections.append(skills_context)

    # Failure notes from upstream issues
    failure_notes = issue.get("failure_notes", [])
    if failure_notes:
        sections.append("\n## Upstream Failure Notes")
        sections.extend(f"- {note}" for note in failure_notes)

    # Integration branch context
    integration_branch = issue.get("integration_branch", "")
    if integration_branch:
        sections.append(f"\n## Git Context")
        sections.append(f"- Integration branch: `{integration_branch}`")
        sections.append(f"- Working in worktree: `{worktree_path}`")

    sections.append(f"\n## Working Directory\n`{worktree_path}`")
    sections.append(f"\n## Iteration: {iteration}")

    if feedback:
        sections.append("\n## Feedback from Previous Iteration")
        sections.append(
            "Address ALL of the following issues from the review:\n"
        )
        sections.append(feedback)
        sections.append(
            "\nFix the issues above, then re-commit. Focus on the specific "
            "problems identified — do not rewrite code that is already correct."
        )
    else:
        sections.append(
            "\n## Your Task\n"
            "1. Explore the codebase to understand patterns and context.\n"
            "2. Implement the solution per the acceptance criteria.\n"
            "3. Write or update tests per the Testing Strategy/guidance.\n"
            "4. Run tests and report results (tests_passed, test_summary).\n"
            "5. Commit your changes.\n"
            "6. Report codebase_learnings and agent_retro in your output."
        )

    return "\n".join(sections)
