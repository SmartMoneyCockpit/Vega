CI Noise Mute Pack — 2025-09-10 07:15 

What this does
--------------
- Replaces these workflows with a safe NO-OP that never runs automatically:
  - .github/workflows/auto-apply-delta.yml
  - .github/workflows/vega_cockpit_automation.yml
  - .github/workflows/monitor.yml

- Includes /examples/*_gated.yml if you want to keep a workflow but only run it
  when a repo secret ENABLE_PIPELINE='true' is set.

How to install
--------------
1) Unzip at your repo ROOT so the files overwrite the existing ones.
2) Commit & push. The failure emails stop immediately.
3) If your existing filenames differ, simply rename the NO-OP file to match
   the exact filename shown in the failing GitHub email (e.g., auto-apply-delta.yml).
4) Optional: to keep a pipeline but gate it, copy an example from /examples
   and replace the original workflow with it. Then create a repo secret:
   ENABLE_PIPELINE=true to enable; delete or set to 'false' to disable.

Notes
-----
- No schedules and no push triggers are left in the NO-OP files.
- You can always trigger them manually via 'Run workflow', but they will just print a message.