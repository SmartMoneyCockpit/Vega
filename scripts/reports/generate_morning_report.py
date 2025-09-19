import argparse, os, pathlib, datetime, sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--region', required=True)
    p.add_argument('--tz', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.utcnow().isoformat()
    content = f"# Morning Report — {args.region}\n\n- Generated: {now}Z\n- Timezone: {args.tz}\n\nThis is a placeholder report body. Replace with your real generator logic."
    out_path.write_text(content, encoding='utf-8')
    print(f"Wrote {out_path}")
if __name__ == '__main__':
    main()
