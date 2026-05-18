from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillDef:
    name: str
    description: str
    triggers: list[str]
    constraints: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    priority: int = 0
    prompt_content: str = ""
    dir_path: Path | None = None


class SkillEngine:
    def __init__(self):
        self._skills: list[SkillDef] = []

    def scan_directory(self, skills_dir: Path) -> None:
        if not skills_dir.exists():
            return
        for entry in sorted(skills_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            skill_file = entry / "SKILL.md"
            if not skill_file.exists():
                continue
            skill = self._parse_skill(skill_file, entry)
            if skill:
                self._skills.append(skill)

    def _parse_skill(self, skill_file: Path, skill_dir: Path) -> SkillDef | None:
        content = skill_file.read_text(encoding="utf-8")
        meta = self._parse_frontmatter(content)
        if not meta:
            return None

        body = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, flags=re.DOTALL).strip()

        prompt_file = skill_dir / "prompt.md"
        prompt_content = ""
        if prompt_file.exists():
            prompt_content = prompt_file.read_text(encoding="utf-8")
        elif body:
            prompt_content = body

        return SkillDef(
            name=meta.get("name", skill_dir.name),
            description=meta.get("description", ""),
            triggers=meta.get("triggers", []),
            constraints=meta.get("constraints", []),
            allowed_tools=meta.get("allowed_tools", []),
            priority=meta.get("priority", 0),
            prompt_content=prompt_content,
            dir_path=skill_dir,
        )

    def _parse_frontmatter(self, content: str) -> dict:
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}
        try:
            return yaml.safe_load(match.group(1)) or {}
        except Exception:
            return {}

    def match(self, user_message: str, top_n: int = 3) -> list[SkillDef]:
        scored: list[tuple[float, SkillDef]] = []
        message_lower = user_message.lower()

        for skill in self._skills:
            score = 0.0
            for trigger in skill.triggers:
                if trigger.lower() in message_lower:
                    score += 10.0
            score += skill.priority
            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:top_n]]

    def build_skill_context(self, matched_skills: list[SkillDef]) -> str:
        if not matched_skills:
            return ""
        parts = []
        for skill in matched_skills:
            parts.append(f"## Skill: {skill.name}\n\n{skill.prompt_content}")
            if skill.constraints:
                parts.append("### Constraints\n" + "\n".join(f"- {c}" for c in skill.constraints))
        return "\n\n".join(parts)

    def get_allowed_tools(self, matched_skills: list[SkillDef]) -> list[str] | None:
        """Return merged tool allowlist from matched skills, or None if no restriction."""
        tools: set[str] = set()
        has_restriction = False
        for skill in matched_skills:
            if skill.allowed_tools:
                has_restriction = True
                tools.update(skill.allowed_tools)
        if not has_restriction:
            return None
        return list(tools)

    @property
    def all_skills(self) -> list[SkillDef]:
        return list(self._skills)

    def skills_snapshot(self) -> str:
        if not self._skills:
            return ""
        lines = ["Available skills:"]
        for s in self._skills:
            triggers_str = ", ".join(s.triggers[:5])
            lines.append(f"- {s.name}: {s.description} (triggers: {triggers_str})")
        return "\n".join(lines)
