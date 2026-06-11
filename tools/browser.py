"""
Browser automation tool using Playwright.
Provides navigate / snapshot / click / type / upload / screenshot / scroll /
press_key capabilities.

Uses a persistent Chromium user-data directory at ~/.cli-agent/browser-profile/
so cookies and login state survive across agent restarts. This is what lets
the agent post to sites like Douyin / Xiaohongshu after a one-time login.
"""

import base64
import os
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from typing import Any, Callable

PROFILE_DIR = Path.home() / ".cli-agent" / "browser-profile"

_state: dict = {
    "pw": None,
    "context": None,
    "page": None,
}

# Playwright's sync API is thread-affine: every call must come from the thread
# that started sync_playwright(). The agent's tool dispatcher uses a parallel
# ThreadPoolExecutor, which would land successive browser calls on different
# workers and crash with "cannot switch to a different thread". We pin all
# Playwright work to one dedicated worker thread.
_pw_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pw")


def _on_pw_thread(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return _pw_executor.submit(fn, *args, **kwargs).result()
    return wrapper

# Snapshot JS. Takes a starting `offset` so the caller can assign globally
# unique refs across multiple frames.
#
# Detection strategy (matches what xiaohongshu / douyin actually ship):
#   1. Standard interactive tags + ARIA roles + contenteditable.
#   2. Any element whose computed `cursor` is `pointer` — this catches
#      `<div>`-based buttons that React/Vue apps build with dynamic
#      onclick listeners (the listeners themselves are invisible to JS).
#   3. Walks open shadow roots (some web-component-based UIs use them).
# Then dedupes: if both an element and its descendant match, keep only the
# innermost text-bearing one.
_SNAPSHOT_JS = """
(offset) => {
    const STRICT_SEL = [
        'input:not([type="hidden"])',
        'button',
        'textarea',
        'select',
        'a[href]',
        '[role="button"]',
        '[role="tab"]',
        '[role="menuitem"]',
        '[role="link"]',
        '[contenteditable="true"]',
    ].join(', ');

    function walk(root, out) {
        // Strict matches
        for (const el of root.querySelectorAll(STRICT_SEL)) out.add(el);
        // Cursor-pointer matches (catches <div onclick=...> in SPAs)
        for (const el of root.querySelectorAll('*')) {
            try {
                if (getComputedStyle(el).cursor === 'pointer') out.add(el);
            } catch (e) { /* detached element */ }
            if (el.shadowRoot) walk(el.shadowRoot, out);
        }
    }

    const candidates = new Set();
    walk(document, candidates);

    // Visible only — and not at the typical "hidden clone" coords. Some SPAs
    // keep template duplicates at (-9999, -9999) for measurement; their
    // cursor:pointer trips up our detector and any click on them times out
    // with "outside of viewport". Keep elements that might need scrolling
    // (small negative or below the fold), reject elements clearly thrown
    // into the offscreen void.
    let arr = [...candidates].filter(el => {
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) return false;
        if (r.left < -2000 || r.top < -2000) return false;
        if (r.left > 5000 || r.top > 50000) return false;
        const style = getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none') return false;
        if (parseFloat(style.opacity) === 0) return false;
        return true;
    });

    // Dedupe: if an element contains another visible candidate, drop the outer
    // (we want the innermost interactive node, e.g. the <span>上传图文</span>
    // inside a wrapping <div>).
    const set = new Set(arr);
    arr = arr.filter(el => {
        for (const other of set) {
            if (other !== el && el.contains(other)) return false;
        }
        return true;
    });

    // Sort by document position so refs are stable visually.
    arr.sort((a, b) => {
        const pos = a.compareDocumentPosition(b);
        if (pos & Node.DOCUMENT_POSITION_FOLLOWING) return -1;
        if (pos & Node.DOCUMENT_POSITION_PRECEDING) return 1;
        return 0;
    });

    arr.forEach((el, i) => el.setAttribute('data-agent-ref', String(offset + i + 1)));

    return arr.map((el, i) => ({
        ref:          offset + i + 1,
        tag:          el.tagName.toLowerCase(),
        type:         el.type || '',
        text:         (el.innerText || el.textContent || '').trim().slice(0, 80),
        placeholder:  el.placeholder || '',
        value:        (el.value || '').slice(0, 50),
        ariaLabel:    el.getAttribute('aria-label') || '',
        id:           el.id || '',
        role:         el.getAttribute('role') || '',
        href:         el.tagName === 'A' ? (el.getAttribute('href') || '') : '',
        editable:     el.getAttribute('contenteditable') || '',
    }));
}
"""


def _locate_in_frames(page, ref_num: str):
    """Find a [data-agent-ref="N"] locator across the main frame and all child
    frames. Returns (locator, frame) or (None, None) if not found."""
    for frame in page.frames:
        try:
            loc = frame.locator(f'[data-agent-ref="{ref_num}"]')
            if loc.count() > 0:
                return loc, frame
        except Exception:
            continue
    return None, None


def _get_page():
    """Return (page, error_str). Creates a persistent browser context if needed."""
    if _state["page"] is not None and not _state["page"].is_closed():
        return _state["page"], None

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "Error: playwright not installed. Run: /usr/bin/python3 -m pip install playwright && /usr/bin/python3 -m playwright install chromium"

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    if _state["context"] is None:
        _state["pw"] = sync_playwright().start()
        headless = os.environ.get("CLI_AGENT_BROWSER_HEADLESS", "").lower() in ("1", "true", "yes")
        _state["context"] = _state["pw"].chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )

    pages = _state["context"].pages
    _state["page"] = pages[0] if pages else _state["context"].new_page()
    return _state["page"], None


