
import os, pandas as pd, numpy as np
from datetime import datetime, timezone
os.makedirs('snapshots', exist_ok=True)

# Demo placeholders: replace with your internal DB loaders
positions = pd.DataFrame({'Ticker':['HPR.TO'],'Qty':[1000],'Avg Cost':[25.0],'Last':[25.4]})
signals   = pd.DataFrame({'Ticker':['SPXU'],'Setup':['Buy Today'],'Reason':['Hedge basket']})
breadth   = pd.DataFrame({'Metric':['VIX'],'Value':[18.7],'Status':['Neutral']})
rs        = pd.DataFrame({'Bucket':['USA'],'RS Trend':['🟡']})

ts = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d_%H%M%S')
positions.to_csv(f'snapshots/positions_{ts}.csv', index=False)
signals.to_csv(f'snapshots/signals_{ts}.csv', index=False)
breadth.to_csv(f'snapshots/breadth_{ts}.csv', index=False)
rs.to_csv(f'snapshots/rs_{ts}.csv', index=False)

print("Daily digest CSV snapshots written:", ts)
