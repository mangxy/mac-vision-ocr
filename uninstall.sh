#!/usr/bin/env bash
# mac-vision-ocr 卸载：删脚本 + 摘除 MCP 注册（幂等）
set -euo pipefail

rm -f "$HOME/.claude/bin/ocr_vision.swift" "$HOME/.claude/bin/ocr_mcp_server.py"
echo "✅ 已删除 ~/.claude/bin/{ocr_vision.swift,ocr_mcp_server.py}"

python3 - <<'PY'
import json, os

path = os.path.expanduser("~/.claude.json")
try:
    d = json.load(open(path))
except FileNotFoundError:
    d = {}
if d.get("mcpServers", {}).pop("mac-vision-ocr", None) is not None:
    json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
    print("✅ 已摘除 mcpServers.mac-vision-ocr")
else:
    print("ℹ️ 本就没有注册，跳过")
PY

echo "卸载完成。"
