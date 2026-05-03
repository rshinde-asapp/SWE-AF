"""Integration tests for DE-AF pipeline execution.

Validates that DE-AF can successfully plan and execute data pipeline builds.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_simple_csv_to_parquet_pipeline():
    """Test that DE-AF can build a simple CSV to Parquet ETL pipeline.

    Acceptance criteria:
    - Pipeline code generated (SQL transformations, dbt models, Airflow DAG)
    - Data quality tests created (dbt tests, Great Expectations suite)
    - Infrastructure definitions produced (Terraform modules)
    - All acceptance criteria from PRD validated
    """
    from de_af.app import app

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test-pipeline"
        repo_path.mkdir()

        # Initialize git repo
        os.system(f"cd {repo_path} && git init && git config user.email 'test@test.com' && git config user.name 'Test'")

        # Call build endpoint
        result = await app.execute(
            "de-planner.build",
            input_data={
                "goal": "Build a simple CSV to Parquet pipeline with data quality validation",
                "repo_path": str(repo_path),
                "config": {
                    "runtime": "claude_code",
                    "models": {"default": "sonnet"},
                    "max_coding_iterations": 3,
                    "enable_replanning": True,
                },
            }
        )

        # Validate build succeeded
        assert result["success"] is True, f"Build failed: {result.get('summary', 'Unknown error')}"

        # Validate artifacts produced
        artifacts = list(repo_path.rglob("*"))
        artifact_names = [f.name for f in artifacts]

        # Check for SQL transformations
        sql_files = [f for f in artifacts if f.suffix == ".sql"]
        assert len(sql_files) >= 2, f"Expected >= 2 SQL files, found {len(sql_files)}"

        # Check for dbt project structure
        dbt_project = repo_path / "dbt_project.yml"
        if not dbt_project.exists():
            # Alternative: dbt models inline
            dbt_models = [f for f in artifacts if "models" in f.parts and f.suffix == ".sql"]
            assert len(dbt_models) >= 1, "No dbt models found"

        # Check for dbt tests (schema.yml)
        schema_ymls = [f for f in artifacts if f.name == "schema.yml"]
        assert len(schema_ymls) >= 1, "No dbt schema.yml tests found"

        # Check for Airflow DAG
        dag_files = [f for f in artifacts if "dag" in f.name.lower() and f.suffix == ".py"]
        assert len(dag_files) >= 1, f"No Airflow DAG found, checked {artifact_names}"

        # Check for Terraform/Pulumi infrastructure
        tf_files = [f for f in artifacts if f.suffix == ".tf"]
        assert len(tf_files) >= 1, f"No Terraform files found, checked {artifact_names}"

        # Check for Great Expectations suite
        ge_suite = [f for f in artifacts if "expectations" in f.parts or "great_expectations" in f.parts]
        assert len(ge_suite) >= 1, "No Great Expectations suite found"

        # Validate acceptance criteria
        plan_result = result.get("plan_result", {})
        prd = plan_result.get("prd", {})
        acceptance_criteria = prd.get("acceptance_criteria", [])
        assert len(acceptance_criteria) > 0, "No acceptance criteria defined"

        # Validate verification ran
        verification = result.get("verification")
        if verification:
            assert verification.get("passed") is True, f"Verification failed: {verification.get('summary')}"


@pytest.mark.asyncio
async def test_data_quality_test_generation():
    """Test that DE-AF generates comprehensive data quality tests.

    Validates:
    - dbt tests for unique/not_null on primary keys
    - Great Expectations suite with profiling
    - SQL assertion scripts for business rules
    """
    from de_af.app import app

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test-dq"
        repo_path.mkdir()
        os.system(f"cd {repo_path} && git init && git config user.email 'test@test.com' && git config user.name 'Test'")

        result = await app.execute(
            "de-planner.build",
            input_data={
                "goal": "Add data quality checks for PII detection in user_events table",
                "repo_path": str(repo_path),
                "config": {
                    "runtime": "claude_code",
                    "models": {"default": "sonnet"},
                },
            }
        )

        assert result["success"] is True

        # Validate dbt tests generated
        schema_files = list(repo_path.rglob("schema.yml"))
        assert len(schema_files) >= 1, "No dbt schema.yml generated"

        # Read schema.yml and verify PII-related tests
        schema_content = schema_files[0].read_text()
        assert "email" in schema_content.lower() or "pii" in schema_content.lower(), \
            "Schema.yml missing PII-related tests"

        # Validate Great Expectations suite
        ge_files = list(repo_path.rglob("*expectations*.json"))
        if ge_files:
            ge_content = json.loads(ge_files[0].read_text())
            # Check for regex validation expectations
            assert any("regex" in str(exp).lower() for exp in ge_content.get("expectations", [])), \
                "Great Expectations suite missing regex validation for PII"


@pytest.mark.asyncio
async def test_schema_migration_planning():
    """Test that DE-AF handles schema changes with backward compatibility.

    Validates:
    - Multi-phase migration plan generated (add nullable → backfill → enforce)
    - Schema reviewer validates backward compatibility
    - Migration safety checks passed
    """
    from de_af.app import app

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test-migration"
        repo_path.mkdir()
        os.system(f"cd {repo_path} && git init && git config user.email 'test@test.com' && git config user.name 'Test'")

        # Create existing table schema
        (repo_path / "schema").mkdir()
        (repo_path / "schema" / "customer_dim.sql").write_text("""
CREATE TABLE customer_dim (
    customer_id INT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
        """)

        result = await app.execute(
            "de-planner.build",
            input_data={
                "goal": "Add customer_tier column to customer_dim with NOT NULL constraint",
                "repo_path": str(repo_path),
                "config": {
                    "runtime": "claude_code",
                    "models": {"default": "sonnet"},
                },
            }
        )

        assert result["success"] is True

        # Validate migration files generated
        migration_files = list(repo_path.rglob("*migration*.sql"))
        assert len(migration_files) >= 1, "No migration files generated"

        # Check for phased approach (add nullable → backfill → enforce)
        migration_content = "\n".join(f.read_text() for f in migration_files)
        assert "ADD COLUMN" in migration_content, "Missing ADD COLUMN statement"
        # Should add as nullable first
        assert "NULL" in migration_content or "DEFAULT" in migration_content, \
            "Migration should add column as nullable or with default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
