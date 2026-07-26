from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CRITICAL_PATHS = (
    "render.yaml",
    "agroq-lab/Dockerfile",
    "agroq-lab/app.py",
    "agroq-lab/schema.sql",
    "agroq-lab/release_preflight.py",
    "agroq-lab/release_manifest.py",
    "agroq-lab/staging_smoke.py",
    "agroq-lab/release_readiness.py",
    ".github/workflows/agroq-q16-validation.yml",
    "agroq-lab/docs/Q16_RELEASE_RUNBOOK.md",
    "agroq-lab/docs/Q16_ROLLBACK_RUNBOOK.md",
    "agroq-lab/docs/RESEARCH_MENTORS_AND_COLLABORATORS.md",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(repo_root: Path, args: list[str]) -> str | None:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def build_manifest(repo_root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    missing: list[str] = []
    for relative in CRITICAL_PATHS:
        path = repo_root / relative
        if not path.is_file():
            missing.append(relative)
            continue
        files.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    schema_path = repo_root / "agroq-lab" / "schema.sql"
    return {
        "schema_version": "AGROQ-Q16-RELEASE-MANIFEST-1.0",
        "generated_at": utc_now(),
        "repository": {
            "branch": git_value(repo_root, ["branch", "--show-current"]),
            "commit": git_value(repo_root, ["rev-parse", "HEAD"]),
            "tree": git_value(repo_root, ["write-tree"]),
            "status": git_value(repo_root, ["status", "--short"]),
        },
        "database_schema_sha256": (
            sha256_file(schema_path) if schema_path.is_file() else None
        ),
        "critical_files": files,
        "missing_files": missing,
        "ready": not missing,
        "boundaries": [
            "This manifest records repository evidence, not remote deployment success.",
            "Staging verification is recorded separately by staging_smoke.py.",
            "SQLite deployment remains limited to one application worker.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the AgroQ Q16 release manifest."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest = build_manifest(repo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Release manifest: {args.output}")
    print(f"Release manifest ready: {manifest['ready']}")
    return 0 if manifest["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
