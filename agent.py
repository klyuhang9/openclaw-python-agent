import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import AgentConfig
from history import ConversationHistory
from memory import MemoryManager
from skills import SkillManager
from tools import TOOL_SCHEMAS, dispatch_tool, init_memory_tools, init_skill_tools
import tools.skill_tools as _st
from ui.display import Display


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(content: Optional[str]) -> str:
    """Remove <think>...</think> blocks from model output."""
    if not content:
        return ""
    return _THINK_RE.sub("", content).strip()


class Agent:
    """Core agent loop: multi-turn conversation with parallel tool calling."""

    def __init__(self, config: Optional[AgentConfig] = None, display: Optional[Display] = None):
        self.config = config or AgentConfig()
        self.display = display or Display()
        self.history = ConversationHistory(max_messages=self.config.max_history_messages)
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key="EMPTY",  # vLLM doesn't require a real key
        )
        self.last_prompt_tokens: int = 0  # updated after every LLM call

        # Memory
        self.memory = MemoryManager(memory_dir=self.config.memory_dir)
        init_memory_tools(self.memory)
        self._long_term_memory: str = self.memory.load_long_term()

        # Skills
        self.skill_manager = SkillManager(skills_dir=self.config.skills_dir)
        init_skill_tools(self.skill_manager)

        # Tools doc
        self._tools_doc: str = self._load_tools_doc()

    def chat(self, user_content: Any) -> str:
        """
        Send a user message and run the agent loop until a final answer.

        user_content can be:
          - str: plain text
          - list: multimodal content (OpenAI content array format)
        """
        self.history.append({"role": "user", "content": user_content})

        for iteration in range(self.config.max_tool_iterations):
            self._enforce_token_budget()
            messages = self._build_messages()

            with self.display.spinner("Thinking..." if iteration == 0 else "Continuing..."):
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )

            if response.usage:
                self.last_prompt_tokens = response.usage.prompt_tokens

            choice = response.choices[0]
            finish_reason = choice.finish_reason
            message = choice.message

            if finish_reason == "tool_calls" or (
                finish_reason == "stop" and message.tool_calls
            ):
                # Append assistant message with tool calls
                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": _strip_thinking(message.content) or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
                self.history.append(assistant_msg)

                # Execute all tool calls in parallel
                tool_calls = message.tool_calls
                results: Dict[str, str] = {}

                def _run_tool(tc):
                    name = tc.function.name
                    args = tc.function.arguments
                    self.display.show_tool_call(name, args)
                    result = dispatch_tool(name, args)
                    return tc.id, name, result

                with ThreadPoolExecutor(max_workers=min(len(tool_calls), 4)) as executor:
                    futures = [executor.submit(_run_tool, tc) for tc in tool_calls]
                    for future in as_completed(futures):
                        tc_id, name, result = future.result()
                        results[tc_id] = (name, result)

                # Append tool results in original order
                for tc in tool_calls:
                    name, result = results[tc.id]
                    self.display.show_tool_result(name, result)
                    if name == "capture_screenshot" and not result.startswith("Error:"):
                        # Send as multimodal content so the model can see the image
                        content: Any = [
                            {"type": "text", "text": "Screenshot captured successfully."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{result}"},
                            },
                        ]
                    else:
                        content = result
                        # Truncate large text results before storing in history
                        limit = self.config.max_tool_result_chars
                        if isinstance(content, str) and len(content) > limit:
                            content = content[:limit] + f"\n...[truncated: {len(content)} chars total]"
                    self.history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": content,
                            "_tool_name": name,  # internal tag for pruning
                        }
                    )

            else:
                # Final answer
                answer = _strip_thinking(message.content) or ""
                self.history.append({"role": "assistant", "content": answer})
                # Prune screenshot base64 from history to keep context lean
                self._prune_screenshot_messages()
                return answer

        return "Error: Maximum tool iterations reached without a final answer."

    def clear_history(self, save: bool = True) -> Optional[str]:
        """Clear the conversation history, optionally saving the session first."""
        saved_path = None
        if save:
            saved_path = self.memory.save_session(self.history.get_messages())
        self.history.clear()
        # Reload long-term memory in case it was updated during the session
        self._long_term_memory = self.memory.load_long_term()
        return saved_path

    def save_session(self) -> Optional[str]:
        """Save the current conversation to a dated session file."""
        return self.memory.save_session(self.history.get_messages())

    def _prune_screenshot_messages(self) -> None:
        """Replace screenshot base64 payloads in history with a short placeholder."""
        for msg in self.history._messages:
            if msg.get("_tool_name") == "capture_screenshot" and isinstance(msg.get("content"), list):
                msg["content"] = "[screenshot: analyzed and removed to save context]"

    def _enforce_token_budget(self) -> None:
        """Trim history so the estimated total context fits within the model's token window."""
        # Estimate chars used by the fixed parts of the system prompt (1 token ≈ 3 chars)
        system_chars = (
            len(self.config.system_prompt)
            + len(self._tools_doc)
            + len(self._long_term_memory)
            + len(self.skill_manager.get_skills_summary())
            + sum(len(c) for c in _st._active_skills.values())
        )
        response_headroom_chars = self.config.max_tokens * 3
        total_budget_chars = self.config.max_context_tokens * 3
        history_budget_chars = total_budget_chars - system_chars - response_headroom_chars
        if history_budget_chars > 0:
            self.history.trim_to_token_budget(history_budget_chars)

    def _load_tools_doc(self) -> str:
        """Load the tools description file, return empty string if not found."""
        from pathlib import Path
        p = Path(self.config.tools_doc)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""

    def _build_messages(self) -> List[Dict[str, Any]]:
        """Build the full messages list with system prompt (+ tools + memory + skills) prepended."""
        system_content = self.config.system_prompt

        # Inject tools documentation
        if self._tools_doc:
            system_content += "\n\n" + self._tools_doc

        if self._long_term_memory:
            system_content += (
                "\n\n## Long-term Memory\n"
                "The following notes persist across sessions. "
                "Use them to personalise responses and recall past context.\n\n"
                + self._long_term_memory
            )
        # Inject available skills summary
        skills_summary = self.skill_manager.get_skills_summary()
        if skills_summary:
            system_content += "\n\n" + skills_summary

        # Inject active skill contents
        for skill_name, skill_content in _st._active_skills.items():
            system_content += f"\n\n## Active Skill: {skill_name}\n{skill_content}"

        system_msg = {"role": "system", "content": system_content}
        clean = []
        for msg in self.history.get_messages():
            # Strip internal bookkeeping keys before sending to API
            clean.append({k: v for k, v in msg.items() if not k.startswith("_")})
        return [system_msg] + clean
