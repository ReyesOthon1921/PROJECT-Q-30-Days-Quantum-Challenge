from __future__ import annotations

import argparse
import csv
import json
import math
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import numpy as np
except Exception:  # pragma: no cover - fallback for minimal environments
    np = None


Edge = Tuple[int, int, float]


@dataclass(frozen=True)
class GraphDiagnostics:
    sequence_id: str
    variable_count: int
    edge_count: int
    graph_density: float
    average_degree: float
    max_degree: int
    degree_variance: float
    connected_component_count: int
    largest_component_size: int
    laplacian_lambda_2: Optional[float]
    laplacian_largest_eigenvalue: Optional[float]
    spectral_gap_available: bool
    fiedler_balance: Optional[float]
    hub_degree_ratio: float
    spectral_risk_score: float
    analysis_status: str
    interpretation: str

    def to_row(self) -> Dict[str, object]:
        return {
            "sequence_id": self.sequence_id,
            "variable_count": self.variable_count,
            "edge_count": self.edge_count,
            "graph_density": self.graph_density,
            "average_degree": self.average_degree,
            "max_degree": self.max_degree,
            "degree_variance": self.degree_variance,
            "connected_component_count": self.connected_component_count,
            "largest_component_size": self.largest_component_size,
            "laplacian_lambda_2": self.laplacian_lambda_2,
            "laplacian_largest_eigenvalue": self.laplacian_largest_eigenvalue,
            "spectral_gap_available": self.spectral_gap_available,
            "fiedler_balance": self.fiedler_balance,
            "hub_degree_ratio": self.hub_degree_ratio,
            "spectral_risk_score": self.spectral_risk_score,
            "analysis_status": self.analysis_status,
            "interpretation": self.interpretation,
        }


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: object) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        text = str(value).strip()
        if text.startswith("x_"):
            text = text[2:]
        if text.startswith("stem_"):
            text = text[5:]
        if text.startswith("var_"):
            text = text[4:]
        return int(float(text))
    except Exception:
        return None


def normalize_edges(variable_count: int, edges: Iterable[Edge]) -> List[Edge]:
    normalized: Dict[Tuple[int, int], float] = {}

    for i, j, weight in edges:
        if i == j:
            continue

        if i < 0 or j < 0:
            continue

        if i >= variable_count or j >= variable_count:
            continue

        left, right = sorted((int(i), int(j)))
        normalized[(left, right)] = normalized.get((left, right), 0.0) + float(weight)

    return [(i, j, w) for (i, j), w in sorted(normalized.items())]


def build_adjacency(variable_count: int, edges: Iterable[Edge]) -> List[List[Tuple[int, float]]]:
    adjacency: List[List[Tuple[int, float]]] = [[] for _ in range(variable_count)]

    for i, j, weight in normalize_edges(variable_count, edges):
        w = abs(float(weight)) if weight != 0 else 1.0
        adjacency[i].append((j, w))
        adjacency[j].append((i, w))

    return adjacency


def connected_components(variable_count: int, edges: Iterable[Edge]) -> List[List[int]]:
    adjacency = build_adjacency(variable_count, edges)
    seen = set()
    components: List[List[int]] = []

    for node in range(variable_count):
        if node in seen:
            continue

        queue: deque[int] = deque([node])
        seen.add(node)
        component: List[int] = []

        while queue:
            current = queue.popleft()
            component.append(current)

            for neighbor, _ in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        components.append(sorted(component))

    return components


def laplacian_matrix(variable_count: int, edges: Iterable[Edge]):
    if np is None:
        return None

    matrix = np.zeros((variable_count, variable_count), dtype=float)

    for i, j, weight in normalize_edges(variable_count, edges):
        w = abs(float(weight)) if weight != 0 else 1.0
        matrix[i, i] += w
        matrix[j, j] += w
        matrix[i, j] -= w
        matrix[j, i] -= w

    return matrix


def laplacian_spectrum(variable_count: int, edges: Iterable[Edge]) -> Tuple[Optional[List[float]], Optional[List[List[float]]]]:
    if np is None or variable_count == 0:
        return None, None

    matrix = laplacian_matrix(variable_count, edges)

    if matrix is None:
        return None, None

    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    eigenvalues_list = [float(v) for v in eigenvalues]
    eigenvectors_list = eigenvectors.tolist()

    return eigenvalues_list, eigenvectors_list


def fiedler_balance_from_eigenvectors(
    variable_count: int,
    eigenvalues: Optional[Sequence[float]],
    eigenvectors: Optional[Sequence[Sequence[float]]],
) -> Optional[float]:
    if eigenvalues is None or eigenvectors is None or variable_count < 2:
        return None

    # Column 1 is the Fiedler vector for a connected graph or the second eigenmode generally.
    try:
        fiedler = [row[1] for row in eigenvectors]
    except Exception:
        return None

    nonnegative = sum(1 for value in fiedler if value >= 0)
    negative = variable_count - nonnegative

    if variable_count == 0:
        return None

    return min(nonnegative, negative) / variable_count


