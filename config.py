from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    base_url: str = "http://10.72.8.19:8001/v1"
    model: str = "qwen3-397b"
    timeout: int = 120
    max_tool_iterations: int = 20
    max_history_messages: int = 40  # sliding window size
    temperature: float = 0.7
    max_tokens: int = 4096
    max_context_tokens: int = 262144   # qwen3-397b context window
    memory_dir: str = "memory"         # directory for long-term and session memory
    skills_dir: str = "skills"         # directory for skill files
    tools_doc: str = "tools.md"        # path to the tools description file
    max_tool_result_chars: int = 8000  # truncate individual tool results stored in history
    system_prompt: str = (
        "You are a helpful AI assistant. "
        "Be concise and accurate in your responses."
    )
