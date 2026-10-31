#!/usr/bin/env python3
"""Structural/provenance validation for HARMONY pilot; no construct validity claim."""
import csv
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
MANIFEST = ROOT / "data/java21_strict_manifest.csv"
EVIDENCE = ROOT / "data/architecture_label_evidence.csv"
AST = ROOT / "results/ast_metrics/class_ast_metrics.csv"
OUT = ROOT / "results/dataset_validation"
OUT.mkdir(parents=True, exist_ok=True)

REQUIRED = {
    "candidate_id", "commit_sha", "architecture_label", "domain",
    "source_file", "package_name", "type_name", "type_kind",
    "method_count", "field_count", "wmc_ast", "rfc_source_proxy",
    "cbo_local_type_proxy", "lcom1_name_based_proxy", "physical_loc"
}
NUMERIC = [
    "method_count", "field_count", "wmc_ast", "rfc_source_proxy",
    "cbo_local_type_proxy", "lcom1_name_based_proxy", "physical_loc"
]
KEY = ["candidate_id", "source_file", "package_name", "type_name", "type_kind"]

def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

def main():
    issues = []
    manifest = read_csv(MANIFEST)
    evidence = read_csv(EVIDENCE)
    ast_rows = read_csv(AST)
    if not manifest or not ast_rows:
        raise ValueError("Manifest or AST dataset is empty.")

    missing = sorted(REQUIRED - set(ast_rows[0]))
    if missing:
        raise ValueError("AST schema missing columns: " + ", ".join(missing))

    manifest_by_id = {r["candidate_id"]: r for r in manifest}
    evidence_by_id = {r["candidate_id"]: r for r in evidence}
    if len(manifest_by_id) != len(manifest):
        issues.append("Duplicate candidate_id in manifest.")
    if len(evidence_by_id) != len(evidence):
        issues.append("Duplicate candidate_id in evidence register.")

    counts = Counter()
    identities = Counter()
    aggregates = {}
    sha_mismatch, label_mismatch = set(), set()
    invalid_numeric = []
    missing_source = 0

    for line, row in enumerate(ast_rows, start=2):
        cid = row.get("candidate_id", "")
        counts[cid] += 1
        if cid not in manifest_by_id:
            issues.append(f"Unknown candidate_id at AST row {line}: {cid}")
            continue
        meta = manifest_by_id[cid]
        if row.get("commit_sha", "").lower() != meta["commit_sha"].lower():
            sha_mismatch.add(cid)
        if row.get("architecture_label") != meta["architecture_label"]:
            label_mismatch.add(cid)
        identities[tuple((row.get(k) or "").strip() for k in KEY)] += 1
        if not row.get("source_file"):
            missing_source += 1

        agg = aggregates.setdefault(cid, {
            "candidate_id": cid,
            "repository": meta["repository"],
            "commit_sha": meta["commit_sha"],
            "architecture_label": meta["architecture_label"],
            "domain": meta["domain"],
            "class_record_count": 0,
            "method_count_sum": 0,
            "field_count_sum": 0,
            "wmc_sum": 0,
            "mean_wmc_per_type": 0,
            "mean_rfc_source_proxy": 0,
            "mean_cbo_local_type_proxy": 0,
            "mean_lcom1_name_based_proxy": 0,
            "mean_physical_loc": 0
        })
        agg["class_record_count"] += 1

        for field in NUMERIC:
            try:
                val = float(row[field])
                if not math.isfinite(val) or val < 0:
                    raise ValueError()
            except (ValueError, TypeError, KeyError):
                invalid_numeric.append({"csv_row": line, "field": field, "value": row.get(field)})
                continue
            agg.setdefault("_" + field, []).append(val)

    duplicates = sum(v - 1 for v in identities.values() if v > 1)
    if duplicates:
        issues.append(f"Duplicate class identity records: {duplicates}")
    if missing_source:
        issues.append(f"Missing source_file values: {missing_source}")
    if invalid_numeric:
        issues.append(f"Invalid numeric values: {len(invalid_numeric)}")
    if sha_mismatch:
        issues.append("Commit SHA mismatch: " + ", ".join(sorted(sha_mismatch)))
    if label_mismatch:
        issues.append("Label mismatch: " + ", ".join(sorted(label_mismatch)))

    for cid, agg in aggregates.items():
        for field in NUMERIC:
            vals = agg.pop("_" + field, [])
            mean = sum(vals) / len(vals) if vals else 0
            if field == "method_count":
                agg["method_count_sum"] = int(sum(vals))
            elif field == "field_count":
                agg["field_count_sum"] = int(sum(vals))
            elif field == "wmc_ast":
                agg["wmc_sum"] = int(sum(vals))
                agg["mean_wmc_per_type"] = round(mean, 6)
            elif field == "rfc_source_proxy":
                agg["mean_rfc_source_proxy"] = round(mean, 6)
            elif field == "cbo_local_type_proxy":
                agg["mean_cbo_local_type_proxy"] = round(mean, 6)
            elif field == "lcom1_name_based_proxy":
                agg["mean_lcom1_name_based_proxy"] = round(mean, 6)
            elif field == "physical_loc":
                agg["mean_physical_loc"] = round(mean, 6)

    unverified = []
    for cid in manifest_by_id:
        item = evidence_by_id.get(cid, {})
        if (item.get("verification_status", "").upper() != "VERIFIED"
                or not item.get("evidence_url", "").strip()):
            unverified.append(cid)

    missing_candidates = sorted(set(manifest_by_id) - set(counts))
    if missing_candidates:
        issues.append("Candidates without AST records: " + ", ".join(missing_candidates))

    write_csv(OUT / "repository_level_features.csv", list(aggregates.values()))
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_stage": "HARMONY pilot v0.4 structural validation",
        "manifest_candidate_count": len(manifest),
        "ast_record_count": len(ast_rows),
        "candidate_record_counts": dict(counts),
        "repository_level_sample_count": len(aggregates),
        "duplicate_class_identity_count": duplicates,
        "missing_source_file_count": missing_source,
        "invalid_numeric_value_count": len(invalid_numeric),
        "commit_sha_mismatch_candidates": sorted(sha_mismatch),
        "manifest_label_mismatch_candidates": sorted(label_mismatch),
        "unverified_architecture_labels": unverified,
        "missing_ast_candidates": missing_candidates,
        "structural_issues": issues,
        "model_training_gate": (
            "NOT_READY" if issues or unverified or missing_candidates
            else "STRUCTURAL_PASS_REQUIRES_SAMPLE_SIZE_AND_CONSTRUCT_VALIDITY_REVIEW"
        ),
        "unit_of_analysis": "repository for architecture-level inference; class records are nested observations",
        "metric_warning": "RFC, CBO, and LCOM columns remain proxies and are not certified CK metrics."
    }
    (OUT / "dataset_quality_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 2 if issues else 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("DATASET_VALIDATION_FATAL:", str(exc), file=sys.stderr)
        sys.exit(2)
