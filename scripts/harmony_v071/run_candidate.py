#!/usr/bin/env python3
"""
Run one pinned repository:
1) clone and checkout the exact commit SHA;
2) attempt Maven/Gradle verification under JDK 21;
3) extract Java AST and repository configuration metrics.

Build failure is recorded, not silently treated as exclusion.
No runtime benchmark is performed by this pipeline.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", "target", "build", ".gradle", "node_modules",
    "generated-sources", "out", "dist", ".idea"
}
CLASS_TYPES = {
    "class_declaration", "interface_declaration",
    "enum_declaration", "record_declaration",
    "annotation_type_declaration"
}
METHOD_TYPES = {"method_declaration", "constructor_declaration"}

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def run_cmd(cmd, cwd=None, timeout=3300, log_path=None):
    started = time.monotonic()
    try:
        p = subprocess.run(
            cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout
        )
        output, code = p.stdout, p.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "")
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        output += f"\nTIMEOUT after {timeout} seconds\n"
        code = 124
    except Exception as exc:
        output, code = f"EXECUTION_ERROR: {exc}\n", 125

    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).write_text(output, encoding="utf-8", errors="replace")

    return {
        "exit_code": code,
        "duration_seconds": round(time.monotonic() - started, 3),
        "output": output
    }

def load_manifest(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows

def excluded(path):
    return any(part in EXCLUDED_DIRS for part in path.parts)

def discover_build_roots(repo):
    poms = [p for p in repo.rglob("pom.xml") if not excluded(p.relative_to(repo))]
    gradle_files = [
        p for p in repo.rglob("*")
        if p.is_file() and p.name in {
            "build.gradle", "build.gradle.kts", "settings.gradle",
            "settings.gradle.kts"
        } and not excluded(p.relative_to(repo))
    ]

    def shallowest(paths):
        paths = sorted(set(paths), key=lambda p: (len(p.relative_to(repo).parts), str(p)))
        roots = []
        for path in paths:
            # Only an ancestor directory's descriptor makes this a nested module.
            ancestors = list(path.parent.parents)
            has_parent_pom = any((ancestor / "pom.xml").exists() for ancestor in ancestors)
            if not has_parent_pom:
                roots.append(path)
        # A root POM owns its Maven submodules.
        root_pom = repo / "pom.xml"
        if root_pom in roots:
            return [root_pom]
        return roots

    maven_roots = shallowest(poms)
    gradle_roots = shallowest(gradle_files)
    # settings.gradle and build.gradle in the same directory represent one build.
    gradle_dirs = sorted({p.parent for p in gradle_roots}, key=lambda p: (len(p.relative_to(repo).parts), str(p)))
    selected_gradle = []
    for d in gradle_dirs:
        if not any(existing == d or existing in d.parents for existing in selected_gradle):
            selected_gradle.append(d)

    return maven_roots, selected_gradle

def build_repository(repo, candidate_id, out_dir):
    maven_roots, gradle_roots = discover_build_roots(repo)
    results = []

    for idx, pom in enumerate(maven_roots, 1):
        wrapper = pom.parent / "mvnw"
        cmd = ["./mvnw", "-B", "-ntp", "-Dstyle.color=never", "clean", "verify"] if wrapper.exists() else [
            "mvn", "-B", "-ntp", "-Dstyle.color=never", "-f", str(pom.resolve()), "clean", "verify"
        ]
        if wrapper.exists():
            wrapper.chmod(wrapper.stat().st_mode | 0o111)
        log = out_dir / f"{candidate_id}_maven_{idx}.log"
        r = run_cmd(cmd, cwd=pom.parent, log_path=log)
        results.append({
            "build_system": "maven", "build_root": str(pom.parent.relative_to(repo)),
            "command": " ".join(cmd), "exit_code": r["exit_code"],
            "duration_seconds": r["duration_seconds"], "log_file": log.name
        })

    for idx, gradle_dir in enumerate(gradle_roots, 1):
        wrapper = gradle_dir / "gradlew"
        cmd = ["./gradlew", "--no-daemon", "clean", "build"] if wrapper.exists() else [
            "gradle", "--no-daemon", "clean", "build"
        ]
        if wrapper.exists():
            wrapper.chmod(wrapper.stat().st_mode | 0o111)
        log = out_dir / f"{candidate_id}_gradle_{idx}.log"
        r = run_cmd(cmd, cwd=gradle_dir, log_path=log)
        results.append({
            "build_system": "gradle", "build_root": str(gradle_dir.relative_to(repo)),
            "command": " ".join(cmd), "exit_code": r["exit_code"],
            "duration_seconds": r["duration_seconds"], "log_file": log.name
        })

    if not results:
        status = "NO_BUILD_DESCRIPTOR"
    elif all(x["exit_code"] == 0 for x in results):
        status = "BUILD_PASS"
    elif any(x["exit_code"] == 0 for x in results):
        status = "PARTIAL_BUILD_PASS"
    else:
        status = "BUILD_FAILED"

    return status, results

def walk_nodes(node):
    yield node
    for child in node.children:
        yield from walk_nodes(child)

def extract_static_features(repo, metadata):
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_java
        language = Language(tree_sitter_java.language())
        parser = Parser(language)
    except Exception as exc:
        raise RuntimeError(f"Tree-sitter initialization failed: {exc}")

    java_files = [
        p for p in repo.rglob("*.java")
        if not excluded(p.relative_to(repo))
    ]

    class_rows = []
    packages = set()
    package_file_map = defaultdict(list)
    imports_by_package = defaultdict(set)
    syntax_error_files = []
    totals = defaultdict(int)
    source_loc = nonblank_loc = 0
    package_re = re.compile(r"(?m)^\s*package\s+([\w.]+)\s*;")
    import_re = re.compile(r"(?m)^\s*import\s+(?:static\s+)?([\w.*]+)\s*;")

    for java_file in java_files:
        source_bytes = java_file.read_bytes()
        source = source_bytes.decode("utf-8", errors="replace")
        source_loc += len(source.splitlines())
        nonblank_loc += sum(bool(line.strip()) for line in source.splitlines())

        pm = package_re.search(source)
        package = pm.group(1) if pm else "(default)"
        packages.add(package)
        package_file_map[package].append(java_file)

        tree = parser.parse(source_bytes)
        root = tree.root_node
        if root.has_error:
            syntax_error_files.append(str(java_file.relative_to(repo)))

        imports = import_re.findall(source)
        imports_by_package[package].update(imports)

        nodes = list(walk_nodes(root))
        for node in nodes:
            if node.type in CLASS_TYPES:
                totals["type_declaration_count"] += 1
                name_node = node.child_by_field_name("name")
                class_name = name_node.text.decode("utf-8", errors="replace") if name_node else "(anonymous)"
                methods = sum(1 for n in walk_nodes(node) if n.type in METHOD_TYPES)
                fields = sum(1 for n in walk_nodes(node) if n.type in {"field_declaration", "constant_declaration"})
                annotations = sum(1 for n in walk_nodes(node) if n.type == "annotation")
                class_rows.append({
                    **metadata,
                    "source_file": str(java_file.relative_to(repo)),
                    "package": package,
                    "type_name": class_name,
                    "type_node": node.type,
                    "method_constructor_count": methods,
                    "field_declaration_count": fields,
                    "annotation_count": annotations,
                    "source_line_count": node.end_point.row - node.start_point.row + 1,
                    "syntax_error_in_file": bool(root.has_error)
                })
            elif node.type in METHOD_TYPES:
                totals["method_constructor_count"] += 1
            elif node.type == "field_declaration":
                totals["field_declaration_count"] += 1
            elif node.type == "import_declaration":
                totals["import_declaration_count"] += 1
            elif node.type == "annotation":
                totals["annotation_count"] += 1

    # Build an intra-repository package import graph; external imports are not graph edges.
    edges = set()
    for source_pkg, imports in imports_by_package.items():
        for imp in imports:
            candidate = imp[:-2] if imp.endswith(".*") else (imp.rsplit(".", 1)[0] if "." in imp else imp)
            matches = [p for p in packages if candidate == p or candidate.startswith(p + ".")]
            if matches:
                target_pkg = max(matches, key=len)
                if target_pkg != source_pkg:
                    edges.add((source_pkg, target_pkg))

    indegree = defaultdict(int)
    outdegree = defaultdict(int)
    for a, b in edges:
        outdegree[a] += 1
        indegree[b] += 1

    all_files = [
        p for p in repo.rglob("*")
        if p.is_file() and not excluded(p.relative_to(repo))
    ]
    names = [p.name.lower() for p in all_files]
    paths = [str(p.relative_to(repo)).lower() for p in all_files]

    def count_name(pattern):
        rx = re.compile(pattern)
        return sum(1 for n, path in zip(names, paths) if rx.search(n) or rx.search(path))

    text_files = [
        p for p in all_files
        if p.suffix.lower() in {".java", ".xml", ".yml", ".yaml", ".json", ".toml", ".properties", ".gradle", ".kts"}
    ]
    text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in text_files[:2500]
    )

    java_version_patterns = [
        r"<maven\\.compiler\\.release>\\s*([^<]+)",
        r"<maven\\.compiler\\.source>\\s*([^<]+)",
        r"<maven\\.compiler\\.target>\\s*([^<]+)",
        r"<java\\.version>\\s*([^<]+)",
        r"JavaVersion\\.VERSION_(\\d+)",
        r"JavaLanguageVersion\\.of\\((\\d+)\\)",
        r"sourceCompatibility\\s*=\\s*['\\\"]?([0-9.]+)",
        r"targetCompatibility\\s*=\\s*['\\\"]?([0-9.]+)"
    ]
    declared_java_versions = []
    for pattern in java_version_patterns:
        declared_java_versions.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    declared_java_versions = sorted(set(str(v).strip() for v in declared_java_versions))
    normalized_java_versions = sorted(set(v.split(".")[0] for v in declared_java_versions))
    if not declared_java_versions:
        java_target_config_status = "NOT_DECLARED_IN_SCANNED_FILES"
    elif normalized_java_versions == ["21"]:
        java_target_config_status = "DECLARED_21"
    elif "21" in normalized_java_versions:
        java_target_config_status = "MIXED_DECLARATIONS_REVIEW"
    else:
        java_target_config_status = "DECLARED_NON_21_REVIEW"

    feature = {
        **metadata,
        "declared_java_version_values": ";".join(declared_java_versions),
        "java_target_config_status": java_target_config_status,
        "java_file_count": len(java_files),
        "java_loc_physical": source_loc,
        "java_loc_nonblank": nonblank_loc,
        "package_count": len(packages),
        "type_declaration_count": totals["type_declaration_count"],
        "method_constructor_count": totals["method_constructor_count"],
        "field_declaration_count": totals["field_declaration_count"],
        "annotation_count": totals["annotation_count"],
        "import_declaration_count": totals["import_declaration_count"],
        "package_dependency_edge_count": len(edges),
        "package_dependency_density": round(
            len(edges) / (len(packages) * (len(packages) - 1)), 6
        ) if len(packages) > 1 else 0,
        "mean_package_fan_in": round(sum(indegree.values()) / len(packages), 4) if packages else 0,
        "mean_package_fan_out": round(sum(outdegree.values()) / len(packages), 4) if packages else 0,
        "max_package_fan_in": max(indegree.values(), default=0),
        "max_package_fan_out": max(outdegree.values(), default=0),
        "syntax_error_file_count": len(syntax_error_files),
        "syntax_error_files": ";".join(syntax_error_files[:100]),
        "pom_file_count": count_name(r"^pom\.xml$"),
        "gradle_build_file_count": count_name(r"^build\.gradle(\.kts)?$"),
        "dockerfile_count": count_name(r"^dockerfile$"),
        "compose_file_count": count_name(r"(docker-compose|compose)\.(yml|yaml)$"),
        "kubernetes_manifest_file_count": sum(1 for p in paths if re.search(r"(^|/)(k8s|kubernetes|helm)/", p)),
        "serverless_manifest_file_count": count_name(r"(serverless\.ya?ml|template\.ya?ml|samconfig\.toml)$"),
        "terraform_file_count": count_name(r"\.tf$"),
        "rest_annotation_occurrences": len(re.findall(r"@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping)\b", text)),
        "kafka_occurrences": len(re.findall(r"\b(KafkaTemplate|@KafkaListener|KafkaProducer|KafkaConsumer)\b", text)),
        "grpc_occurrences": len(re.findall(r"\b(io\.grpc|@GrpcService|ManagedChannel)\b", text)),
        "spring_modulith_occurrences": len(re.findall(r"\b(ApplicationModule|@ApplicationModuleListener|org\.springframework\.modulith)\b", text)),
        "aws_lambda_occurrences": len(re.findall(r"\b(AWS::Serverless::Function|RequestHandler|aws-lambda|LambdaLogger)\b", text)),
        "metric_scope": "static_source_and_configuration_only"
    }
    return feature, class_rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--candidate-id", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    rows = load_manifest(args.manifest)
    matches = [r for r in rows if r["candidate_id"] == args.candidate_id]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one candidate {args.candidate_id}, found {len(matches)}")
    row = matches[0]

    cid, repo_name, sha = row["candidate_id"], row["repository"], row["commit_sha"]
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    checkout = out / "source"
    clone_log = out / f"{cid}_clone_checkout.log"

    meta = {
        "candidate_id": cid,
        "repository": repo_name,
        "commit_sha_expected": sha,
        "proposed_architecture_label": row.get("proposed_architecture_label", ""),
        "domain": row.get("domain", ""),
        "java_target_manifest": row.get("java_target", "")
    }

    clone = run_cmd(
        ["git", "clone", "--filter=blob:none", "--no-checkout",
         f"https://github.com/{repo_name}.git", str(checkout)],
        timeout=900, log_path=clone_log
    )
    if clone["exit_code"] != 0:
        result = {**meta, "checkout_status": "CLONE_FAILED", "build_status": "NOT_RUN",
                  "error": f"clone exit {clone['exit_code']}", "timestamp_utc": utcnow()}
        (out / f"{cid}_build_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        raise SystemExit(0)

    fetch = run_cmd(["git", "fetch", "--depth=1", "origin", sha], cwd=checkout,
                    timeout=900, log_path=clone_log)
    checkout_result = run_cmd(["git", "checkout", "--detach", sha], cwd=checkout,
                              timeout=300, log_path=clone_log)
    actual = run_cmd(["git", "rev-parse", "HEAD"], cwd=checkout, timeout=60)
    actual_sha = actual["output"].strip()

    if fetch["exit_code"] != 0 or checkout_result["exit_code"] != 0 or actual_sha.lower() != sha.lower():
        result = {**meta, "checkout_status": "PINNED_SHA_FAILED", "commit_sha_actual": actual_sha,
                  "build_status": "NOT_RUN", "timestamp_utc": utcnow()}
        (out / f"{cid}_build_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        raise SystemExit(0)

    build_status, build_steps = build_repository(checkout, cid, out)
    java_version = run_cmd(["java", "-version"], timeout=30)
    result = {
        **meta,
        "commit_sha_actual": actual_sha,
        "checkout_status": "PINNED_SHA_CONFIRMED",
        "build_status": build_status,
        "build_step_count": len(build_steps),
        "build_steps": build_steps,
        "build_duration_seconds": round(sum(x["duration_seconds"] for x in build_steps), 3),
        "java_version_output": java_version["output"],
        "timestamp_utc": utcnow(),
        "runtime_benchmark_executed": False
    }

    try:
        feature, class_rows = extract_static_features(checkout, meta)
        feature["build_status"] = build_status
        feature["build_step_count"] = len(build_steps)
        feature["build_duration_seconds"] = result["build_duration_seconds"]
        with (out / f"{cid}_repository_features.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(feature.keys()))
            w.writeheader()
            w.writerow(feature)
        if class_rows:
            with (out / f"{cid}_class_ast_metrics.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(class_rows[0].keys()))
                w.writeheader()
                w.writerows(class_rows)
        result["static_extraction_status"] = "PASS"
        result["class_ast_record_count"] = len(class_rows)
        result["java_file_count"] = feature["java_file_count"]
        result["syntax_error_file_count"] = feature["syntax_error_file_count"]
    except Exception as exc:
        result["static_extraction_status"] = "FAILED"
        result["static_extraction_error"] = str(exc)

    (out / f"{cid}_build_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
