#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <OWNER> <REPO>" >&2
  exit 1
fi
OWNER="$1"; REPO="$2"
cat tools/README_BADGES.md | sed "s/\${OWNER}/${OWNER}/g; s/\${REPO}/${REPO}/g" > .README.badges.tmp.md
if grep -q "^## Status" README.md 2>/dev/null; then
  awk -v RS='' -v ORS='\n\n' '
    BEGIN { while ((getline l < ".README.badges.tmp.md") > 0) t=t l "\n"; }
    {
      n=split($0, a, /\n(?=## )/);
      for(i=1;i<=n;i++){ if(a[i] ~ /^## Status/) print t; else print a[i]; }
    }' README.md > README.md.new && mv README.md.new README.md
else
  echo -e "\n" >> README.md
  cat .README.badges.tmp.md >> README.md
fi
rm -f .README.badges.tmp.md
echo "README badges applied for $OWNER/$REPO"
