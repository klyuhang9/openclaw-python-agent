import json
from typing import Any, Dict, List

from tools.filesystem import read_file, write_file, search_files
from tools.shell import execute_shell
from tools.python_exec import execute_python
from tools.screenshot import capture_screenshot
from tools.web import web_search, scrape_webpage
from tools.browser import (
    browser_navigate,
    browser_snapshot,
    browser_click,
    browser_type,
    browser_upload,
    browser_screenshot,
    browser_scroll,
    browser_press_key,
    browser_click_text,
    browser_upload_file,
    browser_click_selector,
)
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
    # ── Browser automation ────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Open a URL in the browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL to navigate to"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_snapshot",
            "description": (
                "Take a snapshot of the current browser page. "
                "Returns title, URL, and a numbered list of interactive elements "
                "with refs (e1, e2, …). Use refs with browser_click / browser_type / browser_upload."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "Click an element on the current page using its ref from the last snapshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "Element ref, e.g. 'e3'"},
                },
                "required": ["ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_type",
            "description": "Type text into an input or textarea using its ref from the last snapshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref":   {"type": "string",  "description": "Element ref, e.g. 'e5'"},
                    "text":  {"type": "string",  "description": "Text to type"},
                    "clear": {"type": "boolean", "description": "Clear existing content first (default true)", "default": True},
                },
                "required": ["ref", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_upload",
            "description": "Upload a local file to a file-input element using its ref from the last snapshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref":       {"type": "string", "description": "Element ref of the file input, e.g. 'e7'"},
                    "file_path": {"type": "string", "description": "Absolute path to the local file to upload"},
                },
                "required": ["ref", "file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": "Take a screenshot of the current browser page to visually inspect its state.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_scroll",
            "description": "Scroll the current browser page. Use for lazy-loaded feeds or revealing off-screen buttons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["down", "up", "top", "bottom"],
                        "description": "Scroll direction (default: down)",
                        "default": "down",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Pixels to scroll (default: 600, ignored for top/bottom)",
                        "default": 600,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click_selector",
            "description": (
                "Click an element by CSS selector, optionally at a specific "
                "pixel position WITHIN the element. Use when snapshot can't "
                "see internal structure (closed shadow DOM web components, e.g. "
                "xiaohongshu's <xhs-publish-btn>). position_x / position_y are "
                "offsets from the element's top-left corner. Pass -1 to click center."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector, e.g. 'xhs-publish-btn'"},
                    "position_x": {"type": "number", "description": "X offset within element (-1 = center)", "default": -1},
                    "position_y": {"type": "number", "description": "Y offset within element (-1 = center)", "default": -1},
                },
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_upload_file",
            "description": (
                "Upload a local file to the page's hidden <input type=file>. "
                "Use this for xiaohongshu / douyin upload UIs where snapshot can't "
                "see the file input (it's hidden behind a styled button). "
                "accept_hint can disambiguate when multiple inputs exist "
                "(e.g. 'image' or '.jpg' to prefer the image one)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path to the local file"},
                    "accept_hint": {"type": "string", "description": "Optional accept-attr substring to disambiguate, e.g. 'image' or '.jpg'", "default": ""},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click_text",
            "description": (
                "Click the first visible element with the given text. Use this "
                "as a fallback when snapshot doesn't show the element (e.g. "
                "div-based buttons in React/Vue SPAs). Pierces shadow DOM and "
                "iframes automatically."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Visible text to match, e.g. '上传图文'"},
                    "exact": {"type": "boolean", "description": "Require exact match (default false: substring)", "default": False},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_press_key",
            "description": "Press a keyboard key on the page (e.g. 'Enter', 'Escape', 'Tab', 'ArrowDown'). Useful for confirming dialogs or submitting forms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name, e.g. 'Enter'"},
                },
                "required": ["key"],
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
    "browser_navigate":   browser_navigate,
    "browser_snapshot":   browser_snapshot,
    "browser_click":      browser_click,
    "browser_type":       browser_type,
    "browser_upload":     browser_upload,
    "browser_screenshot": browser_screenshot,
    "browser_scroll":     browser_scroll,
    "browser_press_key":  browser_press_key,
    "browser_click_text": browser_click_text,
    "browser_upload_file": browser_upload_file,
    "browser_click_selector": browser_click_selector,
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
