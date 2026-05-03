"""Tests for Schema Migrator agent."""

from __future__ import annotations

import pytest

from de_af.reasoners.schema_migrator import (
    SchemaMigrationPhase,
    SchemaMigrationPlan,
    schema_migrator_prompt,
)


class TestSchemaMigrationPhase:
    """Unit tests for SchemaMigrationPhase model."""

    def test_phase_instantiation_minimal(self):
        """Test creating a phase with minimal required fields."""
        phase = SchemaMigrationPhase(
            phase_number=1,
            description="Add nullable column",
            sql_changes=["ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL"],
            dbt_changes=["models/staging/stg_users.sql"],
            validation_query="SELECT COUNT(*) FROM users WHERE email IS NOT NULL",
            rollback_sql="ALTER TABLE users DROP COLUMN email",
        )
        assert phase.phase_number == 1
        assert phase.description == "Add nullable column"
        assert len(phase.sql_changes) == 1
        assert phase.depends_on_phases == []

    def test_phase_instantiation_with_dependencies(self):
        """Test creating a phase with dependencies on previous phases."""
        phase = SchemaMigrationPhase(
            phase_number=3,
            description="Enforce NOT NULL constraint",
            sql_changes=["ALTER TABLE users ALTER COLUMN email SET NOT NULL"],
            dbt_changes=[],
            validation_query="SELECT COUNT(*) FROM users WHERE email IS NULL",
            rollback_sql="ALTER TABLE users ALTER COLUMN email DROP NOT NULL",
            depends_on_phases=[1, 2],
        )
        assert phase.phase_number == 3
        assert phase.depends_on_phases == [1, 2]
        assert len(phase.dbt_changes) == 0

    def test_phase_fields_present(self):
        """Test that all expected fields are present in the model."""
        phase = SchemaMigrationPhase(
            phase_number=1,
            description="Test phase",
            sql_changes=["CREATE TABLE test (id INT)"],
            dbt_changes=["models/test.sql"],
            validation_query="SELECT 1",
            rollback_sql="DROP TABLE test",
            depends_on_phases=[],
        )
        # Verify all fields from acceptance criteria are present
        assert hasattr(phase, "phase_number")
        assert hasattr(phase, "description")
        assert hasattr(phase, "sql_changes")
        assert hasattr(phase, "dbt_changes")
        assert hasattr(phase, "validation_query")
        assert hasattr(phase, "rollback_sql")
        assert hasattr(phase, "depends_on_phases")


class TestSchemaMigrationPlan:
    """Unit tests for SchemaMigrationPlan model."""

    def test_plan_instantiation_basic(self):
        """Test creating a migration plan with basic fields."""
        phase1 = SchemaMigrationPhase(
            phase_number=1,
            description="Add column",
            sql_changes=["ALTER TABLE users ADD COLUMN status VARCHAR(50) NULL"],
            dbt_changes=[],
            validation_query="SELECT 1",
            rollback_sql="ALTER TABLE users DROP COLUMN status",
        )
        plan = SchemaMigrationPlan(
            table_name="users",
            change_description="Add status column with NOT NULL constraint",
            phases=[phase1],
            affected_pipelines=["models/marts/fct_user_activity.sql"],
            rollback_plan="Execute rollback SQL for each phase in reverse order",
            testing_strategy="Run validation queries after each phase",
        )
        assert plan.table_name == "users"
        assert len(plan.phases) == 1
        assert len(plan.affected_pipelines) == 1

    def test_plan_with_multiple_phases(self):
        """Test migration plan with multiple sequential phases."""
        phases = [
            SchemaMigrationPhase(
                phase_number=i,
                description=f"Phase {i}",
                sql_changes=[f"-- Phase {i} SQL"],
                dbt_changes=[],
                validation_query="SELECT 1",
                rollback_sql=f"-- Rollback phase {i}",
            )
            for i in range(1, 4)
        ]
        plan = SchemaMigrationPlan(
            table_name="orders",
            change_description="Multi-phase schema change",
            phases=phases,
            affected_pipelines=["dag_orders_daily", "model_fct_orders"],
            rollback_plan="Sequential rollback",
            testing_strategy="Validate each phase independently",
        )
        assert len(plan.phases) == 3
        assert plan.phases[0].phase_number == 1
        assert plan.phases[2].phase_number == 3

    def test_plan_fields_present(self):
        """Test that all expected fields are present in the model."""
        phase = SchemaMigrationPhase(
            phase_number=1,
            description="Test",
            sql_changes=["SELECT 1"],
            dbt_changes=[],
            validation_query="SELECT 1",
            rollback_sql="SELECT 1",
        )
        plan = SchemaMigrationPlan(
            table_name="test_table",
            change_description="Test change",
            phases=[phase],
            affected_pipelines=["pipeline1"],
            rollback_plan="Test rollback",
            testing_strategy="Test validation",
        )
        # Verify all fields from acceptance criteria are present
        assert hasattr(plan, "table_name")
        assert hasattr(plan, "change_description")
        assert hasattr(plan, "phases")
        assert hasattr(plan, "affected_pipelines")
        assert hasattr(plan, "rollback_plan")
        assert hasattr(plan, "testing_strategy")


