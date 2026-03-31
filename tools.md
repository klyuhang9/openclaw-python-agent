## Tools

You have access to the following tools. Use them whenever they help accomplish the user's request.

### File System

- **read_file** `path [encoding]` — Read the contents of a local file. Supports `~` expansion.
- **write_file** `path content [mode]` — Write or append content to a file. `mode` is `w` (overwrite, default) or `a` (append). Parent directories are created automatically.
- **search_files** `pattern [directory] [search_content]` — Find files by glob pattern (e.g. `**/*.py`). Optionally filter results by a regex matched against file content.

### Shell

- **execute_shell** `command [timeout]` — Run a shell command and return stdout, stderr, and exit code. Timeout default is 30 seconds.

### Python

- **execute_python** `code [timeout]` — Execute a Python snippet in a subprocess sandbox and return its output. Timeout default is 15 seconds.

### Web

- **web_search** `query [max_results]` — Search the web via DuckDuckGo. Returns title, URL, and snippet for each result (default: 5 results).
- **scrape_webpage** `url [timeout]` — Fetch a URL and extract the main text content. Timeout default is 15 seconds.

### Screenshot

- **capture_screenshot** `[max_width]` — Capture the current screen (macOS only) and return a base64-encoded JPEG. The image is automatically sent to you as a vision input so you can describe or analyse it.

### Memory

- **read_memory** — Read the long-term memory file (`memory.md`). Use this to recall facts, preferences, and notes saved across sessions.
- **update_memory** `content` — Overwrite `memory.md` with new content. Include all entries you want to keep.
- **append_memory** `content` — Append a new entry to `memory.md` without erasing existing content.

### Skills

- **list_skills** — List all available skills with their descriptions and indicate which are currently loaded.
- **load_skill** `name` — Load a skill into the active session. Its full instructions will appear in the system prompt and guide your behaviour for that task type.
- **unload_skill** `name` — Remove a skill from the active session.
- **create_skill** `name content` — Create a new skill file at `skills/<name>/SKILL.md`. Use YAML front-matter with a `description` field followed by Markdown instructions.
- **update_skill** `name content` — Overwrite an existing skill file. If the skill is currently loaded, the in-session copy is refreshed immediately.
