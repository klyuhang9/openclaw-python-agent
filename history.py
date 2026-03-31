from typing import List, Dict, Any


class ConversationHistory:
    """Sliding window conversation history that preserves tool call pairing integrity."""

    def __init__(self, max_messages: int = 40):
        self.max_messages = max_messages
        self._messages: List[Dict[str, Any]] = []

    def append(self, message: Dict[str, Any]) -> None:
        self._messages.append(message)
        self._maybe_truncate()

    def get_messages(self) -> List[Dict[str, Any]]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages = []

    def trim_to_token_budget(self, budget_chars: int) -> None:
        """Remove oldest messages until total content fits within budget_chars."""
        while self._total_chars() > budget_chars and len(self._messages) > 1:
            if not self._drop_oldest():
                break

    def _total_chars(self) -> int:
        total = 0
        for msg in self._messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total += len(part.get("text", ""))
        return total

    def _drop_oldest(self) -> bool:
        """Remove the oldest non-system message (atomically for tool call chains). Returns False if nothing left to drop."""
        start = 0
        while start < len(self._messages) and self._messages[start]["role"] == "system":
            start += 1
        if start >= len(self._messages):
            return False
        msg = self._messages[start]
        if msg["role"] == "assistant" and msg.get("tool_calls"):
            tool_call_ids = {tc["id"] for tc in msg["tool_calls"]}
            end = start + 1
            while end < len(self._messages):
                m = self._messages[end]
                if m["role"] == "tool" and m.get("tool_call_id") in tool_call_ids:
                    tool_call_ids.discard(m["tool_call_id"])
                    end += 1
                else:
                    break
            del self._messages[start:end]
        else:
            del self._messages[start]
        return True

    def _maybe_truncate(self) -> None:
        """Remove messages when over limit, always removing assistant+tool pairs atomically."""
        while len(self._messages) > self.max_messages:
            if not self._drop_oldest():
                break
