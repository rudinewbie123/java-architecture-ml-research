#!/usr/bin/env python3
"""HARMONY v0.5 repository-level feature audit and architecture-label gate.

This script creates descriptive repository-level features and a transparent
label-verification gate. It does not train a model or certify architecture labels.
"""
import csv, json, math, statistics, sys
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
AST = ROOT / "results/ast_metrics/class_ast_metrics.csv"
MANIFEST = ROOT / "data/java21_strict_manifest.csv"
EVIDENCE = ROOT / "data/architecture_label_evidence_v05.csv"
OUT = ROOT / "results/harmony_v05"
OUT.mkdir(parents=True, exist_ok=True)

FEATURES = {
    "method_count": "methods",
    "field_count": "fields",
    "wmc_ast": "wmc",
    "rfc_source_proxy": "rfc_proxy",
    "cbo_local_type_proxy": "cbo_proxy",
    "lcom1_name_based_proxy": "lcom_proxy",
    "physical_loc": "type_loc"
}
KEYS = ["candidate_id", "source_file", "package_name", "type_name", "type_kind"]

def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def gini(values):
    xs = sorted(max(0.0, x) for x in values)
    if not xs or sum(xs) == 0:
        return 0.0
    n = len(xs)
    weighted = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * weighted) / (n * sum(xs)) - (n + 1) / n

def quantile(xs, q):
    ys = sorted(xs)
    if not ys:
        return 0.0
    pos = (len(ys) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ys[lo]
    return ys[lo] * (hi - pos) + ys[hi] * (pos - lo)

def main():
    ast = read_csv(AST)
    manifest = read_csv(MANIFEST)
    evidence = read_csv(EVIDENCE)

    if not ast:
        raise ValueError("AST CSV has no records.")
    required = set(KEYS + ["commit_sha", "architecture_label", "domain"] + list(FEATURES))
    missing = sorted(required - set(ast[0]))
    if missing:
        raise ValueError("AST schema missing columns: " + ", ".join(missing))

    manifest_by_id = {r["candidate_id"]: r for r in manifest}
    evidence_by_id = {r["candidate_id"]: r for r in evidence}
    grouped = defaultdict(list)
    issues = []
    for line, row in enumerate(ast, 2):
        cid = row["candidate_id"]
        if cid not in manifest_by_id:
            issues.append(f"Unknown candidate {cid} at AST row {line}")
            continue
        meta = manifest_by_id[cid]
        if row["commit_sha"].lower() != meta["commit_sha"].lower():
            issues.append(f"SHA mismatch: {cid}")
        if row["architecture_label"] != meta["architecture_label"]:
            issues.append(f"Manifest label mismatch: {cid}")
        for key in KEYS:
            row[key] = row.get(key, "").strip()
        grouped[cid].append(row)

    repo_rows = []
    class_rows = []
    for cid, rows in grouped.items():
        meta = manifest_by_id[cid]
        identity = [tuple(r[k] for k in KEYS) for r in rows]
        duplicate_count = len(identity) - len(set(identity))
        numeric = {}
        for field in FEATURES:
            vals = []
            for i, row in enumerate(rows):
                try:
                    value = float(row[field])
                    if not math.isfinite(value) or value < 0:
                        raise ValueError()
                    vals.append(value)
                except (ValueError, TypeError):
                    issues.append(f"Invalid {field} in {cid}, class row {i+1}")
            numeric[field] = vals

        out = {
            "candidate_id": cid,
            "repository": meta["repository"],
            "commit_sha": meta["commit_sha"],
            "architecture_label": meta["architecture_label"],
            "domain": meta["domain"],
            "class_record_count": len(rows),
            "duplicate_class_identity_count": duplicate_count,
            "class_record_share": 0.0
        }
        for field, prefix in FEATURES.items():
            vals = numeric[field]
            if not vals:
                continue
            out[f"{prefix}_sum"] = round(sum(vals), 6)
            out[f"{prefix}_mean"] = round(statistics.mean(vals), 6)
            out[f"{prefix}_median"] = round(statistics.median(vals), 6)
            out[f"{prefix}_q1"] = round(quantile(vals, .25), 6)
            out[f"{prefix}_q3"] = round(quantile(vals, .75), 6)
            out[f"{prefix}_sd"] = round(statistics.stdev(vals), 6) if len(vals) > 1 else 0
            out[f"{prefix}_gini"] = round(gini(vals), 6)
        out["type_kind_counts"] = json.dumps(dict(Counter(r["type_kind"] for r in rows)), sort_keys=True)
        out["package_count_observed"] = len({r["package_name"] for r in rows if r["package_name"]})
        out["label_verification_status"] = evidence_by_id.get(cid, {}).get("verification_status", "MISSING")
        repo_rows.append(out)

    total_classes = sum(r["class_record_count"] for r in repo_rows)
    for row in repo_rows:
        row["class_record_share"] = round(row["class_record_count"] / total_classes, 6) if total_classes else 0
    write_csv(OUT/"repository_features_v05.csv", repo_rows)

    class_counts = [r["class_record_count"] for r in repo_rows]
    dominant = max(repo_rows, key=lambda r:r["class_record_count"]) if repo_rows else {}
    unverified = []
    evidence_issues = []
    for meta in manifest:
        cid = meta["candidate_id"]
        ev = evidence_by_id.get(cid, {})
        if (ev.get("verification_status","").upper() != "VERIFIED"
            or not ev.get("evidence_url","").strip()
            or not ev.get("reviewer_id","").strip()
            or not ev.get("evidence_type","").strip()):
            unverified.append(cid)
        if ev.get("verification_status","").upper() == "VERIFIED":
            if not ev.get("evidence_url","").strip() or not ev.get("reviewer_id","").strip():
                evidence_issues.append(cid)

    architecture_counts = Counter(r["architecture_label"] for r in manifest)
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_stage": "HARMONY v0.5 repository feature and label audit",
        "manifest_repository_count": len(manifest),
        "repository_feature_rows": len(repo_rows),
        "class_ast_records": total_classes,
        "architecture_class_counts": dict(architecture_counts),
        "largest_class_record_contributor": dominant.get("candidate_id"),
        "largest_class_record_share": dominant.get("class_record_share"),
        "class_record_count_gini_across_repositories": round(gini(class_counts), 6),
        "unverified_architecture_labels": unverified,
        "evidence_register_inconsistencies": evidence_issues,
        "structural_issues": issues,
        "model_training_gate": "NOT_READY" if issues or unverified or len(manifest) < 30 else "REQUIRES_EXTERNAL_VALIDATION",
        "inference_unit": "repository; class-level records are nested observations",
        "limitations": [
            "Five repositories are a pilot feasibility sample, not sufficient for robust supervised learning.",
            "Class-level AST metrics are descriptive features and must not be treated as independent repository samples.",
            "RFC, CBO, and LCOM remain source-level proxies; WMC is a project-specific AST operationalization.",
            "Architecture labels remain unverified until independent documentary evidence and expert review are recorded.",
            "Repository-level summaries of class features do not measure runtime behavior or deployment topology."
        ]
    }
    (OUT/"harmony_v05_audit_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 2 if issues else 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("HARMONY_V05_FATAL:", str(exc), file=sys.stderr)
        sys.exit(2)
