import json
from typing import Any, Dict, List

from tools.filesystem import read_file, write_file, search_files
from tools.shell import execute_shell
from tools.python_exec import execute_python
from tools.screenshot import capture_screenshot
from tools.web import web_search, scrape_webpage
import tools.memory_tools as _mt
import tools.skill_tools as _st


def init_memory_tools(memory_manager) -> None:
    """Inject a MemoryManager instance so memory tools become operational."""
    _mt._memory_manager = memory_manager


def init_skill_tools(skill_manager) -> None:
    """Inject a SkillManager instance so skill tools become operational."""
    _st._skill_manager = skill_manager


TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read (supports ~ expansion).",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8).",
                        "default": "utf-8",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or append content to a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["w", "a"],
                        "description": "Write mode: 'w' to overwrite, 'a' to append (default: w).",
                        "default": "w",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files by glob pattern, optionally filtering by regex content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match file names (e.g., '**/*.py').",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in (default: current directory).",
                        "default": ".",
                    },
                    "search_content": {
                        "type": "string",
                        "description": "Optional regex pattern to filter files by content.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_shell",
            "description": "Execute a shell command and return stdout/stderr. Timeout: 30 seconds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 30, max: 30).",
                        "default": 30,
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute a Python code snippet in a subprocess sandbox. Timeout: 15 seconds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 15, max: 15).",
                        "default": 15,
                    },
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo. Returns title, URL, and snippet for each result.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_webpage",
            "description": "Fetch a webpage and extract the main text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the webpage to scrape.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Request timeout in seconds (default: 15).",
                        "default": 15,
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "capture_screenshot",
            "description": "Capture a screenshot of the current screen (macOS only). Returns base64-encoded PNG.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_width": {
                        "type": "integer",
                        "description": "Maximum width in pixels to resize the screenshot (default: 1920).",
                        "default": 1920,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_memory",
            "description": (
                "Read the long-term memory file (memory.md). "
                "Use this to recall facts, preferences, and notes stored across sessions."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_memory",
            "description": (
                "Overwrite the long-term memory file (memory.md) with new content. "
                "Use this to completely replace the memory with an updated version. "
                "IMPORTANT: include all existing entries you want to keep."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Full new content for memory.md (Markdown format recommended).",
                    }
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_memory",
            "description": (
                "Append a new entry to the long-term memory file (memory.md) "
                "without erasing existing content. Use for adding new facts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Text to append to memory.md.",
                    }
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_skills",
            "description": (
                "List all available skills with their descriptions. "
                "Shows which skills are currently loaded in this session."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": (
                "Load a skill into the active session. "
                "Once loaded, the skill's instructions appear in the system prompt "
                "and guide your behaviour for that skill type."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the skill to load (must exist in the skills directory).",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unload_skill",
            "description": "Remove a skill from the active session so its instructions no longer appear in the system prompt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the skill to unload.",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_skill",
            "description": (
                "Create a new skill file at skills/<name>/SKILL.md. "
                "The content should be a Markdown document with a YAML front-matter block "
                "containing a 'description' field, followed by instructions for the skill."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Skill name (used as directory name, e.g. 'code_review').",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full SKILL.md content in Markdown format with YAML front-matter.",
                    },
                },
                "required": ["name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_skill",
            "description": (
                "Overwrite an existing skill file with new content. "
                "If the skill is currently loaded, the in-session copy is also refreshed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the skill to update.",
                    },
                    "content": {
                        "type": "string",
                        "description": "New full content for the SKILL.md file.",
                    },
                },
                "required": ["name", "content"],
            },
        },
    },
]

_TOOL_REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
    "search_files": search_files,
    "execute_shell": execute_shell,
    "execute_python": execute_python,
    "web_search": web_search,
    "scrape_webpage": scrape_webpage,
    "capture_screenshot": capture_screenshot,
    "read_memory": _mt.read_memory,
    "update_memory": _mt.update_memory,
    "append_memory": _mt.append_memory,
    "list_skills": _st.list_skills,
    "load_skill": _st.load_skill,
    "unload_skill": _st.unload_skill,
    "create_skill": _st.create_skill,
    "update_skill": _st.update_skill,
}


def dispatch_tool(name: str, arguments: str) -> str:
    """Parse tool arguments and dispatch to the appropriate tool function."""
    if name not in _TOOL_REGISTRY:
        return f"Error: Unknown tool '{name}'"
    try:
        kwargs = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError as e:
        return f"Error: Invalid tool arguments JSON: {e}"
    try:
        return str(_TOOL_REGISTRY[name](**kwargs))
    except TypeError as e:
        return f"Error: Invalid arguments for tool '{name}': {e}"
    except Exception as e:
        return f"Error executing tool '{name}': {e}"
