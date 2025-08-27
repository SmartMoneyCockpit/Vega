from __future__ import annotations
from typing import Dict, List, Any

class DemoDataProvider:
    def get_macro_snapshot(self) -> Dict[str, Any]:
        return {
            "tone": "mixed-to-cautious",
            "usd": "softer", "gold": "firm", "oil": "softer", "rates": "mixed", "vix": "low-mid",
            "vix_level": 15.8, "vix_chg": "+0.2",
            "indices": {"SPY": {"level": "643.0", "pct": "+0.0%"},
                        "QQQ": {"level": "571.0", "pct": "+0.2%"},
                        "IWM": {"level": "234.0", "pct": "+0.7%"}}
        }

    def get_benchmark_and_breadth(self) -> Dict[str, Any]:
        return {
            "benchmarks": [
                {"Index": "SPY", "Level": 643.0, "% Chg": 0.0, "vs SPY": "—", "Breadth": "55% adv", "Notes": "VWAP magnet"},
                {"Index": "QQQ", "Level": 571.0, "% Chg": 0.2, "vs SPY": "Stronger", "Breadth": "62% adv", "Notes": "Tech leads"},
                {"Index": "IWM", "Level": 234.0, "% Chg": 0.7, "vs SPY": "Strongest", "Breadth": "65% adv", "Notes": "Small-cap bid"},
                {"Index": "DIA", "Level": 43150, "% Chg": -0.1, "vs SPY": "Weaker", "Breadth": "48% adv", "Notes": "Mixed"},
            ],
            "sectors": [
                {"Sector": "XLK (Tech)", "% Chg": 0.3, "Breadth": "65%", "Rel Strength": "🟢"},
                {"Sector": "XLI (Industrials)", "% Chg": 0.4, "Breadth": "62%", "Rel Strength": "🟢"},
                {"Sector": "XLV (Health Care)", "% Chg": 0.3, "Breadth": "60%", "Rel Strength": "🟢"},
                {"Sector": "XLF (Financials)", "% Chg": 0.0, "Breadth": "52%", "Rel Strength": "🟡"},
                {"Sector": "XLB (Materials)", "% Chg": 0.0, "Breadth": "50%", "Rel Strength": "🟡"},
                {"Sector": "XLE (Energy)", "% Chg": -1.1, "Breadth": "42%", "Rel Strength": "🔴"},
            ],
            "takeaway": "Rotation signal: IWM > QQQ > SPY > DIA; avoid Energy until oil stabilizes.",
        }

    def get_options_skews(self) -> List[Dict[str, Any]]:
        return [
            {"ticker": "BA", "ivr": "38", "skew": "calls slightly underpriced", "plan": "Long calls/spreads (21–60 DTE)"},
            {"ticker": "IBKR", "ivr": "28", "skew": "balanced, cheap IV", "plan": "Long calls/spreads into S&P inclusion"},
            {"ticker": "LLY", "ivr": "55", "skew": "calls rich", "plan": "Stock only"},
            {"ticker": "SATS", "ivr": ">90", "skew": "calls extremely overpriced", "plan": "Avoid options; wait for stabilization"},
        ]

    def get_catalyst_board(self) -> List[Dict[str, Any]]:
        return [
            {"title": "Boeing (BA)", "summary": "Large Asia order; industrials leadership",
             "details": "Order momentum supports XLI; watch VWAP holds.",
             "plan": "Lean long above intraday high; invalidate on VWAP loss + XLI rollover"},
            {"title": "Interactive Brokers (IBKR)", "summary": "S&P 500 inclusion flows",
             "details": "Indexer demand supports dips; options cheap.",
             "plan": "Buy late-day strength or pullbacks; fade if VIX>17"},
        ]

    def get_session_map(self) -> List[Dict[str, str]]:
        return [
            {"window": "09:30–10:00 PT", "text": "Watch opening range resolution; set alerts at ORH/ORL & VWAP for SPY/QQQ/IWM."},
            {"window": "10:00–11:00 PT", "text": "Rebalance flows; confidence data digestion. Breadth trend is key."},
            {"window": "11:00–12:30 PT", "text": "Midday drift risk. If IWM leads → keep tactical longs open."},
            {"window": "12:30–13:00 PT (close)", "text": "Fade risk into close if breadth deteriorates; otherwise ride trend with stops under VWAP."},
        ]

    def get_color_guard_inputs(self) -> Dict[str, str]:
        return {"price_signal": "green", "breadth_signal": "yellow", "risk_signal": "yellow"}

    def get_final_risk_overlay(self) -> Dict[str, Any]:
        return {
            "primary": "VIX > 17 & SPY < VWAP & breadth <45% → add ¼ hedge (SPXU/SQQQ/RWM), scale to ½ if persists 2+ hrs.",
            "secondary": "USO < day-low & down >2% → avoid XLE; DXY > 99 or USDMXN > 18.90 or USDCAD > 1.39 → tighten stops.",
            "fx": "CAD neutral (oil weak offsets USD soft); MXN firm while USD soft.",
            "tactical": [
                "Risk-On if IWM > VWAP and SPY/QQQ hold PDH; breadth >60%",
                "Risk-Off if SPY loses VWAP and breadth <45% with VIX >17",
                "Neutral if chop around VWAP ±0.5% and breadth ~50–55%",
            ],
            "trade_board": [
                {"Ticker": "BA", "Status": "🟢 Trade Now (calls/spreads)"},
                {"Ticker": "IBKR", "Status": "🟢 Trade Now (calls/spreads)"},
                {"Ticker": "BMO/BNS", "Status": "🟢 Buy dips"},
                {"Ticker": "LLY", "Status": "🟡 Wait — stock only"},
                {"Ticker": "T", "Status": "🟡 Wait — call spreads if stabilizes"},
                {"Ticker": "SATS", "Status": "🔴 Avoid — IV extreme"},
                {"Ticker": "SPY/QQQ/IWM", "Status": "🟡 Wait — confirm breadth + VWAP"},
                {"Ticker": "GLD", "Status": "🟢 Dip-buy bias"},
                {"Ticker": "XLE", "Status": "🔴 Avoid until crude stabilizes"},
            ]
        }
