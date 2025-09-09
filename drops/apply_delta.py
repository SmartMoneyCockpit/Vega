#!/usr/bin/env python3
import argparse, os, subprocess, sys, zipfile, shutil, pathlib
def run(cmd, cwd=None):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)
def main():
    p = argparse.ArgumentParser(description="Apply Vega delta ZIP and deletion list, then commit & push.")
    p.add_argument("--repo", required=True, help="Path to your Vega repo (already cloned)")
    p.add_argument("--delta", required=True, help="Path to delta ZIP (changed/new files only)")
    p.add_argument("--delete-list", default=None, help="Optional path to deletion list (txt)")
    p.add_argument("--branch", default="main", help="Branch to commit to (default: main)")
    args = p.parse_args()
    repo = pathlib.Path(args.repo).resolve()
    assert (repo / ".git").exists(), f"{repo} is not a git repo"
    delta = pathlib.Path(args.delta).resolve()
    with zipfile.ZipFile(delta, "r") as z:
        z.extractall(repo)
    removed = []
    if args.delete_list:
        dl = pathlib.Path(args.delete_list).read_text(encoding="utf-8").splitlines()
        for line in dl:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            target = repo / line
            if target.is_file():
                target.unlink(missing_ok=True); removed.append(line)
            elif target.is_dir():
                shutil.rmtree(target, ignore_errors=True); removed.append(line + "/")
    run(["git", "checkout", args.branch], cwd=repo)
    run(["git", "add", "-A"], cwd=repo)
    msg = f"Vega auto-apply delta: {delta.name}"
    if removed: msg += f" | removed: {len(removed)} files/dirs"
    run(["git", "commit", "-m", msg], cwd=repo)
    run(["git", "push"], cwd=repo)
    print("Done.")
if __name__ == "__main__":
    main()
