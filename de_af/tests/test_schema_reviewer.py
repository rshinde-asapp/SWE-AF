"""Tests for the schema reviewer prompt builder."""

import pytest
from de_af.prompts.schema_reviewer import SYSTEM_PROMPT, schema_reviewer_prompt


class TestSchemaReviewerPrompt:
    """Test schema_reviewer_prompt function."""

    def test_schema_reviewer_prompt_builds_task_prompt(self):
        """Test that schema_reviewer_prompt builds task prompt with issue details."""
        issue = {
            "name": "issue-123-add-user-table",
            "title": "Add users table schema"
        }
        coder_result = {
            "files_changed": ["sql/users.sql", "dbt/models/schema.yml"]
        }
        worktree_path = "/tmp/worktree-123"
        architecture_summary = "Users table with id, email, created_at"

        system, task = schema_reviewer_prompt(
            issue, coder_result, worktree_path, architecture_summary
        )

        # Verify system prompt is returned
        assert system == SYSTEM_PROMPT

        # Verify task prompt contains issue details
        assert "issue-123-add-user-table" in task
        assert "Add users table schema" in task
        assert "sql/users.sql" in task
        assert "dbt/models/schema.yml" in task
        assert "/tmp/worktree-123" in task
        assert "Users table with id, email, created_at" in task

    def test_schema_reviewer_prompt_with_empty_files(self):
        """Test task prompt with empty files_changed list."""
        issue = {"name": "issue-456", "title": "Test issue"}
        coder_result = {"files_changed": []}
        worktree_path = "/tmp/test"

        system, task = schema_reviewer_prompt(issue, coder_result, worktree_path)

        assert system == SYSTEM_PROMPT
        assert "issue-456" in task
        assert "Test issue" in task

    def test_schema_reviewer_prompt_with_missing_architecture(self):
        """Test task prompt without architecture_summary."""
        issue = {"name": "issue-789", "title": "Schema change"}
        coder_result = {"files_changed": ["schema.sql"]}
        worktree_path = "/tmp/test"

        system, task = schema_reviewer_prompt(issue, coder_result, worktree_path)

        assert system == SYSTEM_PROMPT
        assert "Read architecture document" in task

    def test_schema_reviewer_prompt_with_none_values(self):
        """Test handling of None values in issue dict."""
        issue = {}  # Empty dict, no name or title
        coder_result = {}  # No files_changed
        worktree_path = "/tmp/test"

        system, task = schema_reviewer_prompt(issue, coder_result, worktree_path)

        assert system == SYSTEM_PROMPT
        assert "(unknown)" in task  # Default value for missing name/title


class TestSystemPromptContent:
    """Test SYSTEM_PROMPT content validation."""

    def test_system_prompt_has_all_focus_areas(self):
        """Test SYSTEM_PROMPT includes all 5 review focus areas."""
        focus_areas = [
            "backward compatibility",
            "migration safety",
            "index coverage",
            "partitioning strategy",
            "data type precision"
        ]

        for area in focus_areas:
            assert area.lower() in SYSTEM_PROMPT.lower(), \
                f"Missing focus area: {area}"

    def test_system_prompt_has_blocking_criteria(self):
        """Test SYSTEM_PROMPT defines blocking criteria."""
        blocking_items = [
            "column drops",
            "type narrowing",
            "constraint enforcement without validation",
            "large table DDL",
            "FLOAT for currency"
        ]

        for item in blocking_items:
            assert item.lower() in SYSTEM_PROMPT.lower(), \
                f"Missing blocking criterion: {item}"

    def test_system_prompt_has_non_blocking_criteria(self):
        """Test SYSTEM_PROMPT defines non-blocking criteria."""
        non_blocking_items = [
            "missing indexes",
            "suboptimal partition",
            "VARCHAR(MAX)"
        ]

        for item in non_blocking_items:
            assert item.lower() in SYSTEM_PROMPT.lower(), \
                f"Missing non-blocking criterion: {item}"

    def test_system_prompt_has_8_step_workflow(self):
        """Test SYSTEM_PROMPT documents 8-step review workflow."""
        import re

        # Extract Review Workflow section
        workflow_section = SYSTEM_PROMPT.split('## Review Workflow')[1].split('## Blocking')[0]

        # Count numbered steps
        steps = re.findall(r'^\d+\.', workflow_section, re.MULTILINE)

        assert len(steps) == 8, f"Expected 8 workflow steps, found {len(steps)}"

    def test_system_prompt_has_structured_output_fields(self):
        """Test SYSTEM_PROMPT defines structured output fields."""
        output_fields = [
            "approved",
            "blocking",
            "schema_risks",
            "migration_warnings",
            "debt_items",
            "summary"
        ]

        for field in output_fields:
            assert field in SYSTEM_PROMPT, \
                f"Missing output field: {field}"

    def test_system_prompt_mentions_backward_compatibility_checks(self):
        """Test backward compatibility validation criteria."""
        compat_checks = [
            "nullable OR have defaults",
            "no column drops",
            "no type narrowing",
            "no constraint tightening"
        ]

        for check in compat_checks:
            assert check.lower() in SYSTEM_PROMPT.lower(), \
                f"Missing compatibility check: {check}"

    def test_system_prompt_mentions_migration_safety_checks(self):
        """Test migration safety criteria."""
        safety_checks = [
            "non-blocking",
            "validated before enforcement",
            "CONCURRENTLY"
        ]

        for check in safety_checks:
            assert check.lower() in SYSTEM_PROMPT.lower(), \
                f"Missing safety check: {check}"


class TestFunctionSignature:
    """Test function signature compliance."""

    def test_schema_reviewer_prompt_signature(self):
        """Test schema_reviewer_prompt has correct signature."""
        import inspect

        sig = inspect.signature(schema_reviewer_prompt)
        params = list(sig.parameters.keys())
        return_annotation = sig.return_annotation

        # Verify parameters
        expected_params = ['issue', 'coder_result', 'worktree_path', 'architecture_summary']
        assert params == expected_params, \
            f"Expected params {expected_params}, got {params}"

        # Verify return type
        assert str(return_annotation) == 'tuple[str, str]', \
            f"Expected return type tuple[str, str], got {return_annotation}"

    def test_schema_reviewer_prompt_returns_tuple(self):
        """Test schema_reviewer_prompt returns tuple of two strings."""
        issue = {"name": "test", "title": "test"}
        coder_result = {"files_changed": []}
        worktree_path = "/tmp/test"

        result = schema_reviewer_prompt(issue, coder_result, worktree_path)

        assert isinstance(result, tuple), "Should return a tuple"
        assert len(result) == 2, "Should return tuple of length 2"
        assert isinstance(result[0], str), "First element should be string"
        assert isinstance(result[1], str), "Second element should be string"
