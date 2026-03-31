import subprocess
import sys
import tempfile
import os


def execute_python(code: str, timeout: int = 15) -> str:
    """Execute a Python code snippet in a subprocess sandbox."""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output_parts = []
            if result.stdout:
                output_parts.append(f"Output:\n{result.stdout}")
            if result.stderr:
                output_parts.append(f"Stderr:\n{result.stderr}")
            output_parts.append(f"Return code: {result.returncode}")
            return "\n".join(output_parts) if output_parts else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Error: Python execution timed out after {timeout} seconds"
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        return f"Error executing Python code: {e}"
