from __future__ import annotations

from pathlib import Path


class PromptBuilder:
    def __init__(self, prompt_dir: Path):
        self._prompt_dir = prompt_dir

    def _read_file(self, filename: str) -> str:
        path = self._prompt_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        return ""

    def build(
        self,
        memory_summary: str = "",
        skills_snapshot: str = "",
        skill_context: str = "",
        tool_names: list[str] | None = None,
    ) -> str:
        layers: list[str] = []

        # Layer 1: Identity
        identity = self._read_file("identity.md")
        if identity:
            layers.append(identity)

        # Layer 2: Rules
        rules = self._read_file("rules.md")
        if rules:
            layers.append(rules)

        # Layer 3: Memory
        if memory_summary:
            layers.append(f"## Recent Context\n\n{memory_summary}")

        # Layer 4: Skills snapshot
        if skills_snapshot:
            layers.append(f"## {skills_snapshot}")

        # Layer 5: Active skill context
        if skill_context:
            layers.append(f"## Active Skill Instructions\n\n{skill_context}")

        # Layer 6: Tool allowlist
        if tool_names:
            tool_list = ", ".join(tool_names)
            layers.append(f"## Available Tools\n\nYou have access to: {tool_list}")

        return "\n\n---\n\n".join(layers)
