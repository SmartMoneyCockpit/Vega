import os, json, datetime as dt

# Inputs from env:
# CHANGE_TYPE in {"major","minor","patch"}
# CHANGE_DESC  free text (optional)

ver_path = os.environ.get("VERSION_PATH","config/version.json")
change_type = os.environ.get("CHANGE_TYPE","patch").lower()
desc = os.environ.get("CHANGE_DESC","Preferences updated")

if os.path.exists(ver_path):
    data = json.load(open(ver_path, "r", encoding="utf-8"))
else:
    data = {"version":"0.0.0"}

major, minor, patch = [int(x) for x in data.get("version", "0.0.0").split(".")]
if change_type == "major":
    major, minor, patch = major+1, 0, 0
elif change_type == "minor":
    minor, patch = minor+1, 0
else:
    patch += 1

new_version = f"{major}.{minor}.{patch}"
data.update({
    "version": new_version,
    "last_updated_utc": dt.datetime.utcnow().isoformat()+"Z",
    "change_notes": desc
})
with open(ver_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print(new_version)
