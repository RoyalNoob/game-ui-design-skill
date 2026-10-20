#!/usr/bin/env bash
# Build the claude.ai upload ZIP from the skill folder.
# Usage: bash tools/build_zip.sh            -> dist/game-gui-design-v<version>.zip
set -euo pipefail
cd "$(dirname "$0")/.."
version=$(python3 -c "import json;print(json.load(open('plugins/game-gui/.claude-plugin/plugin.json'))['version'])")
mkdir -p dist
out="dist/game-gui-design-v${version}.zip"
rm -f "$out"
(cd plugins/game-gui/skills && zip -rq "../../../$out" game-gui-design -x '*__pycache__*' '*.DS_Store')
echo "$out"
