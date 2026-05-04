"""Integration tests for skill-learner in coding loop and coder prompt."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest

from de_af.execution.coding_loop import _inject_skills_context
from de_af.prompts.coder import coder_task_prompt


# ---------------------------------------------------------------------------
# Integration tests for coding_loop.py
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inject_skills_context_populates_memory_context(tmp_path, monkeypatch):
    """Test that _inject_skills_context calls run_skill_learner and populates memory_context."""
    # Setup test skills directory
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Mock call_fn to return a skill result
    mock_call_fn = AsyncMock(
        return_value={
            "skills_context": "### fastapi\n> FastAPI best practices...",
            "discovery_summary": "Found 1 skill, matched 1 (fastapi)",
        }
    )

    # Mock config with skill_learner_model
    class MockConfig:
        skill_learner_model = "haiku"
        ai_provider = "claude"

    memory_context = {"codebase_conventions": {"note_0": "Use pytest"}}
    issue = {"name": "test-issue", "files_to_modify": ["src/api.py"]}

    result = await _inject_skills_context(
        memory_context=memory_context,
        skills_dir=str(skills_dir),
        issue=issue,
        call_fn=mock_call_fn,
        node_id="test_node",
        config=MockConfig(),
        note_fn=None,
    )

    # Verify call_fn was called with correct parameters
    mock_call_fn.assert_called_once()
    call_args = mock_call_fn.call_args
    assert call_args[0][0] == "test_node.run_skill_learner"
    assert call_args[1]["skills_dir"] == str(skills_dir)
    assert call_args[1]["issue"] == issue
    assert call_args[1]["model"] == "haiku"
    assert call_args[1]["ai_provider"] == "claude"

    # Verify skills_context was added to memory_context
    assert "skills_context" in result
    assert result["skills_context"] == "### fastapi\n> FastAPI best practices..."
    # Verify original memory_context is preserved
    assert "codebase_conventions" in result
    assert result["codebase_conventions"] == {"note_0": "Use pytest"}


@pytest.mark.asyncio
async def test_inject_skills_context_no_skills_dir(tmp_path):
    """Test graceful handling when skills directory doesn't exist."""
    skills_dir = tmp_path / "skills"  # Does not exist

    # Mock call_fn (should not be called)
    mock_call_fn = AsyncMock()

    class MockConfig:
        skill_learner_model = "haiku"
        ai_provider = "claude"

    memory_context = {"codebase_conventions": {"note_0": "Use pytest"}}
    issue = {"name": "test-issue"}

    result = await _inject_skills_context(
        memory_context=memory_context,
        skills_dir=str(skills_dir),
        issue=issue,
        call_fn=mock_call_fn,
        node_id="test_node",
        config=MockConfig(),
        note_fn=None,
    )

    # Verify call_fn was NOT called
    mock_call_fn.assert_not_called()

    # Verify memory_context is unchanged
    assert result == memory_context
    assert "skills_context" not in result