class TestSchemaMigratorPrompt:
    """Tests for schema_migrator_prompt function."""

    def test_prompt_function_signature(self):
        """Test that function exists with correct signature."""
        system, task = schema_migrator_prompt(
            table_name="users",
            requested_change="Add email column",
            current_ddl="CREATE TABLE users (id INT PRIMARY KEY)",
            downstream_dependencies=["model_fct_users"],
            repo_path="/tmp/repo",
        )
        assert isinstance(system, str)
        assert isinstance(task, str)

    def test_prompt_returns_tuple_of_strings(self):
        """Test that function returns a tuple of two strings."""
        result = schema_migrator_prompt(
            table_name="products",
            requested_change="Add price column",
            current_ddl="CREATE TABLE products (id INT)",
            downstream_dependencies=[],
            repo_path="/path/to/repo",
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(s, str) for s in result)

    def test_system_prompt_includes_migration_principles(self):
        """Test that system prompt includes key migration principles."""
        system, _ = schema_migrator_prompt(
            table_name="test",
            requested_change="test change",
            current_ddl="CREATE TABLE test (id INT)",
            downstream_dependencies=[],
            repo_path="/repo",
        )
        # Check for migration principles from acceptance criteria
        assert "additive first" in system.lower() or "Additive first" in system
        assert "never break readers" in system.lower() or "Never break readers" in system
        assert "atomic phases" in system.lower() or "Atomic phases" in system

    def test_system_prompt_includes_migration_patterns(self):
        """Test that system prompt includes migration patterns."""
        system, _ = schema_migrator_prompt(
            table_name="test",
            requested_change="test",
            current_ddl="CREATE TABLE test (id INT)",
            downstream_dependencies=[],
            repo_path="/repo",
        )
        # Check for migration patterns from acceptance criteria
        assert "add not null column" in system.lower() or "Add NOT NULL Column" in system
        assert "change column type" in system.lower() or "Change Column Type" in system
        assert "split column" in system.lower() or "Split Column" in system

    def test_system_prompt_includes_rollback_strategy(self):
        """Test that system prompt mentions rollback strategy."""
        system, _ = schema_migrator_prompt(
            table_name="test",
            requested_change="test",
            current_ddl="CREATE TABLE test (id INT)",
            downstream_dependencies=[],
            repo_path="/repo",
        )
        assert "rollback" in system.lower()

    def test_system_prompt_includes_validation_query(self):
        """Test that system prompt mentions validation queries."""
        system, _ = schema_migrator_prompt(
            table_name="test",
            requested_change="test",
            current_ddl="CREATE TABLE test (id INT)",
            downstream_dependencies=[],
            repo_path="/repo",
        )
        assert "validation query" in system.lower() or "validation" in system.lower()

    def test_task_prompt_includes_table_name(self):
        """Test that task prompt includes the table name."""
        _, task = schema_migrator_prompt(
            table_name="customers",
            requested_change="Add column",
            current_ddl="CREATE TABLE customers (id INT)",
            downstream_dependencies=[],
            repo_path="/repo",
        )
        assert "customers" in task

    def test_task_prompt_includes_requested_change(self):
        """Test that task prompt includes the requested change."""
        _, task = schema_migrator_prompt(
            table_name="orders",
            requested_change="Add priority column with default value",
            current_ddl="CREATE TABLE orders (id INT)",
            downstream_dependencies=[],
            repo_path="/repo",
        )
        assert "Add priority column with default value" in task

    def test_task_prompt_includes_current_ddl(self):
        """Test that task prompt includes the current DDL."""
        ddl = "CREATE TABLE inventory (id INT PRIMARY KEY, name VARCHAR(100))"
        _, task = schema_migrator_prompt(
            table_name="inventory",
            requested_change="test",
            current_ddl=ddl,
            downstream_dependencies=[],
            repo_path="/repo",
        )
        assert ddl in task

    def test_task_prompt_includes_downstream_dependencies(self):
        """Test that task prompt includes downstream dependencies."""
        deps = ["model_fct_sales", "dag_daily_sales", "model_dim_product"]
        _, task = schema_migrator_prompt(
            table_name="sales",
            requested_change="test",
            current_ddl="CREATE TABLE sales (id INT)",
            downstream_dependencies=deps,
            repo_path="/repo",
        )
        for dep in deps:
            assert dep in task

    def test_task_prompt_includes_repo_path(self):
        """Test that task prompt includes the repository path."""
        repo = "/home/user/data-warehouse"
        _, task = schema_migrator_prompt(
            table_name="test",
            requested_change="test",
            current_ddl="CREATE TABLE test (id INT)",
            downstream_dependencies=[],
            repo_path=repo,
        )
        assert repo in task
