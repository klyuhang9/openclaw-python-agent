"""
Memory tools: read and update the long-term memory.md file.
The MemoryManager instance is injected at import time by tools/__init__.py.
"""

from typing import Optional

# Injected by tools/__init__.py after the agent is created
_memory_manager = None


def _get_mm():
    if _memory_manager is None:
        raise RuntimeError("MemoryManager not initialised in memory_tools")
    return _memory_manager


def read_memory() -> str:
    """Read the current long-term memory (memory.md)."""
    content = _get_mm().load_long_term()
    if not content:
        return "(memory.md is empty — no long-term memory stored yet)"
    return content


def update_memory(content: str) -> str:
    """Overwrite memory.md with the given content (full replace)."""
    _get_mm().save_long_term(content)
    return "Long-term memory updated successfully."


def append_memory(content: str) -> str:
    """Append a new entry to memory.md without erasing existing content."""
    _get_mm().append_long_term(content)
    return "Entry appended to long-term memory."
