import json
import time
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Vega Lite Chart (Unlimited Indicators)", layout="wide")

# --- Sidebar controls
with st.sidebar:
    st.subheader("Chart controls")
    symbol = st.text_input("Symbol", "QQQ")  # works well via Stooq for ETFs/stocks
    interval = st.selectbox("Interval", ["D"], index=0)  # daily for v1; intraday possible later
    theme = st.radio("Theme", ["dark","light"], index=0, horizontal=True)
    height = st.slider("Chart height", 500, 1600, 980, 20)
    show_ema9 = st.checkbox("EMA 9", True)
    show_ema21 = st.checkbox("EMA 21", True)
    show_ema50 = st.checkbox("EMA 50", True)
    show_ema200 = st.checkbox("EMA 200", True)
    show_rsi = st.checkbox("RSI 14", True)
    show_macd = st.checkbox("MACD 12/26/9", True)

# --- Fetch daily OHLC from stooq (simple CSV; good for many US symbols)
@st.cache_data(ttl=60*15)
def fetch_ohlc_stooq(sym: str):
    # stooq expects lowercase and some symbols formatted differently; try basic first
    url = f"https://stooq.com/q/d/l/?s={sym.lower()}&i=d"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    lines = r.text.strip().splitlines()
    if len(lines) <= 1:
        raise ValueError("No data")
    hdr = lines[0].split(",")
    idx = {k:i for i,k in enumerate(hdr)}
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
                "volume": float(c[idx.get("Volume", -1)]) if "Volume" in idx and c[idx["Volume"]] not in ("", "0") else None
            })
        except Exception:
            pass
    if not out:
        raise ValueError("Parsed empty")
    return out

def safe_fetch(sym: str):
    try:
        return fetch_ohlc_stooq(sym)
    except Exception as e:
        st.error(f"Data fetch failed for {sym}: {e}")
        return []

data = safe_fetch(symbol)

st.title("Vega Lite Chart — Unlimited Indicators")
st.caption("Rendering with TradingView Lightweight-Charts + custom indicators (no 2-indicator limit).")

if not data:
    st.stop()

# --- Pass data + settings to the JS widget
payload = {
    "bars": data,
    "theme": theme,
    "height": height,
    "indicators": {
        "ema": [i for i,(flag,i) in enumerate([(show_ema9,9),(show_ema21,21),(show_ema50,50),(show_ema200,200)]) if flag],
        "ema_periods": [p for flag,p in [(show_ema9,9),(show_ema21,21),(show_ema50,50),(show_ema200,200)] if flag],
        "rsi": show_rsi,
        "macd": show_macd
    }
}

