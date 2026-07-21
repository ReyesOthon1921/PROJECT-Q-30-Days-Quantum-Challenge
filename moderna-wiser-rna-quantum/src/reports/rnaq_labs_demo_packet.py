"""RNAQ Labs 3-minute MVP demo packet generator.

This module is intentionally lightweight and safe to add late in the project.
It does not replace the full RNA-QUBO pipeline. It creates a simple guided
MVP result from one RNA sequence so a reviewer, professor, investor, or
challenge judge can understand the workflow in under three minutes.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

Pair = Tuple[int, int]
Stem = Tuple[Pair, ...]

ALLOWED_BASES = {"A", "C", "G", "U"}
WATSON_CRICK = {("A", "U"), ("U", "A"), ("C", "G"), ("G", "C")}
WOBBLE = {("G", "U"), ("U", "G")}


@dataclass(frozen=True)
class DemoResult:
    label: str
    audience: str
    sequence: str
    sequence_length: int
    gc_content: float
    candidate_pair_count: int
    candidate_stem_count: int
    qubo_variable_count: int
    qubo_conflict_edge_count: int
    graph_density: float
    connected_components: int
    max_degree: int
    hub_variable_count: int
    graph_risk_label: str
    suggested_solver_path: str
    three_minute_story: List[str]
    safe_claim: str
    next_milestone: str


def normalize_sequence(sequence: str) -> str:
    seq = "".join(sequence.upper().split()).replace("T", "U")
    if not seq:
        raise ValueError("RNA sequence is empty.")
    bad = sorted(set(seq) - ALLOWED_BASES)
    if bad:
        raise ValueError(f"Invalid RNA bases found: {bad}. Use only A, C, G, U or DNA T.")
    return seq


def gc_content(sequence: str) -> float:
    if not sequence:
        return 0.0
    return round(100.0 * sum(1 for base in sequence if base in {"G", "C"}) / len(sequence), 2)


def is_allowed_pair(left: str, right: str, allow_wobble: bool = True) -> bool:
    pair = (left, right)
    return pair in WATSON_CRICK or (allow_wobble and pair in WOBBLE)


def generate_candidate_pairs(sequence: str, min_loop_length: int = 3, allow_wobble: bool = True) -> List[Pair]:
    pairs: List[Pair] = []
    n = len(sequence)
    for i in range(n):
        for j in range(i + min_loop_length + 1, n):
            if is_allowed_pair(sequence[i], sequence[j], allow_wobble):
                pairs.append((i + 1, j + 1))  # one-indexed for reports
    return pairs


def generate_candidate_stems(pairs: Sequence[Pair], min_stem_length: int = 2) -> List[Stem]:
    pair_set = set(pairs)
    stems: List[Stem] = []
    seen = set()
    for start in pairs:
        stem: List[Pair] = []
        i, j = start
        while (i, j) in pair_set and i < j:
            stem.append((i, j))
            i += 1
            j -= 1
        if len(stem) >= min_stem_length:
            stem_tuple = tuple(stem)
            if stem_tuple not in seen:
                seen.add(stem_tuple)
                stems.append(stem_tuple)
    return stems


def stem_positions(stem: Stem) -> set[int]:
    used: set[int] = set()
    for i, j in stem:
        used.add(i)
        used.add(j)
    return used


def pair_crosses(a: Pair, b: Pair) -> bool:
    i, j = a
    k, l = b
    return (i < k < j < l) or (k < i < l < j)


def stems_conflict(a: Stem, b: Stem) -> bool:
    if stem_positions(a) & stem_positions(b):
        return True
    return any(pair_crosses(pa, pb) for pa in a for pb in b)


def build_conflict_edges(stems: Sequence[Stem]) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            if stems_conflict(stems[i], stems[j]):
                edges.append((i, j))
    return edges


def component_count(node_count: int, edges: Sequence[Tuple[int, int]]) -> int:
    if node_count == 0:
        return 0
    graph: Dict[int, List[int]] = {i: [] for i in range(node_count)}
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    seen = set()
    count = 0
    for node in range(node_count):
        if node in seen:
            continue
        count += 1
        stack = [node]
        seen.add(node)
        while stack:
            current = stack.pop()
            for nxt in graph[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return count


def graph_metrics(node_count: int, edges: Sequence[Tuple[int, int]]) -> Dict[str, float | int | str]:
    possible_edges = node_count * (node_count - 1) / 2
    density = round(len(edges) / possible_edges, 3) if possible_edges else 0.0
    degrees = [0 for _ in range(node_count)]
    for a, b in edges:
        degrees[a] += 1
        degrees[b] += 1
    max_degree = max(degrees) if degrees else 0
    hub_threshold = max(2, round(0.5 * max_degree)) if max_degree else 0
    hub_count = sum(1 for d in degrees if d >= hub_threshold and d > 0)
    components = component_count(node_count, edges)

    risk_score = (density * 45.0)
    if node_count:
        risk_score += (max_degree / max(1, node_count - 1)) * 35.0
        risk_score += (hub_count / node_count) * 20.0
    if risk_score < 25:
        label = "Low graph risk"
    elif risk_score < 60:
        label = "Medium graph risk"
    else:
        label = "High graph risk"
    return {
        "density": density,
        "max_degree": max_degree,
        "hub_count": hub_count,
        "components": components,
        "risk_score": round(risk_score, 2),
        "risk_label": label,
    }


def recommend_solver(variable_count: int, graph_density: float) -> str:
    if variable_count == 0:
        return "No valid stem-QUBO variables; adjust sequence or candidate-generation rules."
    if variable_count <= 20:
        return "Run exact validation first, then compare greedy and simulated annealing."
    if variable_count <= 80:
        return "Use simulated annealing and graph diagnostics; exact validation is only for reduced subsets."
    if graph_density > 0.35:
        return "Use sampling plus graph-aware compression caution; dense conflicts may be hard for QAOA/QRAO."
    return "Use classical sampling and quantum-readiness estimates; report qubits, depth, and graph risk."


def build_three_minute_story(audience: str) -> List[str]:
    audience = audience.lower().strip()
    if audience == "investor":
        return [
            "Problem: biological optimization workflows are slow, expensive, and hard to explain.",
            "Product: one input sequence produces validation, QUBO, graph risk, solver path, and report output.",
            "Value: the system helps prioritize experiments computationally before spending lab time.",
            "Proof: the MVP shows a working RNA-QUBO flow with graph diagnostics and safe claim boundaries.",
        ]
    if audience == "professor":
        return [
            "Research question: can RNA secondary-structure optimization be represented and audited as a QUBO workflow?",
            "Method: validate sequence, generate candidate stems, build QUBO variables, and inspect graph conflicts.",
            "Validation: exact checks are recommended for small instances before quantum-readiness claims.",
            "Limitation: this is a benchmark prototype, not proof of quantum advantage or biological deployment.",
        ]
    return [
        "Challenge goal: show a reproducible classical-to-quantum RNA optimization workflow.",
        "Input: paste an RNA sequence or choose a sample sequence.",
        "Pipeline: candidate stems become QUBO variables; conflicts become graph edges.",
        "Output: report the solver path, graph risk, validation status, and next quantum-readiness step.",
    ]


def build_demo_packet(
    sequence: str,
    audience: str = "challenge",
    label: str = "day24_demo",
    min_loop_length: int = 3,
    min_stem_length: int = 2,
    allow_wobble: bool = True,
) -> DemoResult:
    seq = normalize_sequence(sequence)
    pairs = generate_candidate_pairs(seq, min_loop_length=min_loop_length, allow_wobble=allow_wobble)
    stems = generate_candidate_stems(pairs, min_stem_length=min_stem_length)
    edges = build_conflict_edges(stems)
    metrics = graph_metrics(len(stems), edges)
    solver_path = recommend_solver(len(stems), float(metrics["density"]))
    return DemoResult(
        label=label,
        audience=audience,
        sequence=seq,
        sequence_length=len(seq),
        gc_content=gc_content(seq),
        candidate_pair_count=len(pairs),
        candidate_stem_count=len(stems),
        qubo_variable_count=len(stems),
        qubo_conflict_edge_count=len(edges),
        graph_density=float(metrics["density"]),
        connected_components=int(metrics["components"]),
        max_degree=int(metrics["max_degree"]),
        hub_variable_count=int(metrics["hub_count"]),
        graph_risk_label=str(metrics["risk_label"]),
        suggested_solver_path=solver_path,
        three_minute_story=build_three_minute_story(audience),
        safe_claim=(
            "This MVP is a computational benchmark and decision-intelligence prototype. "
            "It does not claim quantum advantage, clinical accuracy, or final biological validation."
        ),
        next_milestone=(
            "Connect this guided demo panel to the full Flask dashboard and route each metric "
            "to the existing strict classical, exact-validation, graph-diagnostic, and quantum-readiness outputs."
        ),
    )


def markdown_report(result: DemoResult) -> str:
    story = "\n".join(f"{idx}. {item}" for idx, item in enumerate(result.three_minute_story, start=1))
    return f"""# RNAQ Labs 3-Minute MVP Demo Packet

