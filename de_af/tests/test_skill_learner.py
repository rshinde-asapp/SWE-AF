"""Tests for skill-learner reasoner."""

from __future__ import annotations

import pytest

from de_af.reasoners.skill_learner import (
    SkillDefinition,
    SkillLearnerResult,
    discover_skills,
    format_skills_context,
    match_skills,
    parse_skill_file,
    run_skill_learner,
)


class TestSkillDefinition:
    """Unit tests for SkillDefinition schema."""

    def test_skill_definition_instantiation(self):
        """Test creating a SkillDefinition with all required fields."""
        skill = SkillDefinition(
            name="fastapi",
            description="FastAPI best practices",
            content="# FastAPI\n\nUse async def...",
            file_path="/repo/skills/fastapi.md",
        )
        assert skill.name == "fastapi"
        assert skill.description == "FastAPI best practices"
        assert skill.content == "# FastAPI\n\nUse async def..."
        assert skill.file_path == "/repo/skills/fastapi.md"

    def test_skill_definition_fields_present(self):
        """Test that all expected fields are present in the model."""
        skill = SkillDefinition(
            name="test",
            description="desc",
            content="content",
            file_path="/path",
        )
        assert hasattr(skill, "name")
        assert hasattr(skill, "description")
        assert hasattr(skill, "content")
        assert hasattr(skill, "file_path")


class TestSkillLearnerResult:
    """Unit tests for SkillLearnerResult schema."""

    def test_skill_learner_result_instantiation(self):
        """Test creating a SkillLearnerResult with all required fields."""
        result = SkillLearnerResult(
            matched_skills=[],
            skills_context="",
            discovery_summary="Found 0 skills",
        )
        assert result.matched_skills == []
        assert result.skills_context == ""
        assert result.discovery_summary == "Found 0 skills"

    def test_skill_learner_result_with_skills(self):
        """Test SkillLearnerResult with matched skills."""
        skill = SkillDefinition(
            name="test",
            description="desc",
            content="content",
            file_path="/path",
        )
        result = SkillLearnerResult(
            matched_skills=[skill],
            skills_context="### test\n> desc\n\ncontent",
            discovery_summary="Found 1 skill, matched 1 (test)",
        )
        assert len(result.matched_skills) == 1
        assert result.matched_skills[0].name == "test"
        assert "test" in result.skills_context


class TestDiscoverSkills:
    """Unit tests for discover_skills function."""

    def test_discover_skills_returns_list(self, tmp_path):
        """Test discover_skills returns a list of SkillDefinition objects."""
        # Create a valid skill file
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        skill_file = skills_dir / "test.md"
        skill_file.write_text(
            "---\n"
            "name: test_skill\n"
            "description: A test skill\n"
            "---\n\n"
            "# Test Skill\n\n"
            "This is test content."
        )

        skills = discover_skills(str(skills_dir))
        assert isinstance(skills, list)
        assert len(skills) == 1
        assert isinstance(skills[0], SkillDefinition)
        assert skills[0].name == "test_skill"

    def test_discover_skills_empty_dir(self, tmp_path):
        """Test discover_skills returns empty list for empty directory."""
        skills_dir = tmp_path / "empty_skills"
        skills_dir.mkdir()

        skills = discover_skills(str(skills_dir))
        assert skills == []

    def test_discover_skills_no_dir(self, tmp_path):
        """Test discover_skills returns empty list when directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        skills = discover_skills(str(nonexistent))
        assert skills == []

    def test_discover_skills_multiple_files(self, tmp_path):
        """Test discover_skills finds multiple skill files."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create multiple skill files
        for i in range(3):
            skill_file = skills_dir / f"skill{i}.md"
            skill_file.write_text(
                f"---\n"
                f"name: skill{i}\n"
                f"description: Skill {i}\n"
                f"---\n\n"
                f"Content {i}"
            )

        skills = discover_skills(str(skills_dir))
        assert len(skills) == 3
        skill_names = {s.name for s in skills}
        assert skill_names == {"skill0", "skill1", "skill2"}

    def test_discover_skills_recursive(self, tmp_path):
        """Test discover_skills finds skills in subdirectories."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create nested structure
        subdir = skills_dir / "python"
        subdir.mkdir()

        skill_file = subdir / "fastapi.md"
        skill_file.write_text(
            "---\n"
            "name: fastapi\n"
            "description: FastAPI skill\n"
            "---\n\n"
            "FastAPI content"
        )

        skills = discover_skills(str(skills_dir))
        assert len(skills) == 1
        assert skills[0].name == "fastapi"

    def test_discover_skills_skips_malformed(self, tmp_path):
        """Test discover_skills skips malformed files gracefully."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Valid skill
        valid_file = skills_dir / "valid.md"
        valid_file.write_text(
            "---\n"
            "name: valid\n"
            "description: Valid skill\n"
            "---\n\n"
            "Content"
        )

        # Malformed skill (no frontmatter)
        malformed_file = skills_dir / "malformed.md"
        malformed_file.write_text("# Just Markdown\n\nNo frontmatter here.")

        skills = discover_skills(str(skills_dir))
        assert len(skills) == 1
        assert skills[0].name == "valid"