# --- Embedding JS (Lightweight-Charts) with inline indicator math
components.html(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
  <style>
    html,body,#wrap {{ height: 100%; margin: 0; background: transparent; }}
    #wrap {{ width: 100%; }}
    #chart {{ width: 100%; height: {height}px; }}
    .panel {{ width: 100%; }}
  </style>
</head>
<body>
  <div id="wrap">
    <div id="chart" class="panel"></div>
    <div id="subpanels"></div>
  </div>
  <script>
    const payload = {json.dumps(payload)};

    // ---------- Utils ----------
    function ema(values, period) {{
      const k = 2 / (period + 1);
      let emaArr = Array(values.length).fill(null);
      let prev = null;
      for (let i=0;i<values.length;i++) {{
        const v = values[i];
        if (v == null) {{ emaArr[i] = prev; continue; }}
        prev = (prev === null) ? v : (v - prev) * k + prev;
        emaArr[i] = prev;
      }}
      return emaArr;
    }}

    function rsi14(closes, period=14) {{
      const out = Array(closes.length).fill(null);
      let gain=0, loss=0;
      for (let i=1;i<closes.length;i++) {{
        const ch = closes[i]-closes[i-1];
        gain += ch>0? ch:0;
        loss += ch<0? -ch:0;
        if (i===period) {{
          let avgG = gain/period, avgL = loss/period;
          let rs = (avgL===0) ? 100 : (avgG/avgL);
          out[i] = 100 - 100/(1+rs);
          var prevG=avgG, prevL=avgL;
          for (let j=i+1;j<closes.length;j++) {{
            const c = closes[j]-closes[j-1];
            const g = c>0?c:0, l = c<0?-c:0;
            prevG = (prevG*(period-1)+g)/period;
            prevL = (prevL*(period-1)+l)/period;
            rs = (prevL===0) ? 100 : (prevG/prevL);
            out[j] = 100 - 100/(1+rs);
          }}
          break;
        }}
      }}
      return out;
    }}

    function macd(closes, fast=12, slow=26, signal=9) {{
      const emaFast = ema(closes, fast);
      const emaSlow = ema(closes, slow);
      const macdLine = emaFast.map((v,i)=> (v!=null && emaSlow[i]!=null)? v-emaSlow[i] : null);
      const signalLine = ema(macdLine, signal);
      const hist = macdLine.map((v,i)=> (v!=null && signalLine[i]!=null)? v - signalLine[i] : null);
      return {{ macdLine, signalLine, hist }};
    }}

    // ---------- Data ----------
    const bars = payload.bars;
    const closes = bars.map(b => b.close);
    const theme = payload.theme || 'dark';
    const chartBg = theme === 'dark' ? '#0e1117' : '#ffffff';
    const textColor = theme === 'dark' ? '#d0d0d0' : '#333333';

    // ---------- Main chart ----------
    const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
      width: document.getElementById('chart').clientWidth,
      height: {height},
      layout: {{ background: {{ type: 'Solid', color: chartBg }}, textColor }},
      rightPriceScale: {{ borderVisible: false }},
      timeScale: {{ borderVisible: false }},
      grid: {{
        vertLines: {{ color: theme==='dark' ? '#1e222d' : '#e6e8eb' }},
        horzLines: {{ color: theme==='dark' ? '#1e222d' : '#e6e8eb' }},
      }}
    }});

    const candleSeries = chart.addCandlestickSeries();
    candleSeries.setData(bars.map(b => ({
      time: b.time, open: b.open, high: b.high, low: b.low, close: b.close
    })));

    // EMAs
    const emaPeriods = payload.indicators.ema_periods || [];
    const colors = ['#1e90ff','#00aa55','#ff9900','#cccccc','#ff00aa','#00dddd'];
    emaPeriods.forEach((p,idx) => {{
      const line = chart.addLineSeries({{ lineWidth: 2, color: colors[idx % colors.length] }});
      const arr = ema(closes, p);
      line.setData(bars.map((b,i)=> arr[i]==null? null : {{ time: b.time, value: arr[i] }}).filter(x=>x));
    }});

    // ---------- Subpanels ----------
    const subPanels = document.getElementById('subpanels');

    function addLinePanel(title, seriesData) {{
      const h = 220;
      const el = document.createElement('div');
      el.className = 'panel';
      el.style.height = h + 'px';
      subPanels.appendChild(el);
      const c = LightweightCharts.createChart(el, {{
        width: el.clientWidth, height: h,
        layout: {{ background: {{ type:'Solid', color: chartBg }}, textColor }},
        rightPriceScale: {{ borderVisible: false }},
        timeScale: {{ borderVisible: false }},
        grid: {{
          vertLines: {{ color: theme==='dark' ? '#1e222d' : '#e6e8eb' }},
          horzLines: {{ color: theme==='dark' ? '#1e222d' : '#e6e8eb' }},
        }}
      }});
      const line = c.addLineSeries({{ lineWidth: 2 }});
      line.setData(seriesData);
      return c;
    }}

    function addHistogramPanel(title, seriesData) {{
      const h = 220;
      const el = document.createElement('div');
      el.className = 'panel';
      el.style.height = h + 'px';
      subPanels.appendChild(el);
      const c = LightweightCharts.createChart(el, {{
        width: el.clientWidth, height: h,
        layout: {{ background: {{ type:'Solid', color: chartBg }}, textColor }},
        rightPriceScale: {{ borderVisible: false }},
        timeScale: {{ borderVisible: false }},
        grid: {{
          vertLines: {{ color: theme==='dark' ? '#1e222d' : '#e6e8eb' }},
          horzLines: {{ color: theme==='dark' ? '#1e222d' : '#e6e8eb' }},
        }}
      }});
      const hist = c.addHistogramSeries({{ priceFormat: {{ type:'price', precision: 4, minMove: 0.0001 }} }});
      hist.setData(seriesData);
      return c;
    }}

    // RSI
    if (payload.indicators.rsi) {{
      const r = rsi14(closes, 14);
      const serie = bars.map((b,i)=> r[i]==null? null : {{ time: b.time, value: r[i] }}).filter(x=>x);
      addLinePanel('RSI', serie);
    }}

    // MACD
    if (payload.indicators.macd) {{
      const M = macd(closes, 12, 26, 9);
      const macdL = bars.map((b,i)=> M.macdLine[i]==null? null : {{ time: b.time, value: M.macdLine[i] }}).filter(x=>x);
      const signalL = bars.map((b,i)=> M.signalLine[i]==null? null : {{ time: b.time, value: M.signalLine[i] }}).filter(x=>x);
      const hist = bars.map((b,i)=> M.hist[i]==null? null : {{ time: b.time, value: M.hist[i] }}).filter(x=>x);
      const c = addLinePanel('MACD', macdL);
      const s = c.addLineSeries({{ lineWidth: 2, color: '#aaaaaa' }}); s.setData(signalL);
      // Hist overlay
      const h = c.addHistogramSeries({{ priceFormat: {{ type:'price', precision: 4, minMove: 0.0001 }} }});
      h.setData(hist);
    }}

    // Resize handling
    new ResizeObserver(() => {{
      chart.applyOptions({{ width: document.getElementById('chart').clientWidth }});
      Array.from(document.querySelectorAll('.panel')).forEach(el => {{
        const api = el.__chartApi;
        if (api) api.applyOptions({{ width: el.clientWidth }});
      }});
    }}).observe(document.getElementById('wrap'));
  </script>
</body>
</html>
""", height=height + (220 if show_rsi else 0) + (220 if show_macd else 0) + 20, scrolling=True)
