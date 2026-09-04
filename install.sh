#!/usr/bin/env bash
# mac-vision-ocr 安装：拷贝脚本 + 注册 MCP（幂等，可重复执行）
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.claude/bin"
mkdir -p "$BIN"
cp "$SRC/ocr_vision.swift" "$BIN/ocr_vision.swift"
cp "$SRC/server.py" "$BIN/ocr_mcp_server.py"
echo "✅ 脚本已拷贝到 $BIN"

if ! command -v uv >/dev/null 2>&1; then
  echo "❌ 未找到 uv，请先安装：https://docs.astral.sh/uv/" >&2
  exit 1
fi
UV="$(command -v uv)"

python3 - "$UV" <<'PY'
import json, os, sys

uv = sys.argv[1]
entry = {
    "command": uv,
    "args": ["run", "--with", "mcp<2", "python", os.path.expanduser("~/.claude/bin/ocr_mcp_server.py")],
    "env": {},
}
path = os.path.expanduser("~/.claude.json")
try:
    d = json.load(open(path))
except FileNotFoundError:
    d = {}
d.setdefault("mcpServers", {})["mac-vision-ocr"] = entry
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
print("✅ 已注册/更新 ~/.claude.json → mcpServers.mac-vision-ocr")
PY

echo "安装完成。重启 Claude Code 新会话后生效。"