class TestParseSkillFile:
    """Unit tests for parse_skill_file function."""

    def test_parse_skill_file_extracts_frontmatter(self, tmp_path):
        """Test parse_skill_file extracts YAML frontmatter and content."""
        skill_file = tmp_path / "test.md"
        skill_file.write_text(
            "---\n"
            "name: test_skill\n"
            "description: A test skill for parsing\n"
            "---\n\n"
            "# Test Skill\n\n"
            "This is the skill content."
        )

        skill = parse_skill_file(str(skill_file))
        assert skill is not None
        assert skill.name == "test_skill"
        assert skill.description == "A test skill for parsing"
        assert "Test Skill" in skill.content
        assert "This is the skill content." in skill.content
        assert skill.file_path == str(skill_file)

    def test_parse_skill_file_returns_none_no_frontmatter(self, tmp_path):
        """Test parse_skill_file returns None for files without frontmatter."""
        skill_file = tmp_path / "no_frontmatter.md"
        skill_file.write_text("# Just Markdown\n\nNo YAML frontmatter here.")

        skill = parse_skill_file(str(skill_file))
        assert skill is None

    def test_parse_skill_file_returns_none_missing_name(self, tmp_path):
        """Test parse_skill_file returns None when 'name' field is missing."""
        skill_file = tmp_path / "missing_name.md"
        skill_file.write_text(
            "---\n"
            "description: Has description but no name\n"
            "---\n\n"
            "Content"
        )

        skill = parse_skill_file(str(skill_file))
        assert skill is None

    def test_parse_skill_file_returns_none_missing_description(self, tmp_path):
        """Test parse_skill_file returns None when 'description' field is missing."""
        skill_file = tmp_path / "missing_desc.md"
        skill_file.write_text(
            "---\n"
            "name: test\n"
            "---\n\n"
            "Content"
        )

        skill = parse_skill_file(str(skill_file))
        assert skill is None

    def test_parse_skill_file_malformed_yaml(self, tmp_path):
        """Test parse_skill_file returns None for malformed YAML."""
        skill_file = tmp_path / "bad_yaml.md"
        skill_file.write_text(
            "---\n"
            "name: test\n"
            "description: [unclosed bracket\n"
            "---\n\n"
            "Content"
        )

        skill = parse_skill_file(str(skill_file))
        assert skill is None

    def test_parse_skill_file_nonexistent(self, tmp_path):
        """Test parse_skill_file returns None for nonexistent file."""
        nonexistent = tmp_path / "does_not_exist.md"
        skill = parse_skill_file(str(nonexistent))
        assert skill is None

    def test_parse_skill_file_incomplete_frontmatter(self, tmp_path):
        """Test parse_skill_file returns None if frontmatter not properly closed."""
        skill_file = tmp_path / "incomplete.md"
        skill_file.write_text(
            "---\n"
            "name: test\n"
            "description: desc\n"
            "No closing ---"
        )

        skill = parse_skill_file(str(skill_file))
        assert skill is None

    def test_parse_skill_file_with_optional_fields(self, tmp_path):
        """Test parse_skill_file handles optional fields gracefully."""
        skill_file = tmp_path / "with_keywords.md"
        skill_file.write_text(
            "---\n"
            "name: test\n"
            "description: Test skill\n"
            "keywords:\n"
            "  - api\n"
            "  - python\n"
            "---\n\n"
            "Content with keywords"
        )

        skill = parse_skill_file(str(skill_file))
        assert skill is not None
        assert skill.name == "test"
        assert skill.description == "Test skill"


