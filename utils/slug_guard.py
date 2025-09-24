# vega/utils/slug_guard.py
import os, re

def infer_slug_from_filename(path: str) -> str:
    base = os.path.splitext(os.path.basename(path))[0]
    base = re.sub(r'^\d+[_-]*', '', base)          # drop number prefixes like 095_
    base = re.sub(r'[^0-9A-Za-z]+', '-', base)     # non-alnum -> hyphen
    base = re.sub(r'-+', '-', base).strip('-')     # collapse hyphens
    return base.lower()

def scan_pages_for_slug_collisions(pages_dir: str = "pages"):
    if not os.path.isdir(pages_dir):
        return {}
    files = [f for f in os.listdir(pages_dir) if f.endswith(".py") and f != "__init__.py"]
    slug_map = {}
    for f in files:
        slug = infer_slug_from_filename(f)
        slug_map.setdefault(slug, []).append(os.path.join(pages_dir, f))
    return {s: fs for s, fs in slug_map.items() if len(fs) > 1}

def assert_unique_page_links(link_paths):
    seen = set()
    dups = sorted({p for p in link_paths if (p in seen or seen.add(p))})
    if dups:
        raise SystemExit(f"[BOOT BLOCKED] Duplicate st.page_link targets found: {dups}")

def list_pages_and_slugs(pages_dir: str = "pages"):
    if not os.path.isdir(pages_dir):
        return []
    files = sorted([f for f in os.listdir(pages_dir) if f.endswith(".py") and f != "__init__.py"])
    return [{"file": os.path.join(pages_dir, f), "slug": infer_slug_from_filename(f)} for f in files]
