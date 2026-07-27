from __future__ import annotations
import argparse, hashlib, json, sys, zipfile
from pathlib import Path
from research_translation import build_evidence_zip, benchmark, deterministic_twin, load_registry, model_evaluation, publication_scaffold

def run(repo_root: Path):
    errors=[]; registry=load_registry(); sources=registry["sources"]
    ids=[s["id"] for s in sources]; identifiers=[s["identifier"].lower() for s in sources]
    if ids != [f"QRS-{n:03d}" for n in range(17,23)]: errors.append("QRS-017 through QRS-022 are required")
    if len(identifiers)!=len(set(identifiers)): errors.append("duplicate identifier")
    existing=json.loads((repo_root/"agroq-lab/quantum_research_sources.json").read_text(encoding="utf-8"))
    all_ids=[s["id"] for s in existing]; all_identifiers=[s["identifier"].lower() for s in existing]
    if len(all_ids)!=len(set(all_ids)): errors.append("duplicate QRS id in complete registry")
    if len(all_identifiers)!=len(set(all_identifiers)): errors.append("duplicate identifier in complete registry")
    if not set(ids).issubset(all_ids): errors.append("QRS-017 onward missing from complete registry")
    required={"mechanism","agroqFeature","reproductionTarget","evidenceStatus","limitations","requiredClassicalBaseline","hardwareFieldRestrictions","sequence"}
    for s in sources:
        if not required.issubset(s): errors.append(f"{s.get('id')} missing required metadata")
    if not deterministic_twin()["synthetic"] or deterministic_twin()["real_time"]: errors.append("digital twin boundary")
    if model_evaluation()["automatic_field_instruction"]: errors.append("automatic field instruction enabled")
    if benchmark()["uav_operation"] or benchmark()["sensor_installation"]: errors.append("physical operation enabled")
    if publication_scaffold()["paper_submitted"] or publication_scaffold()["authorship_automatic"]: errors.append("publication boundary")
    if build_evidence_zip()!=build_evidence_zip(): errors.append("evidence ZIP is not deterministic")
    return errors

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--repo-root",default="."); args=p.parse_args()
    errors=run(Path(args.repo_root).resolve())
    if errors:
        print("Q26-Q30 preflight passed: False"); [print(" - "+e) for e in errors]; sys.exit(1)
    print("Q26-Q30 preflight passed: True")
