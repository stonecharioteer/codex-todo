#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Script to record an asciinema demo of the TODO app and convert it to SVG/GIF.
# Dependencies (Ubuntu/Mint):
#   sudo apt update && sudo apt install -y asciinema svg-term-cli imagemagick
# -----------------------------------------------------------------------------

# Paths
CAST=demo.cast
GIF=assets/todo-demo.gif

mkdir -p assets

echo "Recording asciinema cast to '$CAST'..."
asciinema rec -c "DB_PATH=/tmp/tasks.db ./.venv/bin/codex-todo" --title "Codex TODO Demo" "$CAST"

echo "Converting cast to GIF '$GIF'..."
agg --speed 2 "$CAST" "$GIF"

echo
echo "Demo assets generated:"
echo "  GIF: $GIF"
