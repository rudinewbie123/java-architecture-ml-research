#!/usr/bin/env python3
"""Run JavaParser AST metrics on immutable Java repository snapshots."""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
MANIFEST = ROOT / "data/java21_strict_manifest.csv"
WORK = ROOT / "work/ast_repos"
OUT = ROOT / "results/ast_metrics"
CLASSES = ROOT / "build/ast_classes"
JAR = ROOT / "tools/javaparser-core-3.26.3.jar"
JAVA_SOURCE = ROOT / "scripts/ast/ArchitectureAstMetrics.java"

for directory in (WORK, OUT, CLASSES):
    directory.mkdir(parents=True, exist_ok=True)

def run(args, cwd=None):
    return subprocess.run(
        args, cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

with MANIFEST.open(newline="", encoding="utf-8") as handle:
    candidates = list(csv.DictReader(handle))

compile_result = run([
    "javac", "-cp", str(JAR), "-d", str(CLASSES), str(JAVA_SOURCE)
])

if compile_result.returncode:
    print(compile_result.stdout)
    sys.exit(compile_result.returncode)

all_metrics = []
all_errors = []
statuses = []

for metadata in candidates:
    repository_name = metadata["repository"]
    destination = WORK / repository_name.replace("/", "__")

    if not (destination / ".git").exists():
        clone = run([
            "git", "clone", "--filter=blob:none",
            f"https://github.com/{repository_name}.git",
            str(destination)
        ])

        if clone.returncode:
            statuses.append({
                **metadata,
                "analysis_status": "CLONE_FAILED",
                "detail": clone.stdout[-1500:]
            })
            continue

    fetch = run(
        ["git", "fetch", "origin", metadata["commit_sha"]],
        cwd=destination
    )
    checkout = run(
        ["git", "checkout", "--detach", metadata["commit_sha"]],
        cwd=destination
    )
    actual_sha = run(
        ["git", "rev-parse", "HEAD"],
        cwd=destination
    ).stdout.strip()

    if (fetch.returncode or checkout.returncode or
            actual_sha != metadata["commit_sha"]):
        statuses.append({
            **metadata,
            "analysis_status": "SHA_PIN_FAILED",
            "actual_sha": actual_sha
        })
        continue

    output_csv = OUT / f"{metadata['candidate_id']}_class_metrics.csv"

    command = [
        "java",
        "-cp", f"{JAR}:{CLASSES}",
        "ArchitectureAstMetrics",
        str(destination),
        metadata["candidate_id"],
        metadata["architecture_label"],
        metadata["domain"],
        actual_sha,
        "reserved",
        str(output_csv)
    ]

    result = run(command)

    if result.returncode:
        statuses.append({
            **metadata,
            "analysis_status": "AST_FAILED",
            "detail": result.stdout[-2000:]
        })
        continue

    statuses.append({
        **metadata,
        "analysis_status": "AST_ANALYZED",
        "actual_sha": actual_sha,
        "analyzer_output": result.stdout.strip()
    })

    if output_csv.exists():
        with output_csv.open(newline="", encoding="utf-8") as handle:
            all_metrics.extend(csv.DictReader(handle))

    error_csv = OUT / f"{metadata['candidate_id']}_parse_errors.csv"
    if error_csv.exists():
        with error_csv.open(newline="", encoding="utf-8") as handle:
            all_errors.extend(csv.DictReader(handle))

def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    columns = list(dict.fromkeys(
        key for row in rows for key in row
    ))

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

write_csv(OUT / "class_ast_metrics.csv", all_metrics)
write_csv(OUT / "parse_errors.csv", all_errors)
write_csv(OUT / "analysis_status.csv", statuses)

print(
    f"AST class records={len(all_metrics)}; "
    f"parse errors={len(all_errors)}; "
    f"repositories={len(statuses)}"
)