@_on_pw_thread
def browser_navigate(url: str) -> str:
    """Navigate the browser to a URL."""
    page, err = _get_page()
    if err:
        return err
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # SPAs (xiaohongshu / douyin) keep loading after DOMContentLoaded.
        # Wait briefly for the network to settle so iframes attach.
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        page.wait_for_timeout(800)
        return f"Navigated to: {page.url}\nTitle: {page.title()}"
    except Exception as e:
        return f"Error navigating to {url}: {e}"


@_on_pw_thread
def browser_snapshot() -> str:
    """
    Snapshot the current page across the main frame AND all child iframes.
    Returns title, URL, and a numbered list of interactive elements with refs
    (e1, e2, …). Refs are globally unique. Use them with browser_click /
    browser_type / browser_upload — those helpers will find the right frame
    automatically.
    """
    page, err = _get_page()
    if err:
        return err
    try:
        page.wait_for_load_state("domcontentloaded")
        title = page.title()
        url = page.url

        all_elements: list = []
        frame_summaries: list[str] = []
        offset = 0
        for f_idx, frame in enumerate(page.frames):
            try:
                els = frame.evaluate(_SNAPSHOT_JS, offset)
            except Exception:
                continue
            if not els:
                continue
            for el in els:
                el["_frame_idx"] = f_idx
            all_elements.extend(els)
            frame_summaries.append(
                f"  (frame {f_idx}: {len(els)} els, url={frame.url[:80]})"
            )
            offset += len(els)

        lines = [
            f"Title: {title}",
            f"URL: {url}",
            f"Elements ({len(all_elements)} interactive across {len(frame_summaries)} frame(s)):",
        ]
        if len(frame_summaries) > 1:
            lines.extend(frame_summaries)
        for el in all_elements:
            ref = f"e{el['ref']}"
            parts = [f"[{ref}]", el["tag"]]
            if el["type"] and el["type"] not in ("", "button", "submit", "text"):
                parts.append(f'type={el["type"]}')
            label = el["text"] or el["ariaLabel"] or el["placeholder"] or el["value"]
            if label:
                parts.append(f'"{label[:60]}"')
            if el["id"]:
                parts.append(f'id={el["id"]}')
            if el["href"]:
                parts.append(f'href={el["href"][:60]}')
            if el["editable"]:
                parts.append("(editable)")
            if el.get("_frame_idx", 0) > 0:
                parts.append(f"(frame {el['_frame_idx']})")
            lines.append("  " + " ".join(parts))
        return "\n".join(lines)
    except Exception as e:
        return f"Error taking snapshot: {e}"


