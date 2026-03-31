import os
import glob
import re
from typing import Optional


def read_file(path: str, encoding: str = "utf-8") -> str:
    """Read the contents of a local file."""
    try:
        abs_path = os.path.expanduser(path)
        with open(abs_path, "r", encoding=encoding) as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str, mode: str = "w") -> str:
    """Write or append content to a local file."""
    try:
        abs_path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(abs_path) if os.path.dirname(abs_path) else ".", exist_ok=True)
        with open(abs_path, mode, encoding="utf-8") as f:
            f.write(content)
        action = "appended to" if mode == "a" else "written to"
        return f"Successfully {action} {path} ({len(content)} characters)"
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def search_files(pattern: str, directory: str = ".", search_content: Optional[str] = None) -> str:
    """Search for files by glob pattern, optionally filtering by regex content."""
    try:
        abs_dir = os.path.expanduser(directory)
        full_pattern = os.path.join(abs_dir, pattern)
        matches = glob.glob(full_pattern, recursive=True)

        if not matches:
            return f"No files found matching pattern '{pattern}' in '{directory}'"

        if search_content:
            filtered = []
            regex = re.compile(search_content)
            for filepath in matches:
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        if regex.search(f.read()):
                            filtered.append(filepath)
                except Exception:
                    pass
            matches = filtered
            if not matches:
                return f"No files matching pattern '{pattern}' contain '{search_content}'"

        return "\n".join(matches[:100])  # limit to 100 results
    except Exception as e:
        return f"Error searching files: {e}"