def classify_graph_risk(
    density: float,
    hub_degree_ratio: float,
    component_count: int,
    lambda_2: Optional[float],
) -> Tuple[float, str]:
    risk = 0.0

    # Density raises risk because many nonzero interactions create deeper/more coupled objectives.
    risk += min(1.0, density) * 35.0

    # Hub concentration raises risk because a few stem variables can dominate constraints/penalties.
    risk += min(1.0, hub_degree_ratio) * 30.0

    # Disconnected graphs can be easier to decompose, so connectedness raises risk moderately.
    if component_count <= 1:
        risk += 15.0
    elif component_count <= 3:
        risk += 8.0

    # Small lambda_2 in a connected graph suggests weak bottlenecks; large lambda_2 suggests tight coupling.
    if lambda_2 is not None:
        if lambda_2 > 2.0:
            risk += 20.0
        elif lambda_2 > 0.5:
            risk += 12.0
        elif lambda_2 > 1e-9:
            risk += 5.0

    risk = round(min(100.0, risk), 4)

    if risk >= 70:
        label = "high_graph_structure_risk"
    elif risk >= 40:
        label = "moderate_graph_structure_risk"
    elif risk > 0:
        label = "low_graph_structure_risk"
    else:
        label = "no_interaction_edges_detected"

    return risk, label


def analyze_qubo_interaction_graph(
    sequence_id: str,
    variable_count: int,
    edges: Iterable[Edge],
) -> GraphDiagnostics:
    if variable_count < 0:
        raise ValueError("variable_count cannot be negative.")

    clean_edges = normalize_edges(variable_count, edges)
    edge_count = len(clean_edges)

    if variable_count == 0:
        return GraphDiagnostics(
            sequence_id=sequence_id,
            variable_count=0,
            edge_count=0,
            graph_density=0.0,
            average_degree=0.0,
            max_degree=0,
            degree_variance=0.0,
            connected_component_count=0,
            largest_component_size=0,
            laplacian_lambda_2=None,
            laplacian_largest_eigenvalue=None,
            spectral_gap_available=False,
            fiedler_balance=None,
            hub_degree_ratio=0.0,
            spectral_risk_score=0.0,
            analysis_status="no_variables_detected",
            interpretation="No QUBO variables were detected for this instance.",
        )

    adjacency = build_adjacency(variable_count, clean_edges)
    degrees = [len(neighbors) for neighbors in adjacency]
    average_degree = sum(degrees) / variable_count
    max_degree = max(degrees) if degrees else 0
    degree_variance = sum((degree - average_degree) ** 2 for degree in degrees) / variable_count

    possible_edges = variable_count * (variable_count - 1) / 2
    density = edge_count / possible_edges if possible_edges else 0.0

    components = connected_components(variable_count, clean_edges)
    component_count = len(components)
    largest_component_size = max((len(component) for component in components), default=0)

    eigenvalues, eigenvectors = laplacian_spectrum(variable_count, clean_edges)

    if eigenvalues is not None and len(eigenvalues) >= 2:
        lambda_2 = float(eigenvalues[1])
        lambda_max = float(eigenvalues[-1])
        spectral_gap_available = True
    elif eigenvalues is not None and len(eigenvalues) == 1:
        lambda_2 = None
        lambda_max = float(eigenvalues[0])
        spectral_gap_available = False
    else:
        lambda_2 = None
        lambda_max = None
        spectral_gap_available = False

    fiedler_balance = fiedler_balance_from_eigenvectors(variable_count, eigenvalues, eigenvectors)

    hub_degree_ratio = max_degree / max(1, variable_count - 1)

    risk_score, risk_label = classify_graph_risk(
        density=density,
        hub_degree_ratio=hub_degree_ratio,
        component_count=component_count,
        lambda_2=lambda_2,
    )

    if edge_count == 0:
        status = "no_interaction_edges_detected"
        interpretation = (
            "No quadratic QUBO interaction edges were detected. This may mean the instance is "
            "effectively linear, or that the QUBO summary file does not expose quadratic terms."
        )
    else:
        status = risk_label
        interpretation = (
            "Graph Laplacian diagnostics summarize the QUBO interaction graph. Candidate stems "
            "are variables, nonzero quadratic terms are edges, and spectral/degree metrics help "
            "explain optimization difficulty and graph-aware QRAO compression risk."
        )

    return GraphDiagnostics(
        sequence_id=sequence_id,
        variable_count=variable_count,
        edge_count=edge_count,
        graph_density=round(density, 8),
        average_degree=round(average_degree, 8),
        max_degree=max_degree,
        degree_variance=round(degree_variance, 8),
        connected_component_count=component_count,
        largest_component_size=largest_component_size,
        laplacian_lambda_2=None if lambda_2 is None else round(lambda_2, 8),
        laplacian_largest_eigenvalue=None if lambda_max is None else round(lambda_max, 8),
        spectral_gap_available=spectral_gap_available,
        fiedler_balance=None if fiedler_balance is None else round(fiedler_balance, 8),
        hub_degree_ratio=round(hub_degree_ratio, 8),
        spectral_risk_score=risk_score,
        analysis_status=status,
        interpretation=interpretation,
    )


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def infer_variable_count_from_files(run_dir: Path) -> int:
    candidate_stems = read_csv_rows(run_dir / "candidate_stems.csv")
    qubo_rows = read_csv_rows(run_dir / "qubo_summary.csv")

    if candidate_stems:
        return len(candidate_stems)

    max_index = -1
    for row in qubo_rows:
        for key, value in row.items():
            lower_key = key.lower()
            if any(token in lower_key for token in ["var", "stem", "source", "target", "i", "j"]):
                index = _safe_int(value)
                if index is not None:
                    max_index = max(max_index, index)

    return max_index + 1 if max_index >= 0 else 0


