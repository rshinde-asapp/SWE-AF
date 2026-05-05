"""Skill-learner reasoner for DE-AF.

Discovers skill files from a ./skills directory, matches them to issues based on context
(file paths, keywords, descriptions), and injects relevant skill knowledge into the coder
agent's memory context.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel

from de_af.reasoners import router


class SkillDefinition(BaseModel):
    """A single skill parsed from a skill file.

    Represents the structured content extracted from a markdown skill file
    with YAML frontmatter. The skill file format follows the Claude Code
    SKILL.md convention used in library agent directories.
    """

    name: str  # From YAML frontmatter 'name' field
    description: str  # From YAML frontmatter 'description' field
    content: str  # Full markdown content (body after frontmatter)
    file_path: str  # Absolute path to the source skill file


class SkillLearnerResult(BaseModel):
    """Output from the skill-learner reasoner.

    Contains the list of matched skills and a formatted context string
    ready for injection into the coder's memory context.
    """

    matched_skills: list[SkillDefinition]  # Skills matching the issue context
    skills_context: str  # Formatted markdown for coder prompt
    discovery_summary: str  # Brief log of what was found/matched


def discover_skills(skills_dir: str) -> list[SkillDefinition]:
    """Scan skills_dir for *.md files with YAML frontmatter.

    Recursively walks skills_dir and parses each .md file that has valid
    YAML frontmatter (delimited by --- markers). Invalid files are skipped
    with a warning (graceful degradation).

    Args:
        skills_dir: Absolute path to the skills directory (e.g., "<repo>/skills").

    Returns:
        List of SkillDefinition objects. Empty list if:
        - skills_dir doesn't exist
        - skills_dir is empty
        - No valid skill files found

    Example:
        >>> skills = discover_skills("/repo/skills")
        >>> len(skills)
        3
        >>> skills[0].name
        'fastapi'
    """
    if not os.path.isdir(skills_dir):
        return []

    skills = []
    skills_path = Path(skills_dir)

    # Recursively find all .md files
    for md_file in skills_path.rglob("*.md"):
        skill = parse_skill_file(str(md_file))
        if skill:
            skills.append(skill)

    return skills


def parse_skill_file(file_path: str) -> SkillDefinition | None:
    """Parse a single skill file and extract frontmatter + content.

    Expects markdown files with YAML frontmatter in this format:

    ```markdown
    ---
    name: skill_name
    description: What this skill helps with...
    keywords:  # optional
      - pattern1
      - pattern2
    ---

    # Skill Content

    Full markdown body here...
    ```

    Args:
        file_path: Absolute path to the .md skill file.

    Returns:
        SkillDefinition if parsing succeeds, None if:
        - File doesn't exist
        - File has no YAML frontmatter (no --- delimiters)
        - YAML frontmatter lacks required 'name' or 'description' fields
        - YAML parsing fails (malformed YAML)

    Example:
        >>> skill = parse_skill_file("/repo/skills/fastapi.md")
        >>> skill.name
        'fastapi'
        >>> skill.description
        'FastAPI best practices...'
    """
    if not os.path.isfile(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for YAML frontmatter delimiters
        if not content.startswith("---"):
            return None

        # Find the end of frontmatter
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        # Parse YAML frontmatter (parts[1] is between the two --- markers)
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None

        # Validate required fields
        if not isinstance(frontmatter, dict):
            return None

        name = frontmatter.get("name")
        description = frontmatter.get("description")

        if not name or not description:
            return None

        # Content is everything after the second ---
        body = parts[2].strip()

        return SkillDefinition(
            name=str(name),
            description=str(description),
            content=body,
            file_path=file_path,
        )

    except Exception:
        # Graceful degradation: skip malformed files
        return None


def match_skills(
    issue: dict,
    available_skills: list[SkillDefinition],
) -> list[SkillDefinition]:
    """Match skills to an issue based on file paths and keywords.

    Matching heuristics (in priority order):

    1. **Explicit skill tags**: If issue has 'skills' field, match by name
       - issue['skills'] = ['fastapi', 'dbt'] → match skills with those names

    2. **File path patterns**: Match skill name/keywords against issue file paths
       - issue['files_to_modify'] = ['src/api.py'] + skill.name='fastapi' → match
       - issue['files_to_create'] = ['models/stg_users.sql'] + skill keywords
         include 'models/' → match

    3. **Description keywords**: Match skill name/description against issue text
       - issue['description'] contains 'FastAPI' + skill.name='fastapi' → match
       - issue['title'] contains 'API endpoint' + skill.description mentions 'API' → match

    Args:
        issue: Issue dict with keys: name, title, description, files_to_modify,
               files_to_create, skills (optional), acceptance_criteria.
        available_skills: All discovered skills from discover_skills().

    Returns:
        List of matched skills, ordered by relevance (explicit > file path > keyword).
        Returns at most 5 skills to avoid context overflow.
        Returns empty list if no matches found.

    Example:
        >>> issue = {'name': 'api-endpoints', 'files_to_modify': ['src/api/routes.py']}
        >>> matched = match_skills(issue, all_skills)
        >>> [s.name for s in matched]
        ['fastapi', 'python']
    """
    matched = []
    scores = {}  # Track relevance scores for ordering

    # Extract issue context
    explicit_skills = issue.get("skills", [])
    files_to_modify = issue.get("files_to_modify", [])
    files_to_create = issue.get("files_to_create", [])
    all_files = files_to_modify + files_to_create

    title = issue.get("title", "").lower()
    description = issue.get("description", "").lower()
    issue_text = f"{title} {description}"

    for skill in available_skills:
        skill_name_lower = skill.name.lower()
        skill_desc_lower = skill.description.lower()

        # Priority 1: Explicit skill tags (highest score)
        if explicit_skills and skill.name in explicit_skills:
            matched.append(skill)
            scores[skill.name] = 100
            continue

        # Priority 2: File path matching (medium score)
        file_match = False
        for file_path in all_files:
            file_path_lower = file_path.lower()
            # Check if skill name appears in file path
            if skill_name_lower in file_path_lower:
                file_match = True
                break
            # Check if file path contains skill-related patterns
            # (e.g., "api" in path matches "fastapi" skill)
            # Extract meaningful parts from the file path
            path_parts = file_path_lower.replace("/", " ").replace(".", " ").replace("_", " ").split()
            for path_part in path_parts:
                # Check if path part is contained in skill name (e.g., "api" in "fastapi")
                if len(path_part) > 2 and path_part in skill_name_lower:
                    file_match = True
                    break
                # Or if skill name part is in path
                if len(path_part) > 2 and skill_name_lower in path_part:
                    file_match = True
                    break
            if file_match:
                break

        if file_match:
            matched.append(skill)
            scores[skill.name] = 50
            continue

        # Priority 3: Description/title keyword matching (lowest score)
        keyword_match = False
        # Check if skill name appears in issue text
        if skill_name_lower in issue_text:
            keyword_match = True
        # Check if key terms from skill description appear in issue
        elif any(
            word in issue_text
            for word in skill_desc_lower.split()
            if len(word) > 4  # Only check meaningful words
        ):
            keyword_match = True

        if keyword_match:
            matched.append(skill)
            scores[skill.name] = 10

    # Sort by score (descending) and limit to 5
    matched_unique = []
    seen = set()
    for skill in matched:
        if skill.name not in seen:
            matched_unique.append(skill)
            seen.add(skill.name)

    matched_unique.sort(key=lambda s: scores.get(s.name, 0), reverse=True)
    return matched_unique[:5]


def format_skills_context(matched_skills: list[SkillDefinition]) -> str:
    """Format matched skills as markdown for injection into coder prompt.

    Produces a structured markdown block that the coder can reference.
    Truncates individual skill content to 2000 chars if necessary.

    Args:
        matched_skills: Skills that matched the issue context.

    Returns:
        Formatted markdown string. Empty string if no skills matched.

    Example output:
        ```
        The following skills are relevant to this issue:

        ### fastapi
        > FastAPI best practices and conventions...

        [Skill content here, truncated if > 2000 chars]

        ---

        ### dbt
        > dbt model naming and testing conventions...

        [Skill content here]
        ```
    """
    if not matched_skills:
        return ""

    sections = []
    sections.append("The following skills are relevant to this issue:\n")

    for skill in matched_skills:
        sections.append(f"### {skill.name}")
        sections.append(f"> {skill.description}\n")

        # Truncate content to 2000 chars
        content = skill.content
        if len(content) > 2000:
            content = content[:2000] + "\n\n[...content truncated...]"

        sections.append(content)
        sections.append("\n---\n")

    return "\n".join(sections)


@router.reasoner()
async def run_skill_learner(
    skills_dir: str,
    issue: dict,
    model: str = "haiku",
    ai_provider: str = "claude",
) -> dict:
    """Discover and match skills for an issue, returning formatted context.

    This reasoner does NOT invoke an LLM — it performs deterministic file
    scanning and pattern matching. The @router.reasoner() decorator is used
    for observability (appears in call graph) and consistent error handling.

    Args:
        skills_dir: Absolute path to skills directory. If doesn't exist,
                   returns empty result (graceful degradation).
        issue: Issue dict with context for matching (name, title, files, etc.)
        model: Unused — no LLM call (kept for API consistency with other reasoners)
        ai_provider: Unused — no LLM call

    Returns:
        SkillLearnerResult.model_dump() with:
        - matched_skills: List of matched SkillDefinition dicts
        - skills_context: Formatted markdown string for coder prompt
        - discovery_summary: Brief log message

    Graceful Degradation:
        - skills_dir doesn't exist → empty result, no error
        - skills_dir empty → empty result
        - No matches → empty result
        - Parse errors in skill files → skip file, continue
    """
    # Graceful degradation: check if directory exists
    if not os.path.isdir(skills_dir):
        result = SkillLearnerResult(
            matched_skills=[],
            skills_context="",
            discovery_summary="Skills directory not found",
        )
        return result.model_dump()

    # Discover all skills
    all_skills = discover_skills(skills_dir)

    if not all_skills:
        result = SkillLearnerResult(
            matched_skills=[],
            skills_context="",
            discovery_summary="No valid skill files found",
        )
        return result.model_dump()

    # Match skills to issue
    matched = match_skills(issue, all_skills)

    # Format context
    skills_context = format_skills_context(matched)

    # Build summary
    summary = f"Found {len(all_skills)} skill(s), matched {len(matched)}"
    if matched:
        skill_names = ", ".join(s.name for s in matched)
        summary += f" ({skill_names})"

    result = SkillLearnerResult(
        matched_skills=matched,
        skills_context=skills_context,
        discovery_summary=summary,
    )

    return result.model_dump()
