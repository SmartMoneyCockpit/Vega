#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/bootstrap.sh build   # unzip first, then pip install
#   bash scripts/bootstrap.sh start   # run streamlit after unpack

ZIP_PATTERN="Vega-ready-for-Render-*.zip"

copy_merge() {
  # Copy/merge SRC into repo root, overwriting existing files safely
  local SRC="$1"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a "$SRC"/ ./ 
  elif cp --version >/dev/null 2>&1; then
    cp -a "$SRC"/. .
  else
    python - <<'PY'
import os, shutil, sys
src = sys.argv[1]
for root, dirs, files in os.walk(src):
    rel = os.path.relpath(root, src)
    dst = os.path.join(".", rel) if rel != "." else "."
    os.makedirs(dst, exist_ok=True)
    for f in files:
        shutil.copy2(os.path.join(root, f), os.path.join(dst, f))
PY
    python - "$SRC"
  fi
}

unpack_if_needed() {
  if ls $ZIP_PATTERN 1>/dev/null 2>&1; then
    echo "Found ZIP — unpacking…"
    tmpdir="$(mktemp -d)"
    # Pick newest ZIP if multiple
    zipfile="$(ls -1t $ZIP_PATTERN | head -n1)"
    echo "Using $zipfile"

    # Portable unzip (no system 'unzip' or argv needed)
    python -m zipfile -e "$zipfile" "$tmpdir"

    shopt -s dotglob
    # If the zip has a single top-level folder, merge its contents; else merge all
    top_dirs=$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d | wc -l || true)
    top_files=$(find "$tmpdir" -maxdepth 1 -type f | wc -l || true)
    if [ "${top_dirs:-0}" -eq 1 ] && [ "${top_files:-0}" -eq 0 ]; then
      inner="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d)"
      copy_merge "$inner"
    else
      copy_merge "$tmpdir"
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
    echo "Installing dependencies…"
    pip install -r requirements.txt
  else
    echo "requirements.txt not found af
