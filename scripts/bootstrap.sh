#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/bootstrap.sh build   # unzip first, then pip install
#   bash scripts/bootstrap.sh start   # run streamlit after unpack

ZIP_PATTERN="Vega-ready-for-Render-*.zip"

unpack_if_needed() {
  if ls $ZIP_PATTERN 1>/dev/null 2>&1; then
    echo "Found ZIP(s) — unpacking..."
    tmpdir="$(mktemp -d)"
    # Pick newest zip if multiple
    zipfile="$(ls -1t $ZIP_PATTERN | head -n1)"
    echo "Using $zipfile"
    unzip -q "$zipfile" -d "$tmpdir"

    shopt -s dotglob
    # If the zip has a single top-level folder, move its contents only
    top_dirs=$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d | wc -l || true)
    top_files=$(find "$tmpdir" -maxdepth 1 -type f | wc -l || true)
    if [ "${top_dirs:-0}" -eq 1 ] && [ "${top_files:-0}" -eq 0 ]; then
      inner="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d)"
      mv "$inner"/* .
    else
      mv "$tmpdir"/* .
    fi
    rm -rf "$tmpdir"
    rm -f "$zipfile"
    echo "Unpack complete."
  else
    echo "No ZIP found, skipping unpack."
  fi
}

cmd="${1:-build}"

if [ "$cmd" = "build" ]; then
  unpack_if_needed
  if [ -f requirements.txt ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
  else
    echo "requirements.txt not found after unpack. Proceeding without deps."
  fi
elif [ "$cmd" = "start" ]; then
  # Start Streamlit
  PORT="${PORT:-8501}"
  exec streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0
else
  echo "Unknown command: $cmd"
  exit 1
fi
