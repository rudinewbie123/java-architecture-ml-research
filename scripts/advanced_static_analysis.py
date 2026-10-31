
#!/usr/bin/env python3
"""
Advanced Static Analysis for Java Architecture Research.

Extracts package-level dependency graph metrics from
Java repositories pinned to immutable commit SHAs.

IMPORTANT:
These are source-import graph metrics, not CK CBO,
RFC, WMC, LCOM, or runtime call graph metrics.
"""

import csv
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()

MANIFEST = ROOT / "data/java21_strict_manifest.csv"
WORK = ROOT / "work/repos"
OUT = ROOT / "results/advanced_static"

OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)


def cmd(args, cwd=None):
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )


def write_csv(path, rows):
    if not rows:
        return

    columns = list(
        dict.fromkeys(
            key for row in rows for key in row
        )
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(rows)


def strongly_connected_components(nodes, adjacency):
    """Tarjan algorithm for dependency cycle detection."""

    index = 0
    stack = []
    on_stack = set()

    indices = {}
    lowlinks = {}
    components = []

    def visit(node):
        nonlocal index

        indices[node] = index
        lowlinks[node] = index
        index += 1

        stack.append(node)
        on_stack.add(node)

        for neighbor in adjacency.get(node, []):

            if neighbor not in indices:
                visit(neighbor)

                lowlinks[node] = min(
                    lowlinks[node],
                    lowlinks[neighbor]
                )

            elif neighbor in on_stack:

                lowlinks[node] = min(
                    lowlinks[node],
                    indices[neighbor]
                )

        if lowlinks[node] == indices[node]:

            component = []

            while True:
                neighbor = stack.pop()
                on_stack.remove(neighbor)

                component.append(neighbor)

                if neighbor == node:
                    break

            components.append(component)

    for node in nodes:
        if node not in indices:
            visit(node)

    return components


def source_graph(repository, metadata):

    java_files = [
        path
        for path in repository.rglob("*.java")
        if not any(
            item in path.parts
            for item in (
                ".git",
                "target",
                "build",
                "generated-sources"
            )
        )
    ]

    package_files = defaultdict(list)
    imports_by_file = {}

    import_pattern = re.compile(
        r"(?m)^\s*import\s+(?:static\s+)?([\w.$*]+)\s*;"
    )

    package_pattern = re.compile(
        r"(?m)^\s*package\s+([\w.]+)\s*;"
    )

    for java_file in java_files:

        source = java_file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        package_match = package_pattern.search(source)

        package_name = (
            package_match.group(1)
            if package_match
            else "(default)"
        )

        package_files[package_name].append(java_file)

        imports = import_pattern.findall(source)

        imports_by_file[java_file] = (
            package_name,
            imports
        )

    packages = set(package_files.keys())

    edges = set()

    unresolved_imports = 0
    raw_import_count = 0

    for java_file, (
        source_package,
        imports
    ) in imports_by_file.items():

        for imported in imports:

            raw_import_count += 1

            if imported.endswith(".*"):
                candidate = imported[:-2]

            else:
                candidate = (
                    imported.rsplit(".", 1)[0]
                    if "." in imported
                    else imported
                )

            resolved_package = None

            for package in sorted(
                packages,
                key=len,
                reverse=True
            ):

                if (
                    candidate == package
                    or candidate.startswith(package + ".")
                ):

                    resolved_package = package
                    break

            if resolved_package:

                if resolved_package != source_package:

                    edges.add(
                        (
                            source_package,
                            resolved_package
                        )
                    )

            else:
                unresolved_imports += 1

    adjacency = {
        package: set()
        for package in packages
    }

    in_degree = defaultdict(int)
    out_degree = defaultdict(int)

    for source, target in edges:

        adjacency[source].add(target)

        out_degree[source] += 1
        in_degree[target] += 1

    components = strongly_connected_components(
        packages,
        adjacency
    )

    cyclic_components = [
        component
        for component in components
        if (
            len(component) > 1
            or (
                len(component) == 1
                and component[0] in adjacency.get(
                    component[0],
                    set()
                )
            )
        )
    ]

    package_count = len(packages)
    edge_count = len(edges)

    edge_rows = []

    for source, target in sorted(edges):

        edge_rows.append({
            **metadata,
            "source_package": source,
            "target_package": target
        })

    package_rows = []

    for package in sorted(packages):

        package_rows.append({
            **metadata,
            "package": package,
            "java_file_count": len(
                package_files[package]
            ),
            "fan_in": in_degree[package],
            "fan_out": out_degree[package]
        })

    pom_files = [
        path
        for path in repository.rglob("pom.xml")
        if (
            ".git" not in path.parts
            and "target" not in path.parts
        )
    ]

    module_declarations = 0

    for pom in pom_files:

        try:

            source = pom.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            module_declarations += len(
                re.findall(
                    r"<module>\s*[^<]+\s*</module>",
                    source
                )
            )

        except Exception:
            pass

    summary = {
        **metadata,

        "java_file_count_graph": len(java_files),

        "package_node_count": package_count,

        "package_dependency_edge_count": edge_count,

        "package_dependency_density": (
            round(
                edge_count / (
                    package_count * (package_count - 1)
                ),
                6
            )
            if package_count > 1
            else 0
        ),

        "mean_package_fan_in": (
            round(
                sum(in_degree.values()) / package_count,
                4
            )
            if package_count
            else 0
        ),

        "mean_package_fan_out": (
            round(
                sum(out_degree.values()) / package_count,
                4
            )
            if package_count
            else 0
        ),

        "max_package_fan_in": max(
            in_degree.values(),
            default=0
        ),

        "max_package_fan_out": max(
            out_degree.values(),
            default=0
        ),

        "cyclic_scc_count": len(cyclic_components),

        "packages_in_cycles": sum(
            len(component)
            for component in cyclic_components
        ),

        "raw_import_count": raw_import_count,

        "unresolved_external_or_unmatched_import_count":
            unresolved_imports,

        "pom_file_count": len(pom_files),

        "pom_module_declaration_count":
            module_declarations,

        "metric_method":
            "source_import_package_graph_v1"
    }

    return summary, package_rows, edge_rows


def runtime_inventory(repository, metadata):

    all_files = [
        path
        for path in repository.rglob("*")
        if (
            path.is_file()
            and not any(
                item in path.parts
                for item in (
                    ".git",
                    "target",
                    "build",
                    "node_modules"
                )
            )
        )
    ]

    dockerfiles = [
        path for path in all_files
        if path.name.lower() == "dockerfile"
    ]

    compose_files = [
        path for path in all_files
        if path.name.lower() in (
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml"
        )
    ]

    config_files = [
        path for path in all_files
        if path.name in (
            "application.yml",
            "application.yaml",
            "application.properties",
            "bootstrap.yml",
            "bootstrap.yaml"
        )
    ]

    java_files = [
        path for path in all_files
        if path.suffix == ".java"
    ]

    endpoint_count = 0
    main_method_count = 0

    endpoint_patterns = [
        r"@GetMapping\b",
        r"@PostMapping\b",
        r"@PutMapping\b",
        r"@DeleteMapping\b",
        r"@PatchMapping\b",
        r"@RequestMapping\b"
    ]

    database_patterns = {
        "postgresql": r"postgresql|jdbc:postgresql",
        "mysql": r"jdbc:mysql|mysql",
        "mongodb": r"mongodb|spring.data.mongodb",
        "redis": r"redis",
        "dynamodb": r"dynamodb"
    }

    detected_databases = set()

    for java_file in java_files:

        try:

            source = java_file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

        except Exception:
            continue

        endpoint_count += sum(
            len(re.findall(pattern, source))
            for pattern in endpoint_patterns
        )

        main_method_count += len(
            re.findall(
                r"public\s+static\s+void\s+main\s*\(",
                source
            )
        )

    for config in config_files:

        try:

            source = config.read_text(
                encoding="utf-8",
                errors="ignore"
            ).lower()

        except Exception:
            continue

        for database, pattern in database_patterns.items():

            if re.search(pattern, source):
                detected_databases.add(database)

    return {
        **metadata,

        "dockerfile_count": len(dockerfiles),

        "compose_file_count": len(compose_files),

        "application_config_file_count": len(config_files),

        "spring_mapping_annotation_count": endpoint_count,

        "java_main_method_count": main_method_count,

        "detected_database_markers":
            ";".join(sorted(detected_databases)),

        "runtime_readiness": (
            "CONFIGURATION_PRESENT"
            if dockerfiles or compose_files
            else "CONTAINER_CONFIG_NOT_FOUND"
        ),

        "endpoint_status":
            "STATIC_ANNOTATION_COUNT_ONLY_NOT_SMOKE_TESTED"
    }


def main():

    with MANIFEST.open(
        newline="",
        encoding="utf-8"
    ) as f:

        candidates = list(
            csv.DictReader(f)
        )

    summaries = []
    package_metrics = []
    dependency_edges = []
    repository_status = []
    runtime_rows = []

    for metadata in candidates:

        repository_name = metadata["repository"]

        destination = (
            WORK / repository_name.replace("/", "__")
        )

        if not (destination / ".git").exists():

            result = cmd([
                "git",
                "clone",
                "--filter=blob:none",
                f"https://github.com/{repository_name}.git",
                str(destination)
            ])

            if result.returncode:

                repository_status.append({
                    **metadata,
                    "analysis_status": "CLONE_FAILED",
                    "detail": result.stdout[-2000:]
                })

                continue

        cmd(
            [
                "git",
                "fetch",
                "origin",
                metadata["commit_sha"]
            ],
            cwd=destination
        )

        checkout = cmd(
            [
                "git",
                "checkout",
                "--detach",
                metadata["commit_sha"]
            ],
            cwd=destination
        )

        actual_sha = cmd(
            [
                "git",
                "rev-parse",
                "HEAD"
            ],
            cwd=destination
        ).stdout.strip()

        if (
            checkout.returncode
            or actual_sha != metadata["commit_sha"]
        ):

            repository_status.append({
                **metadata,
                "analysis_status": "SHA_PIN_FAILED",
                "actual_sha": actual_sha
            })

            continue

        summary, packages, edges = source_graph(
            destination,
            metadata
        )

        summaries.append(summary)

        package_metrics.extend(packages)

        dependency_edges.extend(edges)

        runtime_rows.append(
            runtime_inventory(
                destination,
                metadata
            )
        )

        repository_status.append({
            **metadata,
            "analysis_status": "ANALYZED",
            "actual_sha": actual_sha
        })

    write_csv(
        OUT / "repository_dependency_metrics.csv",
        summaries
    )

    write_csv(
        OUT / "package_dependency_metrics.csv",
        package_metrics
    )

    write_csv(
        OUT / "package_dependency_edges.csv",
        dependency_edges
    )

    write_csv(
        OUT / "analysis_status.csv",
        repository_status
    )

    write_csv(
        OUT / "runtime_readiness_inventory.csv",
        runtime_rows
    )

    methodology = {
        "generated_at_utc":
            datetime.now(timezone.utc).isoformat(),

        "metric_family":
            "source-level package dependency graph",

        "resolution":
            "Imports are mapped to the longest package prefix found in the same repository.",

        "limitations": [
            "Unresolved imports include third-party dependencies and imports not mapped to local packages.",

            "Package graph edges approximate source imports, not runtime calls.",

            "These metrics are not CK CBO, RFC, WMC, or LCOM.",

            "Manual validation and AST/bytecode confirmation are required before inferential claims."
        ],

        "runtime_benchmark_executed": False,

        "runtime_inventory_is_static_only": True
    }

    (
        OUT / "methodology.json"
    ).write_text(
        json.dumps(
            methodology,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Analyzed {len(summaries)} repositories; "
        f"package edges={len(dependency_edges)}"
    )


if __name__ == "__main__":
    main()
