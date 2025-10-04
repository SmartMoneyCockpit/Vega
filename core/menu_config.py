import yaml, os
def load_menu_config(path: str = "menu_config.yaml"):
    if not os.path.exists(path):
        return {"groups": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if "groups" not in data or not isinstance(data["groups"], list):
            return {"groups": []}
        return data
    except Exception:
        return {"groups": []}