def extract_edges_from_qubo_summary(run_dir: Path, variable_count: int) -> List[Edge]:
    rows = read_csv_rows(run_dir / "qubo_summary.csv")
    edges: List[Edge] = []

    if not rows:
        return edges

    candidate_pairs = [
        ("i", "j"),
        ("var_i", "var_j"),
        ("variable_i", "variable_j"),
        ("variable_a", "variable_b"),
        ("var_a", "var_b"),
        ("stem_i", "stem_j"),
        ("stem_a", "stem_b"),
        ("source", "target"),
        ("node_i", "node_j"),
        ("left", "right"),
    ]

    for row in rows:
        lower = {key.lower(): value for key, value in row.items()}
        coefficient = (
            _safe_float(lower.get("coefficient"), default=None)
            if "coefficient" in lower
            else _safe_float(lower.get("value"), default=None)
            if "value" in lower
            else _safe_float(lower.get("weight"), default=1.0)
        )

        if coefficient is None:
            coefficient = 1.0

        term_type = str(lower.get("term_type", lower.get("type", ""))).lower()
        if term_type and any(token in term_type for token in ["linear", "diagonal", "constant"]):
            continue

        found = False
        for left_key, right_key in candidate_pairs:
            if left_key in lower and right_key in lower:
                i = _safe_int(lower[left_key])
                j = _safe_int(lower[right_key])
                if i is not None and j is not None and i != j:
                    edges.append((i, j, coefficient))
                    found = True
                    break

        if found:
            continue

        # Fallback: parse terms like x_3*x_7, stem_1:stem_4, or (2,5)
        term = str(lower.get("term", lower.get("qubo_term", lower.get("name", ""))))
        if term:
            import re

            numbers = [int(match) for match in re.findall(r"(?:x_|var_|stem_)?(\d+)", term)]
            if len(numbers) >= 2:
                i, j = numbers[0], numbers[1]
                if i != j:
                    edges.append((i, j, coefficient))

    return normalize_edges(variable_count, edges)


def analyze_run_directory(run_dir: Path) -> GraphDiagnostics:
    sequence_id = run_dir.name
    variable_count = infer_variable_count_from_files(run_dir)
    edges = extract_edges_from_qubo_summary(run_dir, variable_count)

    return analyze_qubo_interaction_graph(
        sequence_id=sequence_id,
        variable_count=variable_count,
        edges=edges,
    )


