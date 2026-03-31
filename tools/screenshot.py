import subprocess
import base64
import tempfile
import os

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def capture_screenshot(max_width: int = 960) -> str:
    """Capture a screenshot (macOS), resize to max_width, return as base64 JPEG."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_png = f.name
        tmp_jpg = tmp_png.replace(".png", ".jpg")

        try:
            result = subprocess.run(
                ["screencapture", "-x", tmp_png],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                return f"Error: screencapture failed: {result.stderr.decode()}"

            if HAS_PIL:
                img = Image.open(tmp_png).convert("RGB")
                w, h = img.size
                if w > max_width:
                    ratio = max_width / w
                    new_size = (max_width, int(h * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                img.save(tmp_jpg, "JPEG", quality=80, optimize=True)
                out_path = tmp_jpg
            else:
                out_path = tmp_png

            with open(out_path, "rb") as f:
                data = f.read()

            b64 = base64.b64encode(data).decode("utf-8")
            return b64
        finally:
            for p in (tmp_png, tmp_jpg):
                if os.path.exists(p):
                    os.unlink(p)
    except FileNotFoundError:
        return "Error: screencapture not available (macOS only)"
    except Exception as e:
        return f"Error capturing screenshot: {e}"
