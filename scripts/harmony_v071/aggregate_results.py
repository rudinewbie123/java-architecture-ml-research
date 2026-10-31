#!/usr/bin/env python3
"""Merge per-repository HARMONY v0.7.1 artifacts into auditable CSV/JSON outputs."""
import argparse
import csv
import json
from pathlib import Path
from datetime import datetime, timezone

def read_csv_files(paths):
    rows = []
    for path in paths:
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows.extend(csv.DictReader(f))
    return rows

def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    src, out = Path(args.input_dir), Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    build_files = sorted(src.glob("*_build_result.json"))
    feature_files = sorted(src.glob("*_repository_features.csv"))
    class_files = sorted(src.glob("*_class_ast_metrics.csv"))

    builds = [json.loads(p.read_text(encoding="utf-8")) for p in build_files]
    features = read_csv_files(feature_files)
    classes = read_csv_files(class_files)

    write_csv(out / "build_results_v071.csv", builds)
    write_csv(out / "repository_features_v071.csv", features)
    write_csv(out / "class_ast_metrics_v071.csv", classes)

    statuses = {}
    for row in builds:
        status = row.get("build_status", "UNKNOWN")
        statuses[status] = statuses.get(status, 0) + 1

    summary = {
        "dataset_version": "HARMONY-v0.7.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_build_result_files": len(build_files),
        "repository_feature_rows": len(features),
        "class_ast_records": len(classes),
        "build_status_counts": statuses,
        "pinned_sha_confirmed": sum(
            r.get("checkout_status") == "PINNED_SHA_CONFIRMED" for r in builds
        ),
        "static_extraction_pass": sum(
            r.get("static_extraction_status") == "PASS" for r in builds
        ),
        "runtime_benchmark_executed": False,
        "limitations": [
            "Build success is not proof of architecture-label validity.",
            "Static source/configuration counts are proxies, not runtime observations.",
            "Package import graph is not a complete call graph.",
            "REST/Kafka/gRPC/Lambda occurrences do not independently establish an architecture class.",
            "Candidate labels remain unverified pending expert review."
        ]
    }
    (out / "harmony_v071_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