@_on_pw_thread
def browser_click(ref: str) -> str:
    """Click an element identified by a ref from the last snapshot (e.g. 'e3').
    Searches all frames for the ref."""
    page, err = _get_page()
    if err:
        return err
    ref_num = ref.lstrip("eE")
    try:
        loc, frame = _locate_in_frames(page, ref_num)
        if loc is None:
            return f"Error clicking {ref}: element not found in any frame (re-snapshot first)"
        loc.click(timeout=10000)
        page.wait_for_timeout(600)
        return f"Clicked {ref}" + (f" (frame {page.frames.index(frame)})" if frame != page.main_frame else "")
    except Exception as e:
        return f"Error clicking {ref}: {e}"


@_on_pw_thread
def browser_type(ref: str, text: str, clear: bool = True) -> str:
    """
    Type text into an input/textarea identified by ref.
    Set clear=true (default) to clear existing content first.
    Searches all frames for the ref.
    """
    page, err = _get_page()
    if err:
        return err
    ref_num = ref.lstrip("eE")
    try:
        loc, frame = _locate_in_frames(page, ref_num)
        if loc is None:
            return f"Error typing into {ref}: element not found in any frame (re-snapshot first)"
        loc.click(timeout=10000)
        if clear:
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")
        loc.type(text, delay=20)
        return f"Typed into {ref}"
    except Exception as e:
        return f"Error typing into {ref}: {e}"


@_on_pw_thread
def browser_upload(ref: str, file_path: str) -> str:
    """Upload a local file to a file-input element identified by ref.
    Searches all frames for the ref."""
    page, err = _get_page()
    if err:
        return err
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    ref_num = ref.lstrip("eE")
    try:
        loc, frame = _locate_in_frames(page, ref_num)
        if loc is None:
            return f"Error uploading to {ref}: element not found in any frame (re-snapshot first)"
        loc.set_input_files(file_path)
        page.wait_for_timeout(1500)
        return f"Uploaded {file_path} to {ref}"
    except Exception as e:
        return f"Error uploading to {ref}: {e}"


@_on_pw_thread
def browser_scroll(direction: str = "down", amount: int = 600) -> str:
    """
    Scroll the current page. direction: 'down' | 'up' | 'top' | 'bottom'.
    amount: pixels (ignored for 'top'/'bottom').
    """
    page, err = _get_page()
    if err:
        return err
    try:
        if direction == "top":
            page.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        elif direction == "up":
            page.evaluate(f"window.scrollBy(0, -{int(amount)})")
        else:
            page.evaluate(f"window.scrollBy(0, {int(amount)})")
        page.wait_for_timeout(500)
        return f"Scrolled {direction} by {amount}px"
    except Exception as e:
        return f"Error scrolling: {e}"


@_on_pw_thread
def browser_click_selector(selector: str, position_x: float = -1, position_y: float = -1) -> str:
    """
    Click an element identified by a CSS selector. Optionally click at a
    specific position WITHIN the element (useful for custom elements with
    closed shadow DOM, e.g. `xhs-publish-btn` on xiaohongshu where the
    inner buttons are inaccessible but their pixel position is known).

    Examples:
        browser_click_selector("xhs-publish-btn", 412, 45)   # 发布 inside
        browser_click_selector("button.confirm")             # whole element
    """
    page, err = _get_page()
    if err:
        return err
    try:
        last_err = None
        for f_idx, frame in enumerate(page.frames):
            try:
                loc = frame.locator(selector).first
                if loc.count() == 0:
                    continue
                kwargs = {"timeout": 8000}
                if position_x >= 0 and position_y >= 0:
                    kwargs["position"] = {"x": position_x, "y": position_y}
                try:
                    loc.click(**kwargs)
                except Exception as e:
                    if "intercepts pointer events" in str(e) or "outside of the viewport" in str(e):
                        kwargs["force"] = True
                        loc.click(**kwargs)
                    else:
                        raise
                page.wait_for_timeout(800)
                suffix = f" (frame {f_idx})" if f_idx > 0 else ""
                return f"Clicked {selector}{suffix}"
            except Exception as e:
                last_err = e
                continue
        return f"Error: no element matched {selector!r} ({last_err})"
    except Exception as e:
        return f"Error clicking {selector!r}: {e}"


