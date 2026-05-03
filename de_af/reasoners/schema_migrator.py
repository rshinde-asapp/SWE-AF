"""Schema Migrator agent for DE-AF.

Coordinates multi-phase schema evolution to maintain backward compatibility:
- Phase 1: Add new column (nullable)
- Phase 2: Backfill data
- Phase 3: Enforce constraint (make NOT NULL)
- Phase 4: Update dependent pipelines

Used when PRD specifies schema changes that affect existing tables with downstream dependencies.
"""

from __future__ import annotations

from pydantic import BaseModel


class SchemaMigrationPhase(BaseModel):
    """A single phase in a multi-step schema migration."""

    phase_number: int
    description: str
    sql_changes: list[str]  # DDL statements for this phase
    dbt_changes: list[str]  # dbt model files to modify
    validation_query: str  # SQL to verify phase succeeded
    rollback_sql: str  # How to undo this phase if needed
    depends_on_phases: list[int] = []  # Previous phases that must complete


class SchemaMigrationPlan(BaseModel):
    """Full migration plan for a schema change."""

    table_name: str
    change_description: str  # e.g., "Add customer_tier column with NOT NULL constraint"
    phases: list[SchemaMigrationPhase]
    affected_pipelines: list[str]  # dbt models or Airflow DAGs that depend on this table
    rollback_plan: str  # Overall rollback strategy
    testing_strategy: str  # How to validate each phase


def schema_migrator_prompt(
    table_name: str,
    requested_change: str,
    current_ddl: str,
    downstream_dependencies: list[str],
    repo_path: str,
) -> tuple[str, str]:
    """Build prompts for the schema migrator agent.

    Args:
        table_name: Name of the table being migrated.
        requested_change: Description of desired schema change.
        current_ddl: Current CREATE TABLE statement.
        downstream_dependencies: List of dbt models/pipelines that reference this table.
        repo_path: Path to the repository.

    Returns:
        Tuple of (system_prompt, task_prompt)
    """
    system_prompt = """\
You are a Schema Migration Planner for data platforms. Your job is to decompose
risky schema changes into safe, reversible phases that maintain backward compatibility.

## Migration Principles

1. **Additive first**: Always add new columns as nullable, then backfill, then enforce constraints
2. **Never break readers**: Downstream pipelines must continue working during migration
3. **Atomic phases**: Each phase is a complete, testable unit with validation + rollback
4. **Dependency-aware**: Update dependent pipelines only after schema is stable

## Common Migration Patterns

### Pattern 1: Add NOT NULL Column
- Phase 1: `ALTER TABLE ADD COLUMN new_col VARCHAR(100) NULL`
- Phase 2: Backfill: `UPDATE table SET new_col = <default> WHERE new_col IS NULL`
- Phase 3: Validate: `SELECT COUNT(*) FROM table WHERE new_col IS NULL` → expect 0
- Phase 4: Enforce: `ALTER TABLE ALTER COLUMN new_col SET NOT NULL`

### Pattern 2: Change Column Type
- Phase 1: `ALTER TABLE ADD COLUMN new_col_v2 BIGINT NULL`
- Phase 2: Backfill: `UPDATE table SET new_col_v2 = CAST(old_col AS BIGINT)`
- Phase 3: Update downstream pipelines to reference new_col_v2
- Phase 4: Drop old_col once all pipelines migrated

### Pattern 3: Split Column
- Phase 1: `ALTER TABLE ADD COLUMN first_name VARCHAR(50), last_name VARCHAR(50)`
- Phase 2: Backfill: `UPDATE table SET first_name = SPLIT_PART(full_name, ' ', 1), ...`
- Phase 3: Update pipelines to use first_name, last_name
- Phase 4: Drop full_name once all pipelines migrated

## Your Output

Produce a `SchemaMigrationPlan` with:
- `phases`: List of `SchemaMigrationPhase` objects
- Each phase has: description, SQL changes, validation query, rollback SQL
- `affected_pipelines`: Which dbt models or DAGs need updates
- `testing_strategy`: How to validate each phase (e.g., "run validation query, expect 0 rows")

Make each phase independently testable and reversible.
"""

    task_prompt = f"""\
## Migration Request
- **Table**: `{table_name}`
- **Requested Change**: {requested_change}

## Current Schema
```sql
{current_ddl}
```

## Downstream Dependencies
These pipelines reference this table and must continue working:
{chr(10).join(f"- {dep}" for dep in downstream_dependencies)}

## Repository
{repo_path}

## Your Task
Design a multi-phase migration plan that:
1. Breaks the change into safe, reversible phases
2. Ensures downstream pipelines never break
3. Includes validation queries for each phase
4. Provides rollback SQL for each phase
5. Specifies testing strategy

Output the migration plan as structured `SchemaMigrationPlan`.
"""

    return system_prompt, task_prompt
