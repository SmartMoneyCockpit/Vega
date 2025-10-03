import os, importlib, pandas as pd, json
from datetime import datetime, timezone
import io, zipfile

os.makedirs('snapshots', exist_ok=True)

def _try(name):
    try: return importlib.import_module(name)
    except Exception: return None

adapter = _try('db_adapter')
if adapter:
    positions = adapter.load_positions()
    signals   = adapter.load_signals()
    breadth   = adapter.load_breadth()
    rs        = adapter.load_rs()
else:
    positions = pd.DataFrame({'Ticker':['HPR.TO'],'Qty':[1000],'Avg Cost':[25.0],'Last':[25.4]})
    signals   = pd.DataFrame({'Ticker':['SPXU'],'Setup':['Buy Today'],'Reason':['Hedge basket']})
    breadth   = pd.DataFrame({'Metric':['VIX'],'Value':[18.7],'Status':['Neutral']})
    rs        = pd.DataFrame({'Bucket':['USA'],'RS Trend':['🟡']})

def summarize_signals(df):
    return [{'ticker':str(r.get('Ticker','')), 'setup':str(r.get('Setup','')), 'reason':str(r.get('Reason',''))} for _,r in df.iterrows()]

def summarize_breadth(df):
    m = {str(r['Metric']).lower(): str(r['Status']) for _, r in df.iterrows() if 'Metric' in r and 'Status' in r}
    return {'vix': m.get('vix'), 'moving_avgs': {'gt50dma': m.get('%>50dma (spx)'), 'gt200dma': m.get('%>200dma (spx)')}, 'ad_line': m.get('adv/dec (nyse)')}

def summarize_rs(df):
    buckets = {}
    for _, r in df.iterrows():
        buckets[str(r.get('Bucket',''))] = str(r.get('RS Trend',''))
    return buckets

ts = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d_%H%M%S')

# write CSVs
positions.to_csv(f'snapshots/positions_{ts}.csv', index=False)
signals.to_csv(f'snapshots/signals_{ts}.csv', index=False)
breadth.to_csv(f'snapshots/breadth_{ts}.csv', index=False)
rs.to_csv(f'snapshots/rs_{ts}.csv', index=False)

# build digest ZIP
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('positions.csv', positions.to_csv(index=False))
    z.writestr('signals.csv', signals.to_csv(index=False))
    z.writestr('breadth.csv', breadth.to_csv(index=False))
    z.writestr('relative_strength.csv', rs.to_csv(index=False))
buf.seek(0)
open(f'snapshots/digest_{ts}.zip', 'wb').write(buf.getvalue())

# meta.json
meta = {'timestamp': ts, 'positions_rows': int(len(positions)), 'signals': summarize_signals(signals), 'breadth_summary': summarize_breadth(breadth), 'rs_trends': summarize_rs(rs)}
open(f'snapshots/meta_{ts}.json','w').write(json.dumps(meta, indent=2))

# append RS history
try:
    import db_adapter as _db
    _db.rs_history_append_from_current(rs)
except Exception as _e:
    print('RS history append skipped:', _e)

print('Daily digest snapshots written:', ts)
