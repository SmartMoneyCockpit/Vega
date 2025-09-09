import os, json, hashlib, time
root = "."
out_dir = os.path.join("vault","inventory")
os.makedirs(out_dir, exist_ok=True)

def sha256(p):
    h = hashlib.sha256()
    with open(p,"rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

entries = []
for base, dirs, files in os.walk(root):
    if base.startswith("./.git"):
        continue
    for fn in files:
        p = os.path.join(base, fn)
        if p.startswith("./vault/") and ("/snapshots/" in p or "/exports/" in p):
            size = os.path.getsize(p)
            entries.append({"path": p, "size": size, "sha256": None})
            continue
        try:
            size = os.path.getsize(p)
            digest = sha256(p)
            entries.append({"path": p, "size": size, "sha256": digest})
        except Exception:
            pass

report = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "count": len(entries),
    "files": entries
}
with open(os.path.join(out_dir,"inventory.json"),"w",encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print("Inventory written:", os.path.join(out_dir,"inventory.json"))
