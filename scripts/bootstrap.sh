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
    # rsync present on most images
    rsync -a "$SRC"/ ./ 
  elif cp --version >/dev/null 2>&1; then
    # cp -a is enough if rsync not present
    cp -a "$SRC"/. .
  else
    # Fallback to Python shutil (always available)
    python - <<'PY'
import os, shutil, sys
src = sys.argv[1]
for root, dirs, files in os.walk(src):
    rel = os.path.relpath(root, src)
    dst = os.path.join(".", rel) if rel != "." else "."
    os.makedirs(dst, exist_ok=True)
    for f in files:
        s = os.path.join(root, f)
        d = os.path.join(dst, f)
        shutil.copy2(s, d)
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
    # Use Python unzip (portable) so we don't rely on system unzip
    python - <<'PY'
import glob, os, sys, tempfile, zipfile
zp = sorted(glob.glob("Vega-ready-for-Render-*.zip"), key=os.path.getmtime)[-1]
td = sys.argv[1]
with zipfile.ZipFile(zp) as z:
    z.extractall(td)
PY
    python - "$tmpdir"

    shopt -s dotglob
    # If the zip has a single top-level folder, merge *its contents*; else merge all
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
