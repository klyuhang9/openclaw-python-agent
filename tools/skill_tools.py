"""
Skill tools: list, load, unload, create, and update skills.
The SkillManager instance is injected at startup by tools/__init__.py.
"""

from typing import Dict, Optional

# Injected by tools/__init__.py after the agent is created
_skill_manager = None

# Active skills for this session: name → SKILL.md content
_active_skills: Dict[str, str] = {}


def _get_sm():
    if _skill_manager is None:
        raise RuntimeError("SkillManager not initialised in skill_tools")
    return _skill_manager


# ------------------------------------------------------------------
# Tool functions
# ------------------------------------------------------------------

def list_skills() -> str:
    """Return all available skills with their descriptions."""
    skills = _get_sm().list_skills()
    if not skills:
        return "No skills found. Use create_skill to create one."
    lines = ["Available skills:\n"]
    for s in skills:
        loaded = " [loaded]" if s["name"] in _active_skills else ""
        lines.append(f"- **{s['name']}**{loaded}: {s['description']}")
    return "\n".join(lines)


def load_skill(name: str) -> str:
    """Load a skill into the active session so its instructions appear in the system prompt."""
    content = _get_sm().get_skill_content(name)
    if content is None:
        return f"Error: Skill '{name}' not found. Use list_skills to see available skills."
    _active_skills[name] = content
    # Return a brief summary (first 300 chars) so the tool result isn't huge
    preview = content[:300] + ("…" if len(content) > 300 else "")
    return f"Skill '{name}' loaded into active session.\n\n{preview}"


def unload_skill(name: str) -> str:
    """Remove a skill from the active session."""
    if name not in _active_skills:
        return f"Skill '{name}' is not currently loaded."
    del _active_skills[name]
    return f"Skill '{name}' unloaded from active session."


def create_skill(name: str, content: str) -> str:
    """Create a new skill file at skills/<name>/SKILL.md."""
    path = _get_sm().create_skill(name, content)
    return f"Skill '{name}' created at {path}."


def update_skill(name: str, content: str) -> str:
    """Overwrite an existing skill file with new content."""
    path = _get_sm().update_skill(name, content)
    # If currently loaded, refresh the in-memory copy
    if name in _active_skills:
        _active_skills[name] = content
    return f"Skill '{name}' updated at {path}."


def delete_skill(name: str) -> str:
    """Delete the skill file and directory for a given skill."""
    deleted = _get_sm().delete_skill(name)
    if not deleted:
        return f"Error: Skill '{name}' not found."
    # Keep in _active_skills if loaded — per spec, current session is unaffected
    return f"Skill '{name}' deleted from disk."
