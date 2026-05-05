"""Prompt module for the skill-learner role.

Note: The skill-learner reasoner does NOT invoke an LLM for matching.
These prompts exist for:
1. API consistency with other roles
2. Future extensibility if LLM-based matching is needed
3. Observability in the prompt registry
"""

from __future__ import annotations


SYSTEM_PROMPT: str = """\
You are a Skill Matcher agent for the DE-AF data pipeline framework.
Your job is to analyze an issue's context and identify which pre-defined
skills are relevant to help the coder implement the solution.

## What Skills Are

Skills are markdown documents containing domain-specific knowledge:
- Best practices for specific frameworks (FastAPI, dbt, Airflow)
- Project-specific conventions and patterns
- Code snippets and examples for common tasks
- Testing strategies and validation approaches

## Matching Criteria

Match skills when:
1. The issue explicitly requests a skill by name
2. File paths in the issue match skill keywords (e.g., "models/*.sql" → dbt skill)
3. Issue description contains relevant domain keywords

Do NOT match skills that are only tangentially related.
Prefer fewer, highly-relevant skills over many weakly-related ones.
"""


def skill_learner_task_prompt(
    issue: dict,
    available_skill_names: list[str],
    skills_dir: str,
) -> str:
    """Build task prompt for skill matching (not currently used by reasoner).

    Args:
        issue: Issue dict with name, title, description, files.
        available_skill_names: Names of all discovered skills.
        skills_dir: Path to skills directory.

    Returns:
        Formatted task prompt string.
    """
    sections = []

    sections.append("## Issue to Match")
    sections.append(f"- **Name**: {issue.get('name', '(unknown)')}")
    sections.append(f"- **Title**: {issue.get('title', '(unknown)')}")

    desc = issue.get("description", "")
    if desc:
        sections.append(f"- **Description**: {desc[:500]}...")

    files = issue.get("files_to_modify", []) + issue.get("files_to_create", [])
    if files:
        sections.append(f"- **Files**: {files}")

    sections.append(f"\n## Available Skills\n{available_skill_names}")
    sections.append(f"\n## Skills Directory\n`{skills_dir}`")

    sections.append(
        "\n## Your Task\n"
        "Identify which skills are relevant to this issue.\n"
        "Return the skill names as a list."
    )

    return "\n".join(sections)
