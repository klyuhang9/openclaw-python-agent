"""
SkillManager: scans the skills/ directory and provides skill file management.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional


class SkillManager:
    """Manages skill files stored under skills/<name>/SKILL.md."""

    SKILL_FILENAME = "SKILL.md"

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_skills(self) -> List[Dict]:
        """Scan skills/ directory and return [{name, description, path}]."""
        result = []
        if not self.skills_dir.exists():
            return result
        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / self.SKILL_FILENAME
            if not skill_file.exists():
                continue
            content = skill_file.read_text(encoding="utf-8")
            description = self._extract_description(content)
            result.append(
                {
                    "name": skill_dir.name,
                    "description": description,
                    "path": str(skill_file),
                }
            )
        return result

    def get_skill_content(self, name: str) -> Optional[str]:
        """Return the content of skills/<name>/SKILL.md, or None if it doesn't exist."""
        skill_file = self.skills_dir / name / self.SKILL_FILENAME
        if not skill_file.exists():
            return None
        return skill_file.read_text(encoding="utf-8")

    def create_skill(self, name: str, content: str) -> str:
        """Create skills/<name>/SKILL.md with the given content."""
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / self.SKILL_FILENAME
        skill_file.write_text(content, encoding="utf-8")
        return str(skill_file)

    def update_skill(self, name: str, content: str) -> str:
        """Overwrite skills/<name>/SKILL.md with new content."""
        skill_dir = self.skills_dir / name
        if not skill_dir.exists():
            skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / self.SKILL_FILENAME
        skill_file.write_text(content, encoding="utf-8")
        return str(skill_file)

    def delete_skill(self, name: str) -> bool:
        """Delete the skills/<name>/ directory. Returns True if deleted, False if not found."""
        skill_dir = self.skills_dir / name
        if not skill_dir.exists():
            return False
        shutil.rmtree(skill_dir)
        return True

    def get_skills_summary(self) -> str:
        """Return a short Markdown list of all available skills for injection into the system prompt."""
        skills = self.list_skills()
        if not skills:
            return ""
        lines = [
            "## Available Skills",
            "以下 skill 可按需激活。使用 list_skills 查看详情，load_skill 激活，create_skill 创建新 skill。",
            "",
        ]
        for s in skills:
            lines.append(f"- **{s['name']}**: {s['description']}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_description(self, content: str) -> str:
        """Extract the description field from YAML front-matter, or return empty string."""
        lines = content.splitlines()
        in_frontmatter = False
        for line in lines:
            stripped = line.strip()
            if stripped == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break  # end of frontmatter
            if in_frontmatter and stripped.startswith("description:"):
                return stripped[len("description:"):].strip()
        return ""
