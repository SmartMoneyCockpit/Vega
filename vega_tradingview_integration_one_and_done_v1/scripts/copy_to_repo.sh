#!/usr/bin/env bash
# Copy the One-and-Done files into an existing Vega repo root.
set -euo pipefail
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${1:-.}"
echo "Copying to: $DEST_DIR"
mkdir -p "$DEST_DIR/services" "$DEST_DIR/components" "$DEST_DIR/utils" "$DEST_DIR/pages" "$DEST_DIR/templates" "$DEST_DIR/exports"
cp -f "$SRC_DIR/services/"*.py "$DEST_DIR/services/"
cp -f "$SRC_DIR/components/"*.py "$DEST_DIR/components/"
cp -f "$SRC_DIR/utils/"*.py "$DEST_DIR/utils/"
cp -f "$SRC_DIR/pages/"*.py "$DEST_DIR/pages/"
cp -f "$SRC_DIR/templates/"*.json "$DEST_DIR/templates/"
cp -f "$SRC_DIR/exports/.gitkeep" "$DEST_DIR/exports/.gitkeep" || true
echo "Done. Launch Streamlit and open 'TradingView Export & Launch' page."
