#!/usr/bin/env python3
"""macOS Vision OCR MCP server（月儿自封版，2026-09-04）。

包装 ~/.claude/bin/ocr_vision.swift（Swift + Vision 框架，本地离线免费）。
来源：hermes 的 apple-vision-ocr 技能，经月儿试炼后收编进 CC。
"""
import os
import subprocess

from mcp.server.fastmcp import FastMCP

SWIFT = os.path.expanduser("~/.claude/bin/ocr_vision.swift")

mcp = FastMCP("mac-vision-ocr")


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


if __name__ == "__main__":
    mcp.run(transport="stdio")
