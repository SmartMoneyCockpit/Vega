# scripts/quick_test_ibkr.py
from pathlib import Path
from ruamel.yaml import YAML
from src.ibkr_bridge import connect_ib, get_delayed_last

yaml = YAML()
cfg = yaml.load(Path("config.yaml").read_text())

ib = connect_ib(cfg)
print("Connected:", ib.isConnected())
for tk in ["AAPL","SPY","RY.TO","ZPR.TO","HPR.TO","CPD.TO"]:
    try:
        print(tk, get_delayed_last(ib, tk))
    except Exception as e:
        print(tk, "ERR:", e)
ib.disconnect()
