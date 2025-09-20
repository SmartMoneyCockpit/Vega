
from __future__ import annotations
import os, yaml
import pandas as pd

DEFAULT_WEIGHTS = {"rt": 0.4, "rs": 0.3, "rv": 0.3}

def _load_weights_from_yaml(path: str):
    if not os.path.exists(path):
        return DEFAULT_WEIGHTS
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        formula = (data.get("scoring",{}).get("vst",{}).get("formula","") or "").replace(" ","")
        w = {}
        for part in formula.split("+"):
            if "*" in part:
                a,b = part.split("*",1)
                w[b] = float(a)
        if {"rt","rs","rv"} <= set(w):
            return {"rt": w["rt"], "rs": w["rs"], "rv": w["rv"]}
    except Exception:
        pass
    return DEFAULT_WEIGHTS

def compute_vv_columns(df: pd.DataFrame, config_yaml_path: str | None = None) -> pd.DataFrame:
    if df is None or df.empty: return df
    weights = DEFAULT_WEIGHTS if not config_yaml_path else _load_weights_from_yaml(config_yaml_path)
    out = df.copy()
    ren = {"RT":"rt","RS":"rs","RV":"rv","CI":"ci","EPS":"eps","Growth":"growth","Sales Growth":"sales_growth","salesGrowth":"sales_growth","VST":"vst"}
    for k,v in ren.items():
        if k in out.columns and v not in out.columns:
            out[v] = out[k]
    if all(c in out.columns for c in ["rt","rs","rv"]) and "vst" not in out.columns:
        out["vst"] = (weights["rt"]*out["rt"].astype(float) + weights["rs"]*out["rs"].astype(float) + weights["rv"]*out["rv"].astype(float))
    for c in ["rt","rs","rv","ci","vst"]:
        if c in out.columns:
            out[c] = out[c].astype(float).clip(0,2)
    pref = ["symbol","name","price","rt","rv","rs","vst","ci","eps","growth","sales_growth"]
    cols = [c for c in pref if c in out.columns] + [c for c in out.columns if c not in pref]
    return out[cols]
