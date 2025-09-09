import io
from datetime import datetime
import pandas as pd

def export_dataframe_to_csv_bytes(df: pd.DataFrame, prefix: str = "snapshot"):
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = f"{prefix}_{ts}.csv"
    data = df.to_csv(index=False).encode("utf-8")
    return name, data
