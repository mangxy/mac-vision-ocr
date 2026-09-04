#!/usr/bin/env bash
# mac-vision-ocr uninstaller: remove scripts + unregister MCP (idempotent)
set -euo pipefail

rm -f "$HOME/.claude/bin/ocr_vision.swift" "$HOME/.claude/bin/ocr_mcp_server.py"
echo "OK: removed ~/.claude/bin/{ocr_vision.swift,ocr_mcp_server.py}"

python3 - <<'PY'
import json, os

path = os.path.expanduser("~/.claude.json")
try:
    d = json.load(open(path))
except FileNotFoundError:
    d = {}
if d.get("mcpServers", {}).pop("mac-vision-ocr", None) is not None:
    json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
    print("OK: removed mcpServers.mac-vision-ocr")
else:
    print("Not registered, nothing to do.")
PY

echo "Uninstall done."
