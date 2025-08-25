---
name: Alert YAML
about: Paste alert YAML and let Actions write it to config/alerts/
title: "Alert YAML: <REGION DATE>"
labels: ["alert-yaml"]
---

filename: config/alerts/<region>-<YYYY-MM-DD>.yaml

```yaml
region: <REGION>
as_of: <YYYY-MM-DD>
policy:
  keep_active_automations: []
watchlist: []
notes: []
