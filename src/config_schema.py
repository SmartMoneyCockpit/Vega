from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field, ValidationError
import yaml

class Exchange(BaseModel):
    name: str
    indices: List[str] = Field(default_factory=list)
    etfs: List[str] = Field(default_factory=list)

class Providers(BaseModel):
    order: List[str] = Field(default_factory=lambda: ["ibkr","tradingview","polygon"])

class Indicators(BaseModel):
    rsi: Dict[str, int] | None = None
    ema: List[int] | None = None
    sma: List[int] | None = None
    hull: Dict[str, int] | None = None
    guppy: Dict[str, List[int]] | None = None

class UIFlags(BaseModel):
    enable_us: bool = True
    enable_canada: bool = True
    enable_mexico: bool = True
    enable_europe: bool = True
    enable_apac: bool = True

class VegaConfig(BaseModel):
    exchanges: List[Exchange] = Field(default_factory=list)
    fx_pairs: List[str] = Field(default_factory=list)
    commodities: List[str] = Field(default_factory=list)
    ui: UIFlags = UIFlags()
    providers: Providers = Providers()
    indicators: Indicators = Indicators()

def load_config(path: str) -> VegaConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise RuntimeError(f"YAML parse error in {path}: {e}") from e
    except FileNotFoundError as e:
        raise RuntimeError(f"Config file not found: {path}") from e

    try:
        return VegaConfig.model_validate(data)
    except ValidationError as e:
        details = "\n".join([f"- {'/'.join(map(str,err['loc']))}: {err['msg']}" for err in e.errors()])
        raise RuntimeError(f"Invalid config schema in {path}:\n{details}") from e
