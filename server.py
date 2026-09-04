#!/usr/bin/env python3
"""macOS Vision OCR MCP server（月儿自封版，2026-09-04）。

包装 ~/.claude/bin/ocr_vision.swift（Swift + Vision 框架，本地离线免费）。
来源：hermes 的 apple-vision-ocr 技能，经月儿试炼后收编进 CC。
"""
import base64
import json
import os
import subprocess
import urllib.request

from mcp.server.fastmcp import FastMCP

SWIFT = os.path.expanduser("~/.claude/bin/ocr_vision.swift")

mcp = FastMCP("mac-vision-ocr")


def _omlx_conf():
    """读本地 VLM 接口配置：env 优先，其次 ~/.openviking/ov.conf 的 vlm 块。"""
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
def ocr(path: str, langs: str = "zh-Hans,en-US") -> str:
    """OCR 提取图片文字（macOS Vision 框架，本地离线，约 1 秒，中英文满准）。

    Args:
        path: 图片文件绝对路径（png/jpg 截图等）。
        langs: 逗号分隔的语言码，默认 zh-Hans,en-US。中英混排保持默认即可。

    Returns:
        按版面顺序（上到下、左到右）的文字，每行前缀 y= x= 归一化坐标（可忽略）。
        返回「图里没抠出文字」说明是纯图/照片，应改用视觉理解类工具。
    """
    p = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(p):
        return f"错误：文件不存在 {p}"
    lang_args = [l.strip() for l in langs.split(",") if l.strip()]
    r = subprocess.run(
        ["swift", SWIFT, p] + lang_args,
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        return f"错误：{r.stderr.strip()[:500]}"
    return r.stdout.strip() or "（图里没抠出文字——纯图/照片请改用视觉理解工具）"


@mcp.tool()
def see(path: str, question: str = "详细描述这张图的内容", timeout: int = 300) -> str:
    """看懂图片（本地 oMLX VLM，离线免费；炉子被批处理占满时会排队较久）。

    Args:
        path: 图片文件绝对路径（png/jpg/webp 等）。
        question: 想问这张图什么，默认"详细描述这张图的内容"。
        timeout: 等待秒数，默认 300。烧库/提取期间队列长，超时建议改走云端视觉工具。

    Returns:
        模型对图片的回答。炉忙超时会明说，届时换视觉理解云端工具即可。
    """
    p = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(p):
        return f"错误：文件不存在 {p}"
    mime = MIME.get(os.path.splitext(p)[1].lower())
    if not mime:
        return f"错误：不认识的图片格式 {p}"
    conf = _omlx_conf()
    if not conf["model"]:
        return "错误：没找到本地 VLM 配置（OMLX_MODEL 或 ~/.openviking/ov.conf 的 vlm 块）"

    img = base64.b64encode(open(p, "rb").read()).decode()
    body = json.dumps({
        "model": conf["model"],
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img}"}},
            {"type": "text", "text": question},
        ]}],
        "max_tokens": 1024,
    }).encode()
    req = urllib.request.Request(
        conf["base"].rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {conf['key']}", "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=timeout))
        return r["choices"][0]["message"]["content"].strip()
    except KeyError:
        return f"错误：响应格式意外 {json.dumps(r, ensure_ascii=False)[:300]}"
    except Exception as e:
        return f"炉子忙/不可达（{type(e).__name__}: {e}）——队列长时会这样，建议改走云端视觉工具，或等炉空再试"


if __name__ == "__main__":
    mcp.run(transport="stdio")