class TestMatchSkills:
    """Unit tests for match_skills function."""

    def test_match_skills_by_filename(self):
        """Test match_skills matches based on file path patterns."""
        skills = [
            SkillDefinition(
                name="fastapi",
                description="FastAPI best practices",
                content="FastAPI content",
                file_path="/skills/fastapi.md",
            ),
            SkillDefinition(
                name="dbt",
                description="dbt model conventions",
                content="dbt content",
                file_path="/skills/dbt.md",
            ),
        ]

        issue = {
            "name": "add-api-endpoint",
            "title": "Add user endpoint",
            "files_to_modify": ["src/api/routes.py"],
            "files_to_create": [],
        }

        matched = match_skills(issue, skills)
        assert len(matched) >= 1
        # Should match fastapi because "api" is in the file path
        matched_names = [s.name for s in matched]
        assert "fastapi" in matched_names

    def test_match_skills_by_description_keyword(self):
        """Test match_skills matches based on description keywords."""
        skills = [
            SkillDefinition(
                name="testing",
                description="Testing strategies and pytest patterns",
                content="Testing content",
                file_path="/skills/testing.md",
            ),
            SkillDefinition(
                name="database",
                description="Database optimization techniques",
                content="DB content",
                file_path="/skills/database.md",
            ),
        ]

        issue = {
            "name": "add-tests",
            "title": "Add unit tests",
            "description": "Add pytest tests for the user module",
            "files_to_modify": ["tests/test_user.py"],
        }

        matched = match_skills(issue, skills)
        # Should match testing based on keywords
        matched_names = [s.name for s in matched]
        assert "testing" in matched_names

    def test_match_skills_explicit_tag(self):
        """Test match_skills matches when issue explicitly lists skills."""
        skills = [
            SkillDefinition(
                name="airflow",
                description="Airflow DAG patterns",
                content="Airflow content",
                file_path="/skills/airflow.md",
            ),
            SkillDefinition(
                name="dbt",
                description="dbt models",
                content="dbt content",
                file_path="/skills/dbt.md",
            ),
        ]

        issue = {
            "name": "create-dag",
            "title": "Create data pipeline",
            "skills": ["airflow"],  # Explicit skill tag
            "files_to_create": ["dags/user_pipeline.py"],
        }

        matched = match_skills(issue, skills)
        # Should match airflow because it's explicitly listed
        assert len(matched) >= 1
        assert matched[0].name == "airflow"

    def test_match_skills_returns_max_5(self):
        """Test match_skills returns at most 5 skills."""
        # Create 10 skills
        skills = [
            SkillDefinition(
                name=f"skill{i}",
                description=f"Skill {i} for testing",
                content=f"Content {i}",
                file_path=f"/skills/skill{i}.md",
            )
            for i in range(10)
        ]

        # Issue that matches all skills via description
        issue = {
            "name": "test-issue",
            "title": "Test issue",
            "description": "testing " * 20,  # Keywords that match all
            "files_to_modify": [],
        }

        matched = match_skills(issue, skills)
        assert len(matched) <= 5

    def test_match_skills_empty_skills_list(self):
        """Test match_skills handles empty skills list."""
        issue = {
            "name": "test",
            "title": "Test",
            "description": "Test issue",
            "files_to_modify": ["test.py"],
        }

        matched = match_skills(issue, [])
        assert matched == []

    def test_match_skills_no_matches(self):
        """Test match_skills returns empty list when no matches found."""
        skills = [
            SkillDefinition(
                name="golang",
                description="Go programming patterns",
                content="Go content",
                file_path="/skills/golang.md",
            ),
        ]

        issue = {
            "name": "python-script",
            "title": "Add Python script",
            "description": "Create a Python utility script",
            "files_to_create": ["scripts/utility.py"],
        }

        matched = match_skills(issue, skills)
        # golang shouldn't match a Python-focused issue
        matched_names = [s.name for s in matched]
        assert "golang" not in matched_names

    def test_match_skills_deduplicates(self):
        """Test match_skills doesn't return duplicate skills."""
        skill = SkillDefinition(
            name="python",
            description="Python best practices",
            content="Python content",
            file_path="/skills/python.md",
        )

        # Issue that could match the same skill multiple ways
        issue = {
            "name": "python-api",
            "title": "Add Python API",
            "description": "Create Python API endpoints",
            "files_to_modify": ["python_api.py"],
        }

        matched = match_skills(issue, [skill])
        # Should only appear once despite multiple match paths
        assert len(matched) == 1