@pytest.mark.asyncio
async def test_inject_skills_context_handles_exception(tmp_path):
    """Test that exceptions from run_skill_learner don't halt the build."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Mock call_fn to raise an exception
    mock_call_fn = AsyncMock(side_effect=Exception("Skill learner error"))

    class MockConfig:
        skill_learner_model = "haiku"
        ai_provider = "claude"

    memory_context = {"codebase_conventions": {"note_0": "Use pytest"}}
    issue = {"name": "test-issue"}

    # Mock note_fn to capture log messages
    notes = []

    def mock_note_fn(msg, tags=None):
        notes.append({"msg": msg, "tags": tags})

    result = await _inject_skills_context(
        memory_context=memory_context,
        skills_dir=str(skills_dir),
        issue=issue,
        call_fn=mock_call_fn,
        node_id="test_node",
        config=MockConfig(),
        note_fn=mock_note_fn,
    )

    # Verify exception was caught and logged
    assert len(notes) == 1
    assert "Skill learner failed (non-blocking)" in notes[0]["msg"]
    assert "skill_learner" in notes[0]["tags"]
    assert "error" in notes[0]["tags"]

    # Verify memory_context is unchanged (graceful degradation)
    assert result == memory_context
    assert "skills_context" not in result


@pytest.mark.asyncio
async def test_inject_skills_context_empty_skills_context(tmp_path):
    """Test handling when run_skill_learner returns empty skills_context."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Mock call_fn to return empty skills_context
    mock_call_fn = AsyncMock(
        return_value={
            "skills_context": "",  # Empty
            "discovery_summary": "No skills matched",
        }
    )

    class MockConfig:
        skill_learner_model = "haiku"
        ai_provider = "claude"

    memory_context = {"codebase_conventions": {"note_0": "Use pytest"}}
    issue = {"name": "test-issue"}

    result = await _inject_skills_context(
        memory_context=memory_context,
        skills_dir=str(skills_dir),
        issue=issue,
        call_fn=mock_call_fn,
        node_id="test_node",
        config=MockConfig(),
        note_fn=None,
    )

    # Verify skills_context was NOT added (because it's empty)
    assert "skills_context" not in result
    assert result == memory_context


# ---------------------------------------------------------------------------
# Unit tests for coder_task_prompt
# ---------------------------------------------------------------------------


def test_coder_prompt_includes_skills_section():
    """Test that coder_task_prompt renders 'Applicable Skills' section when skills_context is present."""
    issue = {
        "name": "test-issue",
        "title": "Add FastAPI endpoints",
        "acceptance_criteria": ["Endpoint returns 200"],
    }

    memory_context = {
        "skills_context": (
            "### fastapi\n"
            "> FastAPI best practices and conventions\n\n"
            "Use `fastapi dev` for development...\n"
        )
    }

    prompt = coder_task_prompt(
        issue=issue,
        worktree_path="/repo",
        memory_context=memory_context,
    )

    # Verify the skills section is present
    assert "## Applicable Skills" in prompt
    assert "The following skills are relevant to this issue" in prompt
    assert "### fastapi" in prompt
    assert "FastAPI best practices and conventions" in prompt
    assert "Use `fastapi dev` for development" in prompt


def test_coder_prompt_no_skills_section_when_missing():
    """Test that coder_task_prompt does not render skills section when memory_context lacks skills_context."""
    issue = {
        "name": "test-issue",
        "title": "Add FastAPI endpoints",
        "acceptance_criteria": ["Endpoint returns 200"],
    }

    memory_context = {
        "codebase_conventions": {"note_0": "Use pytest"},
    }

    prompt = coder_task_prompt(
        issue=issue,
        worktree_path="/repo",
        memory_context=memory_context,
    )

    # Verify the skills section is NOT present
    assert "## Applicable Skills" not in prompt
    assert "skills are relevant to this issue" not in prompt


def test_coder_prompt_skills_section_after_bug_patterns():
    """Test that skills section appears after bug_patterns section in the prompt."""
    issue = {"name": "test-issue", "title": "Test Issue"}

    memory_context = {
        "bug_patterns": [
            {"type": "import_error", "frequency": 3, "modules": ["mod1", "mod2"]}
        ],
        "skills_context": "### skill1\n> Skill content",
    }

    prompt = coder_task_prompt(
        issue=issue,
        worktree_path="/repo",
        memory_context=memory_context,
    )

    # Verify both sections are present
    assert "## Common Bug Patterns in This Build" in prompt
    assert "## Applicable Skills" in prompt

    # Verify skills section comes after bug_patterns
    bug_patterns_idx = prompt.index("## Common Bug Patterns in This Build")
    skills_idx = prompt.index("## Applicable Skills")
    assert skills_idx > bug_patterns_idx


def test_coder_prompt_empty_memory_context():
    """Test coder_task_prompt with empty memory_context."""
    issue = {"name": "test-issue", "title": "Test Issue"}

    prompt = coder_task_prompt(
        issue=issue,
        worktree_path="/repo",
        memory_context={},
    )

    # Verify no skills section
    assert "## Applicable Skills" not in prompt
