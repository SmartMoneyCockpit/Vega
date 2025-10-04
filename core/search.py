
from typing import List, Tuple, Dict
import unicodedata

def _normalize(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()

def build_search_index(groups: List[Dict]) -> List[Tuple[str,str,str]]:
    # returns list of (group,label,route) for searching
    out = []
    for g in groups:
        for it in g.get("items", []):
            out.append((g["group"], it["label"], it["route"]))
    return out

def search_routes(groups: List[Dict], query: str, limit: int = 20) -> List[Tuple[str,str,str]]:
    q = _normalize(query)
    idx = build_search_index(groups)
    if not q:
        return idx[:limit]
    scored = []
    for g,l,r in idx:
        s = f"{g} {l} {r}"
        sn = _normalize(s)
        if all(part in sn for part in q.split()):
            # simple score: shorter match is better
            scored.append((len(sn), g,l,r))
    scored.sort(key=lambda t: t[0])
    return [(g,l,r) for _,g,l,r in scored[:limit]]
