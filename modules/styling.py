def pill(text: str, state: str) -> str:
    cmap = {"softer": "#22c55e", "firmer": "#ef4444", "mixed": "#f59e0b", "low-mid": "#f59e0b"}
    color = cmap.get(state, "#6b7280")
    return f"<span style='background:{color};color:white;padding:2px 8px;border-radius:999px;font-size:12px'>{text}</span>"

def color_block(label: str, color: str) -> str:
    return (f"<div style='display:flex;align-items:center;gap:10px;background:{color}20;border:1px solid {color}55;"
            f"padding:10px 12px;border-radius:10px;'><div style='width:14px;height:14px;border-radius:50%;background:{color}'></div>"
            f"<div style='color:#111827;font-weight:600'>{label}</div></div>")
