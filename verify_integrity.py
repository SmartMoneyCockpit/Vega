import os, sys, json, hashlib

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv) < 3:
        print("Usage: python verify_integrity.py <manifest.json> <repo_root>")
        sys.exit(2)

    manifest_path = sys.argv[1]
    repo_root = sys.argv[2]

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    expected = { entry["path"]: (entry["size"], entry["sha256"]) for entry in manifest["files"] }

    missing = []
    mismatched = []
    extra = []

    # Check expected files
    for rel, (exp_size, exp_sha) in expected.items():
        local_path = os.path.join(repo_root, rel)
        if not os.path.exists(local_path):
            missing.append(rel)
            continue
        if os.path.isdir(local_path):
            missing.append(rel + " (expected file, found directory)")
            continue
        size = os.path.getsize(local_path)
        sha = sha256_of_file(local_path)
        if size != exp_size or sha != exp_sha:
            mismatched.append((rel, {"expected_size": exp_size, "actual_size": size, "expected_sha256": exp_sha, "actual_sha256": sha}))

    # Detect extras (anything in repo that is not in manifest)
    repo_files = []
    for root, _, files in os.walk(repo_root):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), repo_root)
            # Normalize path sep
            rel = rel.replace("\\", "/")
            repo_files.append(rel)
    for rel in repo_files:
        if rel not in expected:
            extra.append(rel)

    ok = not missing and not mismatched
    print("=== Integrity Report ===")
    print(f"Files expected: {len(expected)}")
    print(f"Missing: {len(missing)} | Mismatched: {len(mismatched)} | Extra (not in manifest): {len(extra)}")
    if missing:
        print("\n-- Missing files --")
        for m in missing:
            print(m)
    if mismatched:
        print("\n-- Mismatched files --")
        for rel, det in mismatched:
            print(rel, det)
    if extra:
        print("\n-- Extra files (OK, just not in manifest) --")
        for e in extra[:50]:
            print(e)
        if len(extra) > 50:
            print(f"... and {len(extra)-50} more")

    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
