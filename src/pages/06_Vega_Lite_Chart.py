# --- Robust symbol normalization for Stooq
def normalize_for_stooq(sym: str) -> list[str]:
    """
    Return a list of candidate tickers for Stooq, highest priority first.
    Examples:
      "QQQ" -> ["qqq.us", "qqq"]
      "NASDAQ:QQQ" -> ["qqq.us", "qqq"]
      "SPY" -> ["spy.us", "spy"]
      "AAPL" -> ["aapl.us", "aapl"]
      "^GSPC" -> ["^gspc"]  # Stooq has indices without .us sometimes
    """
    s = (sym or "").strip()
    if ":" in s:
        s = s.split(":")[-1].strip()
    s_low = s.lower()

    # Common index aliases
    index_map = {
        "^gspc": "spx",     # S&P 500 (sometimes 'spx' works, sometimes '^gspc')
        "^ixic": "ndx",     # Nasdaq 100 proxy on Stooq
        "^dji":  "dji",
    }
    if s_low in index_map:
        return [index_map[s_low], s_low]

    # If already has a suffix like ".us" or ".to", try as-is first
    if "." in s_low:
        return [s_low]

    # Plain US equities/ETFs → try with .us, then bare
    return [f"{s_low}.us", s_low]

@st.cache_data(ttl=60*15)
def fetch_ohlc_stooq_any(sym: str):
    """
    Try multiple candidate tickers against Stooq daily CSV until one works.
    """
    errors = []
    for cand in normalize_for_stooq(sym):
        url = f"https://stooq.com/q/d/l/?s={cand}&i=d"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            lines = r.text.strip().splitlines()
            if len(lines) <= 1:
                errors.append(f"{cand}: empty")
                continue
            hdr = lines[0].split(",")
            idx = {k:i for i,k in enumerate(hdr)}
            # Expect Date,Open,High,Low,Close[,Volume]
            out = []
            for ln in lines[1:]:
                c = ln.split(",")
                try:
                    out.append({
                        "time": c[idx["Date"]],
                        "open": float(c[idx["Open"]]),
                        "high": float(c[idx["High"]]),
                        "low":  float(c[idx["Low"]]),
                        "close":float(c[idx["Close"]]),
                        "volume": float(c[idx["Volume"]]) if "Volume" in idx and c[idx["Volume"]] not in ("", "0") else None
                    })
                except Exception:
                    # skip bad row
                    pass
            if out:
                return out, url  # success
            errors.append(f"{cand}: parsed empty")
        except Exception as e:
            errors.append(f"{cand}: {e}")
            continue
    raise ValueError(" ; ".join(errors))

def safe_fetch(sym: str):
    try:
        data, used_url = fetch_ohlc_stooq_any(sym)
        st.caption(f"Data source: {used_url}")
        return data
    except Exception as e:
        st.error(f"Data fetch failed for {sym}: {e}")
        return []
