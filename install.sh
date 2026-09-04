#!/usr/bin/env bash
# mac-vision-ocr installer: copy scripts + register MCP (idempotent, safe to re-run)
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.claude/bin"
mkdir -p "$BIN"
cp "$SRC/ocr_vision.swift" "$BIN/ocr_vision.swift"
cp "$SRC/server.py" "$BIN/ocr_mcp_server.py"
echo "OK: scripts copied to $BIN"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv not found. Install it first: https://docs.astral.sh/uv/" >&2
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
print("OK: registered/updated mcpServers.mac-vision-ocr in ~/.claude.json")
PY

echo "Done. Restart Claude Code (new session) to take effect."
