#!/usr/bin/env python3
"""Validate the pinned candidate manifest and emit a GitHub Actions matrix."""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

REQUIRED = {
    "candidate_id", "repository", "commit_sha",
    "java_target", "build_tool"
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    path = Path(args.manifest)
    if not path.is_file():
        raise SystemExit(f"Manifest not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Missing manifest columns: {sorted(missing)}")
        rows = list(reader)

    if not rows:
        raise SystemExit("Manifest is empty.")

    ids, repos = set(), set()
    include = []
    errors = []

    for row in rows:
        cid = row["candidate_id"].strip()
        repo = row["repository"].strip()
        sha = row["commit_sha"].strip()

        if not cid or cid in ids:
            errors.append(f"Blank or duplicate candidate_id: {cid!r}")
        if not repo or repo.count("/") != 1:
            errors.append(f"{cid}: repository must be owner/name, got {repo!r}")
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            errors.append(f"{cid}: commit_sha must be a 40-character SHA")
        if row["java_target"].strip() != "21":
            errors.append(f"{cid}: strict Java policy requires java_target=21")
        if repo in repos:
            errors.append(f"{cid}: duplicate repository {repo}")

        ids.add(cid)
        repos.add(repo)
        include.append({
            "candidate_id": cid,
            "repository": repo,
            "commit_sha": sha
        })

    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(2)

    print(json.dumps(include, separators=(",", ":")))

if __name__ == "__main__":
    main()
