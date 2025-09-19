All-in-One Reports: quick install

1) Copy this bundle into your repo root (preserving folders):
   - .github/workflows/all_in_one_reports.yml
   - scripts/
   - data/templates/
   - tools/

2) Commit & push:
   git add .github/workflows/all_in_one_reports.yml scripts data/templates tools
   git commit -m "All-in-one reports: workflows + scripts + templates + tools"
   git push

3) (Optional) Email:
   Repo secret: SENDGRID_API_KEY
   Repo variables: SENDGRID_FROM, SENDGRID_TO

4) Run it:
   Actions → All-in-One Reports, Email, Monthly Release & Cleanup → Run workflow

5) Badges (optional):
   bash tools/apply_badges.sh YOUR_OWNER YOUR_REPO
   git add README.md && git commit -m "Add CI badges" && git push