def discover_run_directories(batch_dir: Path) -> List[Path]:
    if not batch_dir.exists():
        return []

    return sorted(
        path for path in batch_dir.iterdir()
        if path.is_dir() and (path / "qubo_summary.csv").exists()
    )


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def build_diagnostics_markdown(rows: Sequence[Mapping[str, object]]) -> str:
    lines = [
        "# Graph Laplacian Diagnostics for RNA-QUBO Interaction Graphs",
        "",
        "## Purpose",
        "",
        "This document connects the updated mathematical discussion and Graph Laplacian notes to the implemented RNA-QUBO project.",
        "",
        "Candidate stems are treated as QUBO variables. Nonzero quadratic QUBO interactions are treated as graph edges. The Graph Laplacian provides a diagnostic layer for optimization difficulty, hub variables, spectral structure, and graph-aware QRAO compression risk.",
        "",
        "This layer is an interpretability and readiness tool. It does not claim improved biological accuracy, quantum advantage, or validated compression improvement.",
        "",
        "## Metrics",
        "",
        "- `variable_count`: number of QUBO variables detected for the run.",
        "- `edge_count`: number of nonzero quadratic interaction edges detected.",
        "- `graph_density`: interaction density of the QUBO graph.",
        "- `max_degree`: largest number of conflicts/interactions connected to one variable.",
        "- `degree_variance`: hub concentration signal.",
        "- `laplacian_lambda_2`: second-smallest Laplacian eigenvalue when available.",
        "- `fiedler_balance`: balance of the Fiedler split when available.",
        "- `spectral_risk_score`: project-specific diagnostic score for graph-structure difficulty.",
        "",
        "## Output Table",
        "",
    ]

    if not rows:
        lines.append("No diagnostics rows were generated.")
    else:
        header = ["sequence_id", "variable_count", "edge_count", "graph_density", "max_degree", "laplacian_lambda_2", "spectral_risk_score", "analysis_status"]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for row in rows:
            lines.append("| " + " | ".join(str(row.get(key, "")) for key in header) + " |")

    lines.extend(
        [
            "",
            "## Safe Claim Boundary",
            "",
            "- This is a graph-diagnostic layer, not a new RNA thermodynamic model.",
            "- QUBO graph structure can explain optimization and compression risk, but it does not prove quantum advantage.",
            "- Graph-aware QRAO packing should be evaluated with rounding, feasibility, and solution-quality metrics before being treated as a central claim.",
            "",
        ]
    )

    return "\n".join(lines)


def run_batch_diagnostics(
    batch_dir: Path,
    output_csv: Path,
    manifest_csv: Optional[Path] = None,
    doc_path: Optional[Path] = None,
) -> Dict[str, object]:
    run_dirs = discover_run_directories(batch_dir)
    diagnostics = [analyze_run_directory(run_dir) for run_dir in run_dirs]
    rows = [item.to_row() for item in diagnostics]

    if not rows:
        rows = [
            {
                "sequence_id": "NO_BATCH_RUNS_FOUND",
                "variable_count": 0,
                "edge_count": 0,
                "graph_density": 0.0,
                "average_degree": 0.0,
                "max_degree": 0,
                "degree_variance": 0.0,
                "connected_component_count": 0,
                "largest_component_size": 0,
                "laplacian_lambda_2": None,
                "laplacian_largest_eigenvalue": None,
                "spectral_gap_available": False,
                "fiedler_balance": None,
                "hub_degree_ratio": 0.0,
                "spectral_risk_score": 0.0,
                "analysis_status": "batch_directory_missing_or_no_runs",
                "interpretation": f"No strict-classical run folders were found under {batch_dir}.",
            }
        ]

    write_csv(output_csv, rows)

    manifest_rows = [
        {
            "artifact": "qubo_graph_laplacian_diagnostics",
            "path": str(output_csv),
            "purpose": "Graph Laplacian diagnostics over final RNA-QUBO batch outputs.",
            "status": "generated",
        }
    ]

    if doc_path is not None:
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(build_diagnostics_markdown(rows), encoding="utf-8")
        manifest_rows.append(
            {
                "artifact": "graph_laplacian_diagnostics_doc",
                "path": str(doc_path),
                "purpose": "Readable explanation tying Graph Laplacian diagnostics to the RNA-QUBO model.",
                "status": "generated",
            }
        )

    if manifest_csv is not None:
        write_csv(manifest_csv, manifest_rows)

    return {
        "batch_dir": str(batch_dir),
        "run_count": len(run_dirs),
        "output_csv": str(output_csv),
        "manifest_csv": None if manifest_csv is None else str(manifest_csv),
        "doc_path": None if doc_path is None else str(doc_path),
    }


def choose_existing_batch_dir() -> Path:
    candidates = [
        Path("results/classical_foundation_batch/a_plus_12_sequence_check"),
        Path("results/classical_foundation_batch/final_submission_12_sequence_check"),
        Path("results/classical_foundation_batch/professor_12_sequence_check"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Graph Laplacian diagnostics for RNA-QUBO batch outputs.")
    parser.add_argument("--batch-dir", default=None, help="Strict classical batch output directory.")
    parser.add_argument("--output-csv", default="results/final_submission/qubo_graph_laplacian_diagnostics.csv")
    parser.add_argument("--manifest-csv", default="results/final_submission/graph_laplacian_evidence_manifest.csv")
    parser.add_argument("--write-doc", default="docs/graph_laplacian_diagnostics.md")

    args = parser.parse_args()

    batch_dir = Path(args.batch_dir) if args.batch_dir else choose_existing_batch_dir()

    result = run_batch_diagnostics(
        batch_dir=batch_dir,
        output_csv=Path(args.output_csv),
        manifest_csv=Path(args.manifest_csv),
        doc_path=Path(args.write_doc),
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
