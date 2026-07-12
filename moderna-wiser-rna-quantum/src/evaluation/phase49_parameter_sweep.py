"""Calibration-only parameter sweep for Phase 49.

The script screens a small QUBO-penalty grid on the calibration split, confirms
the top configurations with the normal solver settings, and writes a locked
strict configuration for the untouched validation split.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evaluation.phase49_benchmark import (
    _load_yaml,
    _resolve_repo_path,
    _write_csv,
    _write_json,
    _write_yaml,
    load_benchmark_config,
    run_benchmark,
)


def _safe_id(raw: str | None) -> str:
    candidate = raw or datetime.now(timezone.utc).strftime("calibration_%Y%m%dT%H%M%SZ")
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", candidate).strip("._")
    if not cleaned:
        raise ValueError("run-id must contain a letter or number")
    return cleaned


def _parameter_combinations(grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    if not grid:
        raise ValueError("parameter_grid cannot be empty")
    keys = list(grid)
    values = []
    for key in keys:
        choices = grid[key]
        if not isinstance(choices, list) or not choices:
            raise ValueError(f"parameter_grid.{key} must be a non-empty list")
        values.append(choices)
    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


def _rank_tuple(record: dict[str, Any]) -> tuple[float, ...]:
    summary = record["summary"]
    nontrivial = summary.get("macro_f1_nontrivial_reference")
    if nontrivial is None:
        nontrivial = summary.get("macro_f1_all") or 0.0
    normalized_distance = summary.get("mean_normalized_base_pair_distance")
    runtime = summary.get("median_total_runtime_seconds")
    agreement = summary.get("solver_structure_agreement_rate")
    return (
        float(summary.get("success_rate") or 0.0),
        float(nontrivial or 0.0),
        float(summary.get("micro_f1") or 0.0),
        float(summary.get("exact_match_rate") or 0.0),
        -float(normalized_distance if normalized_distance is not None else 1e9),
        float(agreement if agreement is not None else 0.0),
        -float(runtime if runtime is not None else 1e9),
    )


def _summary_row(record: dict[str, Any], rank: int | None = None) -> dict[str, Any]:
    summary = record["summary"]
    return {
        "rank": rank,
        "config_id": record["config_id"],
        "stage": record["stage"],
        "parameters": json.dumps(record["parameters"], sort_keys=True),
        "sequence_count": summary.get("sequence_count"),
        "success_rate": summary.get("success_rate"),
        "micro_f1": summary.get("micro_f1"),
        "macro_f1_all": summary.get("macro_f1_all"),
        "macro_f1_nontrivial_reference": summary.get("macro_f1_nontrivial_reference"),
        "exact_match_rate": summary.get("exact_match_rate"),
        "mean_normalized_base_pair_distance": summary.get(
            "mean_normalized_base_pair_distance"
        ),
        "solver_structure_agreement_rate": summary.get(
            "solver_structure_agreement_rate"
        ),
        "median_total_runtime_seconds": summary.get("median_total_runtime_seconds"),
        "run_dir": record.get("run_dir"),
    }


def _report(
    run_id: str,
    screen_records: list[dict[str, Any]],
    confirmation_records: list[dict[str, Any]],
    selected: dict[str, Any],
    output_dir: Path,
) -> str:
    return "\n".join(
        [
            "# Phase 49 QUBO Calibration Report",
            "",
            f"- Run ID: `{run_id}`",
            f"- Screened configurations: {len(screen_records)}",
            f"- Confirmed configurations: {len(confirmation_records)}",
            f"- Selected configuration: `{selected['config_id']}`",
            f"- Selected parameters: `{json.dumps(selected['parameters'], sort_keys=True)}`",
            f"- Output directory: `{output_dir}`",
            "",
            "## Selection rule",
            "",
            "Configurations are ranked lexicographically by successful-run rate, "
            "macro F1 on non-empty ViennaRNA references, micro F1, exact-match rate, "
            "lower normalized base-pair distance, solver structure agreement, and "
            "lower median runtime. Only calibration sequences are used.",
            "",
            "## Holdout rule",
            "",
            "The validation split must not be used to choose or revise these parameters. "
            "Run the locked `selected_strict_config.yaml` on validation only after this "
            "calibration report is saved.",
            "",
            "## Safe claim boundary",
            "",
            "This is calibration against ViennaRNA references on a synthetic starter "
            "dataset. It does not establish biological generalization or quantum advantage.",
            "",
        ]
    )


def run_parameter_sweep(
    *,
    run_id: str | None = None,
    benchmark_config_path: str | Path | None = None,
    dataset_path: str | Path | None = None,
    strict_config_path: str | Path | None = None,
    output_root: str | Path | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    config = load_benchmark_config(benchmark_config_path)
    safe_run_id = _safe_id(run_id)
    dataset = dataset_path or config["dataset_path"]
    strict_path = _resolve_repo_path(strict_config_path or config["strict_config_path"])
    root = _resolve_repo_path(output_root or config["calibration_output_root"])
    output_dir = root / safe_run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    base_strict = _load_yaml(strict_path)
    grid = config.get("parameter_grid", {})
    combinations = _parameter_combinations(grid)
    screen_overrides = dict(config.get("screen_strict_overrides", {}))
    confirmation_top_k = int(config.get("confirmation_top_k", 3))

    manifest = {
        "phase": 49,
        "run_id": safe_run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(_resolve_repo_path(dataset)),
        "strict_config": str(strict_path),
        "parameter_grid": grid,
        "screen_strict_overrides": screen_overrides,
        "confirmation_top_k": confirmation_top_k,
        "calibration_split_only": True,
    }
    _write_json(output_dir / "calibration_manifest.json", manifest)

    screen_records: list[dict[str, Any]] = []
    for index, parameters in enumerate(combinations, start=1):
        config_id = f"screen_{index:03d}"
        overrides = {**parameters, **screen_overrides}
        print(f"[SCREEN {index}/{len(combinations)}] {config_id}: {parameters}")
        result = run_benchmark(
            dataset_path=dataset,
            split="calibration",
            strict_config_path=strict_path,
            benchmark_config_path=benchmark_config_path,
            run_id=config_id,
            output_root=output_dir / "screen",
            limit=limit,
            resume=True,
            strict_overrides=overrides,
        )
        screen_records.append(
            {
                "config_id": config_id,
                "stage": "screen",
                "parameters": parameters,
                "summary": result["summary"],
                "run_dir": result["run_dir"],
            }
        )

    screen_records.sort(key=_rank_tuple, reverse=True)
    screen_rows = [_summary_row(record, rank) for rank, record in enumerate(screen_records, 1)]
    _write_csv(
        output_dir / "screen_summary.csv",
        screen_rows,
        list(screen_rows[0].keys()),
    )

    confirmation_records: list[dict[str, Any]] = []
    for index, screened in enumerate(screen_records[:confirmation_top_k], start=1):
        config_id = f"confirm_{index:03d}_{screened['config_id']}"
        print(f"[CONFIRM {index}/{min(confirmation_top_k, len(screen_records))}] {config_id}")
        result = run_benchmark(
            dataset_path=dataset,
            split="calibration",
            strict_config_path=strict_path,
            benchmark_config_path=benchmark_config_path,
            run_id=config_id,
            output_root=output_dir / "confirmation",
            limit=limit,
            resume=True,
            strict_overrides=screened["parameters"],
        )
        confirmation_records.append(
            {
                "config_id": config_id,
                "stage": "confirmation",
                "parameters": screened["parameters"],
                "summary": result["summary"],
                "run_dir": result["run_dir"],
            }
        )

    candidates = confirmation_records or screen_records
    candidates.sort(key=_rank_tuple, reverse=True)
    selected = candidates[0]

    if confirmation_records:
        confirmation_rows = [
            _summary_row(record, rank)
            for rank, record in enumerate(confirmation_records, 1)
        ]
        _write_csv(
            output_dir / "confirmation_summary.csv",
            confirmation_rows,
            list(confirmation_rows[0].keys()),
        )
    else:
        _write_csv(
            output_dir / "confirmation_summary.csv",
            [],
            [
                "rank",
                "config_id",
                "stage",
                "parameters",
                "sequence_count",
                "success_rate",
                "micro_f1",
                "macro_f1_all",
                "macro_f1_nontrivial_reference",
                "exact_match_rate",
                "mean_normalized_base_pair_distance",
                "solver_structure_agreement_rate",
                "median_total_runtime_seconds",
                "run_dir",
            ],
        )

    selected_strict = dict(base_strict)
    selected_strict.update(selected["parameters"])
    selected_strict["notes"] = (
        str(selected_strict.get("notes", "")).rstrip()
        + "\nPhase 49 parameters selected on the calibration split only."
    ).strip()
    selected_path = output_dir / "selected_strict_config.yaml"
    _write_yaml(selected_path, selected_strict)

    selection_payload = {
        "selected_config_id": selected["config_id"],
        "selected_stage": selected["stage"],
        "selected_parameters": selected["parameters"],
        "selected_summary": selected["summary"],
        "ranking_rule": [
            "success_rate",
            "macro_f1_nontrivial_reference",
            "micro_f1",
            "exact_match_rate",
            "lower_mean_normalized_base_pair_distance",
            "solver_structure_agreement_rate",
            "lower_median_total_runtime_seconds",
        ],
        "validation_has_not_been_used": True,
        "selected_strict_config": str(selected_path),
    }
    _write_json(output_dir / "selected_parameters.json", selection_payload)
    (output_dir / "calibration_report.md").write_text(
        _report(safe_run_id, screen_records, confirmation_records, selected, output_dir),
        encoding="utf-8",
    )

    return {
        "success": True,
        "run_id": safe_run_id,
        "output_dir": str(output_dir),
        "selected_strict_config": str(selected_path),
        "selection": selection_payload,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    config = load_benchmark_config(None)
    parser = argparse.ArgumentParser(description="Calibrate Phase 49 QUBO parameters.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--benchmark-config", default=None)
    parser.add_argument("--dataset", default=config["dataset_path"])
    parser.add_argument("--strict-config", default=config["strict_config_path"])
    parser.add_argument("--output-root", default=config["calibration_output_root"])
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        result = run_parameter_sweep(
            run_id=args.run_id,
            benchmark_config_path=args.benchmark_config,
            dataset_path=args.dataset,
            strict_config_path=args.strict_config,
            output_root=args.output_root,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] Calibration saved to: {result['output_dir']}")
    print(f"[OK] Locked config: {result['selected_strict_config']}")
    print(f"[OK] Selected parameters: {result['selection']['selected_parameters']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
