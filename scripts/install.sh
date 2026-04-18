#!/usr/bin/env bash
# price-desk — install/sync script
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_DIR="$HOME/.claude/skills/price-desk"
STALE_ZIP="$HOME/.claude/skills/price-desk.skill"

echo "📦 price-desk install/sync"
echo "   source: $REPO_DIR"
echo "   target: $INSTALL_DIR"

# Verify yfinance installed
if ! python3 -c "import yfinance" 2>/dev/null; then
  echo "📦 Installing yfinance..."
  pip3 install yfinance || {
    echo "❌ yfinance install failed. Try: pip3 install --user yfinance"
    exit 1
  }
fi

[ -f "$STALE_ZIP" ] && { echo "🗑️  removing stale $STALE_ZIP"; rm "$STALE_ZIP"; }

if [ "${1:-}" = "--clean" ]; then
  echo "🧹 clean install"
  rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cp "$REPO_DIR/SKILL.md" "$INSTALL_DIR/"
cp -R "$REPO_DIR/scripts" "$INSTALL_DIR/"
[ -d "$REPO_DIR/data" ] && cp -R "$REPO_DIR/data" "$INSTALL_DIR/"

VERSION=$(grep -m1 "^version:" "$INSTALL_DIR/SKILL.md" | awk '{print $2}')
echo "✅ installed price-desk v$VERSION — restart Claude Code to reload"
