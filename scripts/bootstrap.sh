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
  elif command -v cp >/dev/null 2>&1; then
    cp -a "$SRC"/. .
  else
    # Python fallback (no here-docs)
    python -c "import os,shutil,sys
src=sys.argv[1]
for root,dirs,files in os.walk(src):
    rel=os.path.relpath(root, src)
    dst='.' if rel=='.' else os.path.join('.', rel)
    os.makedirs(dst, exist_ok=True)
    for f in files:
        shutil.copy2(os.path.join(root,f), os.path.join(dst,f))" "$SRC"
  fi
}

sanitize() {
  # Trim trailing CR/LF from a path
  local p="$1"
  p="${p%$'\n'}"
  p="${p%$'\r'}"
  printf '%s' "$p"
}

unpack_if_needed() {
  shopt -s nullglob dotglob
  local matches=( $ZIP_PATTERN )
  if ((${#matches[@]})); then
    echo "Found ZIP(s) — unpacking..."
    local zipfile
    # pick newest; then sanitize CR/LF
    zipfile="$(ls -1t $ZIP_PATTERN | head -n1 || true)"
    zipfile="$(sanitize "$zipfile")"
    if [ ! -f "$zipfile" ]; then
      echo "Selected ZIP not found after listing: '$zipfile'"
      ls -la
      exit 1
    fi
    echo "Using: $zipfile"

    local tmpdir
    tmpdir="$(mktemp -d)"

    # Portable unzip
    python -m zipfile -e "$zipfile" "$tmpdir"

    # If a single top-level folder, merge its contents; else merge all
    local top_dirs top_files
    top_dirs=$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d | wc -l || true)
    top_files=$(find "$tmpdir" -maxdepth 1 -type f | wc -l || true)
    if [ "${top_dirs:-0}" -eq 1 ] && [ "${top_files:-0}" -eq 0 ]; then
      local inner
      inner="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d)"
      copy_merge "$inner"
    else
      copy_merge "$tmpdir"
    fi

    rm -rf "$tmpdir" "$zipfile"
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
  PORT="${PORT:-8501}"
  exec streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0
else
  echo "Unknown command: $cmd"
  exit 1
fi