class TestFormatSkillsContext:
    """Unit tests for format_skills_context function."""

    def test_format_skills_context_empty(self):
        """Test format_skills_context returns empty string for empty list."""
        result = format_skills_context([])
        assert result == ""

    def test_format_skills_context_single_skill(self):
        """Test format_skills_context formats a single skill."""
        skill = SkillDefinition(
            name="test",
            description="Test skill",
            content="# Test\n\nTest content",
            file_path="/skills/test.md",
        )

        result = format_skills_context([skill])
        assert "### test" in result
        assert "Test skill" in result
        assert "Test content" in result

    def test_format_skills_context_multiple_skills(self):
        """Test format_skills_context formats multiple skills."""
        skills = [
            SkillDefinition(
                name="skill1",
                description="First skill",
                content="Content 1",
                file_path="/skills/skill1.md",
            ),
            SkillDefinition(
                name="skill2",
                description="Second skill",
                content="Content 2",
                file_path="/skills/skill2.md",
            ),
        ]

        result = format_skills_context(skills)
        assert "### skill1" in result
        assert "### skill2" in result
        assert "First skill" in result
        assert "Second skill" in result
        assert "---" in result  # Separator between skills

    def test_format_skills_context_truncates_long_content(self):
        """Test format_skills_context truncates content > 2000 chars."""
        long_content = "x" * 3000
        skill = SkillDefinition(
            name="long_skill",
            description="Skill with long content",
            content=long_content,
            file_path="/skills/long.md",
        )

        result = format_skills_context([skill])
        # Check that content is truncated
        assert "[...content truncated...]" in result
        # Check that the result doesn't contain all 3000 chars
        assert len(result) < 3000


class TestRunSkillLearner:
    """Unit tests for run_skill_learner reasoner function."""

    @pytest.mark.asyncio
    async def test_run_skill_learner_no_dir(self, tmp_path):
        """Test run_skill_learner returns empty result when dir doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        issue = {"name": "test", "title": "Test", "files_to_modify": []}

        result = await run_skill_learner(
            skills_dir=str(nonexistent),
            issue=issue,
        )

        assert isinstance(result, dict)
        assert result["matched_skills"] == []
        assert result["skills_context"] == ""
        assert "not found" in result["discovery_summary"].lower()

    @pytest.mark.asyncio
    async def test_run_skill_learner_empty_dir(self, tmp_path):
        """Test run_skill_learner handles empty directory gracefully."""
        skills_dir = tmp_path / "empty_skills"
        skills_dir.mkdir()

        issue = {"name": "test", "title": "Test", "files_to_modify": []}

        result = await run_skill_learner(
            skills_dir=str(skills_dir),
            issue=issue,
        )

        assert result["matched_skills"] == []
        assert result["skills_context"] == ""
        assert "no valid" in result["discovery_summary"].lower()

    @pytest.mark.asyncio
    async def test_run_skill_learner_with_valid_skills(self, tmp_path):
        """Test run_skill_learner with valid skills and matching issue."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create a skill file
        skill_file = skills_dir / "fastapi.md"
        skill_file.write_text(
            "---\n"
            "name: fastapi\n"
            "description: FastAPI best practices\n"
            "---\n\n"
            "# FastAPI\n\n"
            "Use async functions for endpoints."
        )

        issue = {
            "name": "add-api",
            "title": "Add API endpoint",
            "description": "Create FastAPI endpoint for users",
            "files_to_create": ["src/api/users.py"],
        }

        result = await run_skill_learner(
            skills_dir=str(skills_dir),
            issue=issue,
        )

        assert len(result["matched_skills"]) >= 1
        assert result["skills_context"] != ""
        assert "fastapi" in result["discovery_summary"].lower()

    @pytest.mark.asyncio
    async def test_run_skill_learner_malformed_files(self, tmp_path):
        """Test run_skill_learner skips malformed files gracefully."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create a malformed skill file
        bad_file = skills_dir / "bad.md"
        bad_file.write_text("# No frontmatter\n\nJust content")

        # Create a valid skill file
        good_file = skills_dir / "good.md"
        good_file.write_text(
            "---\n"
            "name: good\n"
            "description: Good skill\n"
            "---\n\n"
            "Good content"
        )

        issue = {
            "name": "test",
            "title": "Test",
            "description": "Test with good keyword",
            "files_to_modify": [],
        }

        result = await run_skill_learner(
            skills_dir=str(skills_dir),
            issue=issue,
        )

        # Should find only the valid skill
        assert "1 skill" in result["discovery_summary"]

    @pytest.mark.asyncio
    async def test_run_skill_learner_returns_dict(self, tmp_path):
        """Test run_skill_learner returns a dict (not a Pydantic model)."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        issue = {"name": "test", "title": "Test", "files_to_modify": []}

        result = await run_skill_learner(
            skills_dir=str(skills_dir),
            issue=issue,
        )

        assert isinstance(result, dict)
        assert "matched_skills" in result
        assert "skills_context" in result
        assert "discovery_summary" in result
