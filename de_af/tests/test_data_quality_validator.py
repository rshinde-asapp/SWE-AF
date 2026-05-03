"""Tests for the data quality validator prompt builder."""

import pytest
from de_af.reasoners.data_quality_validator import data_quality_validator_prompt
from de_af.execution.schemas import WorkspaceManifest, WorkspaceRepo


class TestDataQualityValidatorPrompt:
    """Test data_quality_validator_prompt function."""

    def test_data_quality_validator_prompt_builds_task_prompt(self):
        """Test that data_quality_validator_prompt builds task prompt with issue details."""
        issue = {
            "name": "issue-123-add-user-table",
            "title": "Add users table with PII validation",
            "data_validation_strategy": "dbt tests in schema.yml for unique/not_null on primary keys"
        }
        coder_result = {
            "files_changed": ["dbt/models/users.sql", "dbt/models/schema.yml"],
            "summary": "Created users table with dbt tests"
        }
        worktree_path = "/tmp/worktree-123"
        project_context = {
            "architecture_path": "/tmp/architecture.md"
        }

        system, task = data_quality_validator_prompt(
            worktree_path=worktree_path,
            coder_result=coder_result,
            issue=issue,
            project_context=project_context
        )

        # Verify system prompt contains validation checklist sections
        assert "Critical Column Coverage" in system
        assert "Schema Validation" in system
        assert "Data Profiling Setup" in system
        assert "PII Detection" in system
        assert "Framework Usage" in system

        # Verify task prompt contains issue details
        assert "issue-123-add-user-table" in task
        assert "Add users table with PII validation" in task
        assert "dbt tests in schema.yml for unique/not_null on primary keys" in task
        assert "dbt/models/users.sql" in task
        assert "dbt/models/schema.yml" in task
        assert "/tmp/worktree-123" in task
        assert "/tmp/architecture.md" in task

    def test_data_quality_validator_prompt_with_empty_coder_result(self):
        """Test task prompt with empty coder_result."""
        issue = {"name": "issue-456", "title": "Test issue"}
        coder_result = {}
        worktree_path = "/tmp/test"

        system, task = data_quality_validator_prompt(
            worktree_path=worktree_path,
            coder_result=coder_result,
            issue=issue
        )

        assert "Critical Column Coverage" in system
        assert "issue-456" in task
        assert "Test issue" in task
        assert "(none)" in task  # Default for missing summary

    def test_data_quality_validator_prompt_with_missing_data_validation_strategy(self):
        """Test task prompt without data_validation_strategy field."""
        issue = {"name": "issue-789", "title": "Schema change"}
        coder_result = {"files_changed": ["schema.sql"]}
        worktree_path = "/tmp/test"

        system, task = data_quality_validator_prompt(
            worktree_path=worktree_path,
            coder_result=coder_result,
            issue=issue
        )

        assert "Critical Column Coverage" in system
        assert "issue-789" in task
        # Should not crash when data_validation_strategy is missing
        assert "Data Validation Strategy" not in task

    def test_data_quality_validator_prompt_with_none_values(self):
        """Test handling of None values in issue dict."""
        issue = {}  # Empty dict, no name or title
        coder_result = {}  # No files_changed
        worktree_path = "/tmp/test"

        system, task = data_quality_validator_prompt(
            worktree_path=worktree_path,
            coder_result=coder_result,
            issue=issue
        )

        assert "Critical Column Coverage" in system
        assert "(unknown)" in task  # Default value for missing name/title

    def test_data_quality_validator_prompt_with_multi_repo_workspace(self):
        """Test task prompt with multi-repo workspace manifest."""
        workspace_manifest = WorkspaceManifest(
            workspace_root="/tmp/ws",
            primary_repo_name="data-pipeline",
            repos=[
                WorkspaceRepo(
                    repo_name="data-pipeline",
                    repo_url="https://github.com/test/data-pipeline",
                    role="primary",
                    absolute_path="/tmp/ws/data-pipeline",
                    branch="main"
                ),
                WorkspaceRepo(
                    repo_name="shared-dbt",
                    repo_url="https://github.com/test/shared-dbt",
                    role="dependency",
                    absolute_path="/tmp/ws/shared-dbt",
                    branch="main"
                )
            ]
        )
        issue = {"name": "issue-999", "title": "Multi-repo test"}
        coder_result = {"files_changed": ["pipeline.py"]}
        worktree_path = "/tmp/test"

        system, task = data_quality_validator_prompt(
            worktree_path=worktree_path,
            coder_result=coder_result,
            issue=issue,
            workspace_manifest=workspace_manifest,
            target_repo="data-pipeline"
        )

        assert "Critical Column Coverage" in system
        assert "Workspace Repositories" in task
        assert "data-pipeline" in task
        assert "shared-dbt" in task
        assert "Target Repository: `data-pipeline`" in task

    def test_data_quality_validator_prompt_with_target_repo_only(self):
        """Test task prompt with target_repo but no workspace manifest."""
        issue = {"name": "issue-111", "title": "Single repo with target"}
        coder_result = {"files_changed": ["test.sql"]}
        worktree_path = "/tmp/test"

        system, task = data_quality_validator_prompt(
            worktree_path=worktree_path,
            coder_result=coder_result,
            issue=issue,
            target_repo="my-repo"
        )

        assert "Critical Column Coverage" in system
        assert "Target Repository: `my-repo`" in task


