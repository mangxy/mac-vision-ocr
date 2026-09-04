#!/usr/bin/env python3
"""macOS local OCR + vision MCP server.

Two tools:
- ocr: extract text from images via the macOS Vision framework (offline, free, ~1s).
- see: ask a local multimodal LLM (oMLX) about an image.

The Swift OCR script lives at ~/.claude/bin/ocr_vision.swift (installed by install.sh).
"""
import base64
import json
import os
import re
import subprocess
import urllib.request

from mcp.server.fastmcp import FastMCP

SWIFT = os.path.expanduser("~/.claude/bin/ocr_vision.swift")

mcp = FastMCP("mac-vision-ocr")


def _omlx_conf():
    """Read local VLM endpoint config: env vars first, then ~/.openviking/ov.conf vlm block."""
    conf = {
        "base": os.environ.get("OMLX_BASE_URL", ""),
        "key": os.environ.get("OMLX_API_KEY", ""),
        "model": os.environ.get("OMLX_MODEL", ""),
    }
    if not conf["base"]:
        try:
            ov = json.load(open(os.path.expanduser("~/.openviking/ov.conf")))
            v = ov.get("vlm", {})
            conf["base"] = v.get("api_base", "http://localhost:8000/v1")
            conf["key"] = conf["key"] or v.get("api_key", "")
            conf["model"] = conf["model"] or v.get("model", "")
        except (OSError, ValueError):
            pass
    return conf


MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp"}


@mcp.tool()
def ocr(path: str, langs: str = "zh-Hans,en-US", coords: bool = False) -> str:
    """Extract text from an image (macOS Vision framework; local, offline, ~1s, near-perfect on Chinese+English).

    Args:
        path: absolute path to the image (png/jpg screenshot etc.).
        langs: comma-separated language codes, default zh-Hans,en-US.
        coords: prefix each line with normalized `y= x= |` layout coords, default False.

    Returns:
        Plain text lines in layout order (top-to-bottom, left-to-right).
        An empty-text notice means the image has no text (photo/icon) — use a
        vision-model tool instead.
    """
    p = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(p):
        return f"Error: file not found: {p}"
    lang_args = [l.strip() for l in langs.split(",") if l.strip()]
    r = subprocess.run(
        ["swift", SWIFT, p] + lang_args,
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        return f"Error: {r.stderr.strip()[:500]}"
    out = r.stdout.strip()
    if not out:
        return "(No text found — likely a photo/icon; use a vision-model tool instead)"
    if not coords:
        out = "\n".join(
            re.sub(r"^y=[\d.]+ x=[\d.]+ \| ", "", line) for line in out.splitlines()
        )
    return out


@mcp.tool()
def see(path: str, question: str = "Describe this image in detail.", timeout: int = 300) -> str:
    """Understand an image with a local multimodal LLM via oMLX (offline, free). Slow while the server is busy with batch jobs.

    Args:
        path: absolute path to the image (png/jpg/webp/gif/bmp).
        question: what to ask about the image, default "Describe this image in detail.".
        timeout: seconds to wait, default 300. If batch jobs are queueing, consider
            falling back to a cloud vision tool instead of waiting.

    Returns:
        The model's answer, or a timeout/unreachable notice suggesting a cloud
        vision tool or retry when the server is idle.
    """
    p = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(p):
        return f"Error: file not found: {p}"
    mime = MIME.get(os.path.splitext(p)[1].lower())
    if not mime:
        return f"Error: unsupported image format: {p}"
    conf = _omlx_conf()
    if not conf["model"]:
        return "Error: no local VLM config found (set OMLX_MODEL or the vlm block in ~/.openviking/ov.conf)"

    img = base64.b64encode(open(p, "rb").read()).decode()
    body = json.dumps({
        "model": conf["model"],
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img}"}},
            {"type": "text", "text": (
        "Format: answer in Simplified Chinese Markdown (tables/lists where fitting). "
        "ONLY state what is actually visible; if unsure, say so. "
        "Never invent names, relations, numbers, or facts not shown in the image. "
        "If the image contradicts the question, correct the question.\n\n" + question)},
        ]}],
        "max_tokens": 1024,
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        conf["base"].rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {conf['key']}", "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=timeout))
        return r["choices"][0]["message"]["content"].strip()
    except KeyError:
        return f"Error: unexpected response shape: {json.dumps(r, ensure_ascii=False)[:300]}"
    except Exception as e:
        return (f"Local VLM busy or unreachable ({type(e).__name__}: {e}). "
                "Long queue likely — use a cloud vision tool or retry when idle.")


if __name__ == "__main__":
    mcp.run(transport="stdio")
