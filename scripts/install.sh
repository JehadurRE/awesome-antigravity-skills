#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_SKILLS_DIR="${1:-$HOME/.gemini/config/skills}"

mkdir -p "$TARGET_SKILLS_DIR"

for skill_dir in "$REPO_ROOT"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  rm -rf "$TARGET_SKILLS_DIR/$skill_name"
  cp -R "$skill_dir" "$TARGET_SKILLS_DIR/$skill_name"
  echo "Installed skill: $skill_name -> $TARGET_SKILLS_DIR/$skill_name"
done

cat <<EOF

Add this entry under "mcpServers" in ~/.gemini/config/mcp_config.json:
{
  "canva-skills-mcp": {
    "command": "python3",
    "args": ["-m", "mcp_server"],
    "cwd": "$REPO_ROOT"
  }
}
EOF
