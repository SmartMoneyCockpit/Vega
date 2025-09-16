# warm_cache.py
from app import fetch
def warm():
    for s in ["SPY","QQQ","^N225","^HSI"]:
        try: fetch(s, "1y", "1d")
        except: pass
if __name__ == "__main__":
    warm()
