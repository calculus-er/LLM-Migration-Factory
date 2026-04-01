"""
Fetch status for a single job (requires running API).

  python scripts/smoke_job.py <job_id>

Uses PUBLIC_API_BASE env or http://localhost:8000.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("PUBLIC_API_BASE", "http://localhost:8000").rstrip("/")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/smoke_job.py <job_id>", file=sys.stderr)
        sys.exit(2)
    job_id = sys.argv[1]
    url = f"{BASE}/api/jobs/{job_id}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(data, indent=2))
    r = data.get("report") or {}
    if r:
        print("\navg_semantic_score:", r.get("avg_semantic_score"))


if __name__ == "__main__":
    main()
