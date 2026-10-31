#!/usr/bin/env python3
import csv, json, re, subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.cwd()
MANIFEST=ROOT/"data/java21_strict_manifest.csv"
WORK=ROOT/"work/repos"
OUT=ROOT/"results"
OUT.mkdir(exist_ok=True,parents=True)
WORK.mkdir(exist_ok=True,parents=True)

def run(cmd,cwd=None,log=None):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if log: Path(log).write_text(p.stdout,encoding="utf-8")
    return p

def metrics(repo, meta):
    try: import lizard
    except Exception: lizard=None
    files=[p for p in repo.rglob("*.java") if not any(x in p.parts for x in (".git","target","build","generated-sources"))]
    packages=set(); types=set(); imports=set()
    total=nonblank=module_ann=event_ann=rest=handlers=0
    ccs=[]
    for f in files:
        s=f.read_text(encoding="utf-8",errors="ignore")
        total+=len(s.splitlines()); nonblank+=sum(bool(x.strip()) for x in s.splitlines())
        packages.update(re.findall(r"(?m)^\s*package\s+([\w.]+)\s*;",s))
        imports.update(re.findall(r"(?m)^\s*import\s+(?:static\s+)?([\w.*]+)\s*;",s))
        types.update(re.findall(r"\b(?:class|interface|enum|record)\s+([\w$]+)",s))
        module_ann+=len(re.findall(r"@ApplicationModule\b",s))
        event_ann+=len(re.findall(r"@(?:EventListener|TransactionalEventListener|ApplicationModuleListener)\b",s))
        rest+=len(re.findall(r"@RestController\b",s))
        handlers+=len(re.findall(r"\bRequestHandler\s*<",s))
        if lizard:
            try:
                ccs.extend(fn.cyclomatic_complexity for fn in lizard.analyze_file(str(f)).function_list)
            except Exception: pass
    poms=[p for p in repo.rglob("pom.xml") if ".git" not in p.parts and "target" not in p.parts]
    modules=sum(len(re.findall(r"<module>\s*[^<]+\s*</module>",p.read_text(errors="ignore"))) for p in poms)
    return {**meta,"java_file_count":len(files),"java_loc_physical":total,"java_loc_nonblank":nonblank,
      "package_count":len(packages),"type_count":len(types),"unique_import_count":len(imports),
      "import_density_proxy":round(len(imports)/len(types),4) if types else "",
      "application_module_annotation_count":module_ann,"event_listener_annotation_count":event_ann,
      "rest_controller_count":rest,"lambda_requesthandler_count":handlers,"pom_file_count":len(poms),
      "pom_module_declaration_count":modules,"lizard_function_count":len(ccs),
      "cyclomatic_complexity_mean":round(sum(ccs)/len(ccs),4) if ccs else ""}

def write_csv(path,rows):
    if rows:
        fields=list(dict.fromkeys(k for r in rows for k in r))
        with path.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

build_rows=[]; feature_rows=[]
with MANIFEST.open(newline="",encoding="utf-8") as f: items=list(csv.DictReader(f))
for m in items:
    dest=WORK/m["repository"].replace("/","__")
    logdir=OUT/"build_logs"; logdir.mkdir(exist_ok=True)
    clone_log=logdir/(m["candidate_id"]+"_clone.log")
    if not (dest/".git").exists():
        p=run(["git","clone","--filter=blob:none",f"https://github.com/{m['repository']}.git",str(dest)],log=clone_log)
        if p.returncode:
            build_rows.append({**m,"build_status":"CLONE_FAILED","exit_code":p.returncode,"log_path":str(clone_log)})
            continue
    run(["git","fetch","origin",m["commit_sha"]],cwd=dest,log=clone_log)
    p=run(["git","checkout","--detach",m["commit_sha"]],cwd=dest,log=clone_log)
    actual=run(["git","rev-parse","HEAD"],cwd=dest).stdout.strip()
    if p.returncode or actual!=m["commit_sha"]:
        build_rows.append({**m,"build_status":"SHA_PIN_FAILED","commit_sha_actual":actual,"exit_code":p.returncode,"log_path":str(clone_log)})
        continue
    poms=[p for p in dest.rglob("pom.xml") if ".git" not in p.parts and "target" not in p.parts]
    pom=dest/"pom.xml" if (dest/"pom.xml").exists() else (poms[0] if poms else None)
    if pom is None:
        status="NO_MAVEN_POM"; code=""; log=""
    else:
        log=logdir/(m["candidate_id"]+"_maven.log")
        bp=run(["mvn","-B","-ntp","-f",str(pom),"clean","verify","-DskipTests=false"],cwd=dest,log=log)
        status="BUILD_PASS" if bp.returncode==0 else "BUILD_FAILED"; code=bp.returncode
    build_rows.append({**m,"commit_sha_actual":actual,"build_status":status,"exit_code":code,
      "timestamp_utc":datetime.now(timezone.utc).isoformat(),"log_path":str(log)})
    feature_rows.append(metrics(dest,m))

write_csv(OUT/"build_results.csv",build_rows)
write_csv(OUT/"static_features_raw.csv",feature_rows)
(OUT/"run_metadata.json").write_text(json.dumps({"timestamp_utc":datetime.now(timezone.utc).isoformat(),
 "java_version":run(["java","-version"]).stdout,"maven_version":run(["mvn","-version"]).stdout,
 "commit_pins_enforced":True,"runtime_benchmark_executed":False,
 "notes":"Static screening metrics only. Import density is not CK CBO."},indent=2),encoding="utf-8")
print(f"Completed {len(build_rows)} build records and {len(feature_rows)} static-analysis records.")