class TestSystemPromptContent:
    """Test SYSTEM_PROMPT content validation."""

    def test_system_prompt_has_all_validation_sections(self):
        """Test SYSTEM_PROMPT includes all 5 validation checklist sections."""
        _, _ = data_quality_validator_prompt(
            worktree_path="/tmp/test",
            coder_result={},
            issue={}
        )
        # Get system prompt
        system, _ = data_quality_validator_prompt(
            worktree_path="/tmp/test",
            coder_result={},
            issue={}
        )

        validation_sections = [
            "Critical Column Coverage",
            "Schema Validation",
            "Data Profiling Setup",
            "PII Detection",
            "Framework Usage"
        ]

        for section in validation_sections:
            assert section in system, f"Missing validation section: {section}"

    def test_system_prompt_has_critical_column_checks(self):
        """Test SYSTEM_PROMPT defines critical column checks."""
        system, _ = data_quality_validator_prompt(
            worktree_path="/tmp/test",
            coder_result={},
            issue={}
        )

        critical_checks = [
            "Primary keys",
            "Foreign keys",
            "Amount/numeric columns",
            "Date columns",
            "Required business columns"
        ]

        for check in critical_checks:
            assert check in system, f"Missing critical column check: {check}"

    def test_system_prompt_has_schema_validation_criteria(self):
        """Test SYSTEM_PROMPT defines schema validation criteria."""
        system, _ = data_quality_validator_prompt(
            worktree_path="/tmp/test",
            coder_result={},
            issue={}
        )

        schema_criteria = [
            "Column names match architecture spec exactly",
            "Data types match",
            "Nullability correct",
            "Partition/clustering keys"
        ]

        for criterion in schema_criteria:
            assert criterion in system, f"Missing schema criterion: {criterion}"

    def test_system_prompt_has_pii_detection_requirements(self):
        """Test SYSTEM_PROMPT defines PII detection requirements."""
        system, _ = data_quality_validator_prompt(
            worktree_path="/tmp/test",
            coder_result={},
            issue={}
        )

        pii_requirements = [
            "email",
            "ssn",
            "phone",
            "Regex validation tests",
            "Columns marked as PII"
        ]

        for req in pii_requirements:
            assert req in system, f"Missing PII requirement: {req}"

    def test_system_prompt_has_framework_checks(self):
        """Test SYSTEM_PROMPT mentions data quality frameworks."""
        system, _ = data_quality_validator_prompt(
            worktree_path="/tmp/test",
            coder_result={},
            issue={}
        )

        frameworks = [
            "dbt tests",
            "Great Expectations",
            "SQL assertions"
        ]

        for framework in frameworks:
            assert framework in system, f"Missing framework: {framework}"

    def test_system_prompt_has_structured_output_fields(self):
        """Test SYSTEM_PROMPT defines structured output fields."""
        system, _ = data_quality_validator_prompt(
            worktree_path="/tmp/test",
            coder_result={},
            issue={}
        )

        output_fields = [
            "validation_passed",
            "missing_tests",
            "schema_mismatches",
            "pii_gaps"
        ]

        for field in output_fields:
            assert field in system, f"Missing output field: {field}"


class TestFunctionSignature:
    """Test function signature compliance."""

    def test_data_quality_validator_prompt_signature(self):
        """Test data_quality_validator_prompt has correct signature."""
        import inspect

        sig = inspect.signature(data_quality_validator_prompt)
        params = list(sig.parameters.keys())
        return_annotation = sig.return_annotation

        # Verify parameters
        expected_params = [
            'worktree_path',
            'coder_result',
            'issue',
            'iteration_id',
            'project_context',
            'workspace_manifest',
            'target_repo'
        ]
        assert params == expected_params, \
            f"Expected params {expected_params}, got {params}"

        # Verify return type
        assert str(return_annotation) == 'tuple[str, str]', \
            f"Expected return type tuple[str, str], got {return_annotation}"

    def test_data_quality_validator_prompt_returns_tuple(self):
        """Test data_quality_validator_prompt returns tuple of two strings."""
        issue = {"name": "test", "title": "test"}
        coder_result = {"files_changed": []}
        worktree_path = "/tmp/test"

        result = data_quality_validator_prompt(
            worktree_path=worktree_path,
            coder_result=coder_result,
            issue=issue
        )

        assert isinstance(result, tuple), "Should return a tuple"
        assert len(result) == 2, "Should return tuple of length 2"
        assert isinstance(result[0], str), "First element should be string (system prompt)"
        assert isinstance(result[1], str), "Second element should be string (task prompt)"

    def test_data_quality_validator_prompt_with_all_parameters(self):
        """Test data_quality_validator_prompt with all parameters provided."""
        workspace_manifest = WorkspaceManifest(
            workspace_root="/tmp",
            primary_repo_name="test-repo",
            repos=[
                WorkspaceRepo(
                    repo_name="test-repo",
                    repo_url="https://github.com/test/test-repo",
                    role="primary",
                    absolute_path="/tmp/test-repo",
                    branch="main"
                )
            ]
        )
        issue = {
            "name": "issue-test",
            "title": "Test Issue",
            "data_validation_strategy": "dbt tests"
        }
        coder_result = {
            "files_changed": ["test.sql"],
            "summary": "Test summary"
        }
        worktree_path = "/tmp/worktree"
        project_context = {
            "architecture_path": "/tmp/arch.md",
            "prd_path": "/tmp/prd.md"
        }

        system, task = data_quality_validator_prompt(
            worktree_path=worktree_path,
            coder_result=coder_result,
            issue=issue,
            iteration_id="test-iteration-123",
            project_context=project_context,
            workspace_manifest=workspace_manifest,
            target_repo="test-repo"
        )

        # Verify all components are present
        assert isinstance(system, str)
        assert isinstance(task, str)
        assert len(system) > 0
        assert len(task) > 0
        assert "issue-test" in task
        assert "Test Issue" in task
        assert "dbt tests" in task
        assert "test.sql" in task
        assert "/tmp/arch.md" in task
