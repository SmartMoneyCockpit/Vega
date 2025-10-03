import os, time, pathlib
SNAPSHOT_DIR = pathlib.Path(os.getenv('SNAPSHOT_DIR','snapshots'))
KEEP_DAYS = int(os.getenv('SNAPSHOT_KEEP_DAYS','90'))
MAX_MB = int(os.getenv('SNAPSHOT_MAX_DISK_MB','900'))  # 90% of 1GB
CUT = time.time() - KEEP_DAYS*24*60*60
def total_bytes(path): return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
def delete_old(root, older):
    removed=0
    for p in sorted([p for p in root.rglob('*') if p.is_file()], key=lambda x:x.stat().st_mtime):
        if p.stat().st_mtime < older:
            try: p.unlink(); removed+=1
            except Exception: pass
    return removed
def delete_until_cap(root, cap_bytes):
    removed=0; files=sorted([p for p in root.rglob('*') if p.is_file()], key=lambda x:x.stat().st_mtime); size=total_bytes(root)
    for p in files:
        if size<=cap_bytes: break
        try: s=p.stat().st_size; p.unlink(); size-=s; removed+=1
        except Exception: pass
    return removed
def main():
    if not SNAPSHOT_DIR.exists(): return
    delete_old(SNAPSHOT_DIR, CUT)
    cap = MAX_MB*1024*1024
    if total_bytes(SNAPSHOT_DIR) > cap: delete_until_cap(SNAPSHOT_DIR, cap)
if __name__=='__main__': main()