@_on_pw_thread
def browser_upload_file(file_path: str, accept_hint: str = "") -> str:
    """
    Upload a file to the page's <input type=file> element, even when it is
    hidden (which is the case on xiaohongshu / douyin upload UIs — the styled
    'choose file' button overlays a hidden input).

    If `accept_hint` is given (e.g. ".jpg" or "image"), prefers a file input
    whose `accept` attribute contains the hint; useful when a page has both
    an image-upload and a video-upload input.
    """
    page, err = _get_page()
    if err:
        return err
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    try:
        candidates = []
        for f_idx, frame in enumerate(page.frames):
            try:
                infos = frame.evaluate("""
                    () => Array.from(document.querySelectorAll('input[type=file]'))
                              .map((el, i) => ({i, accept: el.accept || ''}))
                """)
            except Exception:
                continue
            for info in infos:
                candidates.append((f_idx, frame, info["i"], info["accept"]))
        if not candidates:
            return "Error: no <input type=file> found on the page"
        # Prefer one whose accept contains the hint
        chosen = None
        if accept_hint:
            for c in candidates:
                if accept_hint.lower() in c[3].lower():
                    chosen = c
                    break
        if chosen is None:
            chosen = candidates[0]
        f_idx, frame, idx, accept = chosen
        loc = frame.locator("input[type=file]").nth(idx)
        loc.set_input_files(file_path)
        page.wait_for_timeout(1500)
        suffix = f" (frame {f_idx})" if f_idx > 0 else ""
        return f"Uploaded {file_path} to file input #{idx} (accept={accept!r}){suffix}"
    except Exception as e:
        return f"Error uploading {file_path}: {e}"


@_on_pw_thread
def browser_click_text(text: str, exact: bool = False) -> str:
    """
    Click the first visible element whose text matches `text`. Use this when
    snapshot doesn't surface the element you need — Playwright's text selector
    pierces shadow DOM and iframes automatically.

    Examples:
        browser_click_text("上传图文")
        browser_click_text("发布", exact=True)
    """
    page, err = _get_page()
    if err:
        return err
    try:
        last_err = None
        for f_idx, frame in enumerate(page.frames):
            try:
                base = frame.get_by_text(text, exact=exact)
                n = base.count()
                if n == 0:
                    continue
                # Pick the first candidate that is actually in the viewport.
                # SPAs often have hidden template duplicates at (-9999, -9999)
                # which would block on "outside of viewport" if clicked.
                chosen = None
                for i in range(n):
                    cand = base.nth(i)
                    try:
                        box = cand.bounding_box(timeout=1000)
                    except Exception:
                        box = None
                    if box and -100 <= box["x"] <= 5000 and -100 <= box["y"] <= 5000:
                        chosen = cand
                        break
                if chosen is None:
                    chosen = base.first  # fall back; let Playwright try its best
                try:
                    chosen.click(timeout=4000)
                except Exception as click_err:
                    # SPAs often have overlapping siblings (covering anchor /
                    # ripple layers) that "intercept pointer events". Bypass
                    # the actionability check by dispatching the click event
                    # programmatically.
                    if "intercepts pointer events" in str(click_err) or "outside of the viewport" in str(click_err):
                        chosen.click(timeout=4000, force=True)
                    else:
                        raise
                page.wait_for_timeout(800)
                suffix = f" (frame {f_idx})" if f_idx > 0 else ""
                return f"Clicked element with text {text!r}{suffix}"
            except Exception as e:
                last_err = e
                continue
        return f"Error: no clickable element with text {text!r} found in any frame ({last_err})"
    except Exception as e:
        return f"Error clicking text {text!r}: {e}"


@_on_pw_thread
def browser_press_key(key: str) -> str:
    """
    Press a keyboard key on the page (e.g. 'Enter', 'Escape', 'Tab',
    'ArrowDown', 'Control+a'). Useful for confirming dialogs, submitting forms,
    or selecting items in dropdowns.
    """
    page, err = _get_page()
    if err:
        return err
    try:
        page.keyboard.press(key)
        page.wait_for_timeout(400)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key {key}: {e}"


@_on_pw_thread
def browser_screenshot() -> str:
    """
    Capture a screenshot of the current browser page.
    Returns base64-encoded JPEG so the model can see the visual state.
    """
    page, err = _get_page()
    if err:
        return err
    try:
        png_bytes = page.screenshot(full_page=False)
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except ImportError:
            return base64.b64encode(png_bytes).decode("utf-8")
    except Exception as e:
        return f"Error taking browser screenshot: {e}"