## Demo label
{result.label}

## Audience mode
{result.audience}

## Input sequence
`{result.sequence}`

## Fast results
- Sequence length: {result.sequence_length}
- GC content: {result.gc_content}%
- Candidate base pairs: {result.candidate_pair_count}
- Candidate stems: {result.candidate_stem_count}
- QUBO variables: {result.qubo_variable_count}
- QUBO conflict edges: {result.qubo_conflict_edge_count}
- Graph density: {result.graph_density}
- Connected components: {result.connected_components}
- Max degree: {result.max_degree}
- Hub variables: {result.hub_variable_count}
- Graph risk label: {result.graph_risk_label}

## Recommended solver path
{result.suggested_solver_path}

## 3-minute story
{story}

## Safe claim
{result.safe_claim}

## Next milestone
{result.next_milestone}
"""


def save_outputs(result: DemoResult, out_dir: Path) -> Dict[str, str]:
    reports_dir = out_dir / "reports"
    data_dir = out_dir / "data"
    reports_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / "rnaq_labs_3min_demo_packet.md"
    json_path = data_dir / "rnaq_labs_demo_result.json"
    report_path.write_text(markdown_report(result), encoding="utf-8")
    json_path.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    return {"report": str(report_path), "json": str(json_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate RNAQ Labs 3-minute MVP demo packet.")
    parser.add_argument("--sequence", default="GGGAAAUCC", help="RNA sequence to demo.")
    parser.add_argument("--audience", default="challenge", choices=["challenge", "investor", "professor"])
    parser.add_argument("--label", default="day24_demo")
    parser.add_argument("--out-dir", default="results", help="Output directory root.")
    args = parser.parse_args()

    result = build_demo_packet(args.sequence, audience=args.audience, label=args.label)
    paths = save_outputs(result, Path(args.out_dir))
    print("RNAQ Labs 3-minute MVP demo packet generated.")
    print(f"Report: {paths['report']}")
    print(f"JSON:   {paths['json']}")
    print(f"Graph risk: {result.graph_risk_label}")
    print(f"Solver path: {result.suggested_solver_path}")


if __name__ == "__main__":
    main()
