"""
Utilities for VectorVest-style metrics in Vega Cockpit.

Expected input columns if available:
- rt, rs, rv, ci  (scaled ~0–2)
- eps (EPS), growth (earnings growth %), sales_growth (sales growth %)
We compute:
- vst = w_rt*rt + w_rs*rs + w_rv*rv  (weights default to 0.4/0.3/0.3, override via _vega_scores.yaml if present)
All outputs are clipped to [0, 2] where applicable.
"""
from __future__ import annotations
import os, yaml
import pandas as pd
from typing import Dict, Any

DEFAULT_WEIGHTS = {"rt": 0.4, "rs": 0.3, "rv": 0.3}

def _load_weights_from_yaml(path: str) -> Dict[str, float]:
    if not os.path.exists(path):
        return DEFAULT_WEIGHTS
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # Expect data['scoring']['vst']['formula'] like "0.4*rt + 0.3*rs + 0.3*rv"
        scoring = data.get("scoring", {})
        vst = scoring.get("vst", {})
        formula = vst.get("formula", "").strip()
        # crude parse
        # Accept tokens like "0.4*rt + 0.3*rs + 0.3*rv"
        weights = {}
        for part in formula.replace(" ", "").split("+"):
            if "*" in part:
                w, k = part.split("*", 1)
                try:
                    weights[k] = float(w)
                except Exception:
                    pass
        if {"rt","rs","rv"}.issubset(weights.keys()):
            return {"rt": weights["rt"], "rs": weights["rs"], "rv": weights["rv"]}
    except Exception:
        pass
    return DEFAULT_WEIGHTS

def compute_vv_columns(df: pd.DataFrame, config_yaml_path: str | None = None) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    weights = DEFAULT_WEIGHTS
    if config_yaml_path:
        weights = _load_weights_from_yaml(config_yaml_path)

    out = df.copy()
    # Harmonize column names
    rename_map = {
        "sales growth": "sales_growth",
        "salesGrowth": "sales_growth",
        "Growth": "growth",
        "EPS": "eps",
        "RT": "rt",
        "RS": "rs",
        "RV": "rv",
        "CI": "ci",
        "VST": "vst",
    }
    for k,v in rename_map.items():
        if k in out.columns and v not in out.columns:
            out[v] = out[k]

    # Compute VST if possible
    if all(c in out.columns for c in ["rt","rs","rv"]) and "vst" not in out.columns:
        out["vst"] = (weights["rt"]*out["rt"].astype(float) +
                      weights["rs"]*out["rs"].astype(float) +
                      weights["rv"]*out["rv"].astype(float))
    # Clip known 0-2 scaled metrics
    for c in ["rt","rs","rv","ci","vst"]:
        if c in out.columns:
            out[c] = out[c].astype(float).clip(0, 2)

    # Order common columns if present
    preferred = ["symbol","name","price","rt","rv","rs","vst","ci","eps","growth","sales_growth"]
    cols = [c for c in preferred if c in out.columns] + [c for c in out.columns if c not in preferred]
    return out[cols]

def merge_metrics(base: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    """Left-merge metrics by 'symbol' onto base."""
    if base is None or base.empty or metrics is None or metrics.empty:
        return base
    if "symbol" not in base.columns or "symbol" not in metrics.columns:
        return base
    m2 = metrics.copy()
    keep_cols = [c for c in m2.columns if c != "symbol"]
    out = base.merge(m2[["symbol"] + keep_cols], on="symbol", how="left")
    return out
