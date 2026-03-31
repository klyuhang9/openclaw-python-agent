import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class MemoryManager:
    """
    File-based long-term and session memory.

    Structure:
        memory/
        ├── memory.md           # Long-term memory, injected into system prompt each session
        └── YYYY-MM-DD/
            ├── session_1.md    # Saved when /clear or exit is triggered
            └── session_2.md
    """

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.long_term_path = self.memory_dir / "memory.md"

    # ------------------------------------------------------------------
    # Long-term memory
    # ------------------------------------------------------------------

    def load_long_term(self) -> str:
        """Return the content of memory.md, or empty string if it doesn't exist."""
        if self.long_term_path.exists():
            return self.long_term_path.read_text(encoding="utf-8").strip()
        return ""

    def save_long_term(self, content: str) -> None:
        """Overwrite memory.md with new content."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.long_term_path.write_text(content, encoding="utf-8")

    def append_long_term(self, content: str) -> None:
        """Append a line to memory.md."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        with open(self.long_term_path, "a", encoding="utf-8") as f:
            f.write(f"\n{content}")

    # ------------------------------------------------------------------
    # Session memory
    # ------------------------------------------------------------------

    def save_session(self, messages: List[Dict[str, Any]]) -> str:
        """
        Save the current conversation to a dated session file.
        Returns the path of the saved file, or empty string if nothing to save.
        """
        # Filter to only user/assistant exchanges (skip tool messages)
        turns = [
            m for m in messages
            if m["role"] in ("user", "assistant")
            and isinstance(m.get("content"), str)
            and m.get("content", "").strip()
        ]
        if not turns:
            return ""

        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.memory_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        # Auto-increment session number
        existing = sorted(date_dir.glob("session_*.md"))
        session_num = len(existing) + 1
        session_path = date_dir / f"session_{session_num}.md"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [f"# Session {session_num} — {timestamp}\n"]
        for msg in turns:
            role_label = "**User**" if msg["role"] == "user" else "**Assistant**"
            lines.append(f"## {role_label}\n\n{msg['content']}\n")

        session_path.write_text("\n".join(lines), encoding="utf-8")
        return str(session_path)

    def list_sessions(self, date_str: str = None) -> List[str]:
        """List session files for a given date (default: today)."""
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        date_dir = self.memory_dir / date_str
        if not date_dir.exists():
            return []
        return sorted(str(p) for p in date_dir.glob("session_*.md"))
