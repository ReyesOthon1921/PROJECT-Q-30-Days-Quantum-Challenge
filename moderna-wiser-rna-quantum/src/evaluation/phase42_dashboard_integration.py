from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

APP_PATH = ROOT / "app.py"
HTML_PATH = ROOT / "templates" / "index.html"
JS_PATH = ROOT / "static" / "js" / "app.js"
CSS_PATH = ROOT / "static" / "css" / "style.css"
DOC_PATH = ROOT / "docs" / "phase42_dashboard_integration.md"
MODULE_PATH = ROOT / "src" / "evaluation" / "exact_validation_dashboard.py"

APP_MARKER = "# PHASE42_EXACT_VALIDATION_DASHBOARD_ROUTE"
HTML_MARKER = "<!-- PHASE42_EXACT_VALIDATION_PANEL -->"
JS_MARKER = "// PHASE42_EXACT_VALIDATION_DASHBOARD_JS"
CSS_MARKER = "/* PHASE42_EXACT_VALIDATION_DASHBOARD_CSS */"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_exact_validation_dashboard_module() -> None:
    code = r'''from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "results" / "publication_tables"

EXACT_RESULTS_TABLE = TABLE_DIR / "exact_validation_results.csv"
ENERGY_AUDIT_SUMMARY_TABLE = TABLE_DIR / "qubo_energy_audit_summary.csv"
ISING_COEFFICIENTS_TABLE = TABLE_DIR / "qubo_to_ising_coefficients.csv"
FINAL_EXACT_BENCHMARK_TABLE = TABLE_DIR / "final_publication_benchmark_with_exact_validation.csv"
INTEGRATED_SUMMARY_TABLE = TABLE_DIR / "exact_validation_integrated_summary.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def safe_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def safe_int(value: Any) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(value))
    except ValueError:
        return None


def first_rows(rows: List[Dict[str, str]], limit: int = 8) -> List[Dict[str, str]]:
    return rows[:limit]


def exact_validation_summary(exact_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    if not exact_rows:
        return {
            "sequence_count": 0,
            "enumerated_count": 0,
            "feasible_count": 0,
            "total_assignments": 0,
            "minimum_energy_best": None,
            "minimum_energy_worst": None,
            "average_variable_count": None,
        }

    enumerated_count = 0
    feasible_count = 0
    total_assignments = 0
    energies: List[float] = []
    variables: List[int] = []

    for row in exact_rows:
        if str(row.get("enumerated", "")).lower() == "true":
            enumerated_count += 1

        if str(row.get("feasible", "")).lower() == "true":
            feasible_count += 1

        assignments = safe_int(row.get("assignment_count"))
        if assignments is not None:
            total_assignments += assignments

        energy = safe_float(row.get("exact_minimum_energy"))
        if energy is not None:
            energies.append(energy)

        variable_count = safe_int(row.get("variable_count"))
        if variable_count is not None:
            variables.append(variable_count)

    return {
        "sequence_count": len(exact_rows),
        "enumerated_count": enumerated_count,
        "feasible_count": feasible_count,
        "total_assignments": total_assignments,
        "minimum_energy_best": min(energies) if energies else None,
        "minimum_energy_worst": max(energies) if energies else None,
        "average_variable_count": round(sum(variables) / len(variables), 3) if variables else None,
    }


def energy_summary(energy_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    totals: List[float] = []
    linear_values: List[float] = []
    overlap_values: List[float] = []
    crossing_values: List[float] = []

    for row in energy_rows:
        total = safe_float(row.get("total_energy"))
        linear = safe_float(row.get("linear_energy"))
        overlap = safe_float(row.get("overlap_penalty_energy"))
        crossing = safe_float(row.get("crossing_penalty_energy"))

        if total is not None:
            totals.append(total)
        if linear is not None:
            linear_values.append(linear)
        if overlap is not None:
            overlap_values.append(overlap)
        if crossing is not None:
            crossing_values.append(crossing)

    return {
        "audited_sequence_count": len(energy_rows),
        "best_total_energy": min(totals) if totals else None,
        "worst_total_energy": max(totals) if totals else None,
        "total_linear_energy": round(sum(linear_values), 6) if linear_values else 0,
        "total_overlap_penalty": round(sum(overlap_values), 6) if overlap_values else 0,
        "total_crossing_penalty": round(sum(crossing_values), 6) if crossing_values else 0,
    }


def ising_summary(ising_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    sequence_ids = set()
    constant_count = 0
    h_count = 0
    j_count = 0
    values: List[float] = []

    for row in ising_rows:
        sequence_id = row.get("sequence_id", "")
        if sequence_id:
            sequence_ids.add(sequence_id)

        coefficient_type = row.get("coefficient_type", "")

        if coefficient_type == "constant_offset":
            constant_count += 1
        elif coefficient_type == "linear_field":
            h_count += 1
        elif coefficient_type == "coupling":
            j_count += 1

        value = safe_float(row.get("value"))
        if value is not None:
            values.append(value)

    return {
        "sequence_count": len(sequence_ids),
        "constant_offset_count": constant_count,
        "linear_field_count": h_count,
        "coupling_count": j_count,
        "min_coefficient_value": min(values) if values else None,
        "max_coefficient_value": max(values) if values else None,
    }


def benchmark_summary(benchmark_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    exact_available = 0
    exact_control = 0

    for row in benchmark_rows:
        if str(row.get("phase41_exact_ground_truth_available", "")).lower() == "true":
            exact_available += 1

        if row.get("phase41_row_type") == "exact_validation_control_row":
            exact_control += 1

    return {
        "integrated_benchmark_rows": len(benchmark_rows),
        "rows_with_exact_ground_truth": exact_available,
        "exact_validation_control_rows": exact_control,
    }


def file_status() -> Dict[str, Any]:
    files = {
        "exact_validation_results": EXACT_RESULTS_TABLE,
        "qubo_energy_audit_summary": ENERGY_AUDIT_SUMMARY_TABLE,
        "qubo_to_ising_coefficients": ISING_COEFFICIENTS_TABLE,
        "final_benchmark_with_exact_validation": FINAL_EXACT_BENCHMARK_TABLE,
        "exact_validation_integrated_summary": INTEGRATED_SUMMARY_TABLE,
    }

    return {
        name: {
            "exists": path.exists(),
            "path": str(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        for name, path in files.items()
    }


def run_exact_validation_dashboard() -> Dict[str, Any]:
    exact_rows = read_csv(EXACT_RESULTS_TABLE)
    energy_rows = read_csv(ENERGY_AUDIT_SUMMARY_TABLE)
    ising_rows = read_csv(ISING_COEFFICIENTS_TABLE)
    benchmark_rows = read_csv(FINAL_EXACT_BENCHMARK_TABLE)
    integrated_summary_rows = read_csv(INTEGRATED_SUMMARY_TABLE)

    return {
        "success": True,
        "title": "Phase 42 Exact Validation Dashboard",
        "summary": {
            "exact_validation": exact_validation_summary(exact_rows),
            "energy_audit": energy_summary(energy_rows),
            "ising_mapping": ising_summary(ising_rows),
            "integrated_benchmark": benchmark_summary(benchmark_rows),
        },
        "tables": {
            "exact_validation_results": first_rows(exact_rows),
            "energy_audit_summary": first_rows(energy_rows),
            "ising_coefficients": first_rows(ising_rows),
            "final_benchmark_with_exact_validation": first_rows(benchmark_rows),
            "exact_validation_integrated_summary": first_rows(integrated_summary_rows),
        },
        "file_status": file_status(),
        "interpretation": [
            "Exact validation gives small-instance ground truth for the RNA Stem-QUBO model.",
            "Energy audit separates linear reward, overlap penalty, crossing penalty, and total QUBO energy.",
            "QUBO-to-Ising coefficients support QAOA/VQE cost-Hamiltonian interpretation.",
            "This supports auditability, but it does not claim quantum advantage or final biological validation.",
        ],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_exact_validation_dashboard(), indent=2))
'''
    write_text(MODULE_PATH, code)


def patch_app_py() -> None:
    app_text = read_text(APP_PATH)

    if APP_MARKER in app_text:
        return

    route_block = f'''

{APP_MARKER}
@app.route("/api/exact-validation-dashboard", methods=["GET"])
def exact_validation_dashboard_api():
    from flask import jsonify
    from src.evaluation.exact_validation_dashboard import run_exact_validation_dashboard

    try:
        result = run_exact_validation_dashboard()
        return jsonify(result)
    except Exception as error:
        return jsonify({{"success": False, "error": str(error)}}), 500

'''

    if 'if __name__ == "__main__":' in app_text:
        app_text = app_text.replace('if __name__ == "__main__":', route_block + '\nif __name__ == "__main__":')
    else:
        app_text = app_text.rstrip() + route_block

    write_text(APP_PATH, app_text)


def patch_html() -> None:
    html = read_text(HTML_PATH)

    if HTML_MARKER in html:
        return

    panel = f'''
{HTML_MARKER}
<section id="exact-validation-panel" class="card phase42-exact-validation-card">
    <div class="card-header">
        <div>
            <p class="eyebrow">Phase 42</p>
            <h3>Exact Validation Dashboard</h3>
        </div>
        <span class="status-pill hot">Exact Ground Truth</span>
    </div>

    <p class="helper-text">
        This section displays the Phase 40/41 exact-validation layer, including exact minimum energy,
        feasibility, decoded dot-bracket structure, QUBO-to-Ising summaries, energy audit summaries,
        and the final benchmark with exact validation.
    </p>

    <div class="action-row">
        <button type="button" onclick="loadExactValidationDashboard()">Load Exact Validation Results</button>
    </div>

    <div id="exactValidationStatus" class="phase42-status">
        Exact-validation dashboard has not been loaded yet.
    </div>

    <div id="exactValidationMetrics" class="phase42-metric-grid"></div>

    <h4>Exact Validation Results</h4>
    <div id="exactValidationResultsTable" class="phase42-table-wrap"></div>

    <h4>Energy Audit Summary</h4>
    <div id="exactValidationEnergyTable" class="phase42-table-wrap"></div>

    <h4>QUBO-to-Ising Coefficients</h4>
    <div id="exactValidationIsingTable" class="phase42-table-wrap"></div>

    <h4>Final Benchmark With Exact Validation</h4>
    <div id="exactValidationBenchmarkTable" class="phase42-table-wrap"></div>

    <p class="helper-text">
        Safe interpretation: this validates small QUBO instances and strengthens benchmark auditability.
        It does not claim quantum advantage, clinical accuracy, or final biological validation.
    </p>
</section>
'''

    if '<section id="results-panel"' in html:
        html = html.replace('<section id="results-panel"', panel + '\n<section id="results-panel"', 1)
    elif "</main>" in html:
        html = html.replace("</main>", panel + "\n</main>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", panel + "\n</body>", 1)
    else:
        html = html.rstrip() + "\n" + panel

    write_text(HTML_PATH, html)


def patch_js() -> None:
    js = read_text(JS_PATH)

    if JS_MARKER in js:
        return

    block = r'''
// PHASE42_EXACT_VALIDATION_DASHBOARD_JS

function phase42EscapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function phase42SetText(id, text) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = text;
    }
}

function phase42MetricCard(label, value) {
    return `
        <div class="phase42-metric-card">
            <span>${phase42EscapeHtml(label)}</span>
            <strong>${phase42EscapeHtml(value)}</strong>
        </div>
    `;
}

function phase42RenderMetrics(summary) {
    const target = document.getElementById("exactValidationMetrics");

    if (!target) {
        return;
    }

    const exact = summary.exact_validation || {};
    const energy = summary.energy_audit || {};
    const ising = summary.ising_mapping || {};
    const benchmark = summary.integrated_benchmark || {};

    const cards = [
        phase42MetricCard("Exact sequences", exact.sequence_count ?? ""),
        phase42MetricCard("Enumerated", exact.enumerated_count ?? ""),
        phase42MetricCard("Feasible optima", exact.feasible_count ?? ""),
        phase42MetricCard("Assignments checked", exact.total_assignments ?? ""),
        phase42MetricCard("Best exact energy", exact.minimum_energy_best ?? ""),
        phase42MetricCard("Audited sequences", energy.audited_sequence_count ?? ""),
        phase42MetricCard("Ising h fields", ising.linear_field_count ?? ""),
        phase42MetricCard("Ising couplings", ising.coupling_count ?? ""),
        phase42MetricCard("Benchmark rows", benchmark.integrated_benchmark_rows ?? ""),
        phase42MetricCard("Rows with exact ground truth", benchmark.rows_with_exact_ground_truth ?? "")
    ];

    target.innerHTML = cards.join("");
}

function phase42RenderTable(id, rows, columns) {
    const target = document.getElementById(id);

    if (!target) {
        return;
    }

    if (!rows || rows.length === 0) {
        target.innerHTML = `<p class="helper-text">No rows available.</p>`;
        return;
    }

    const tableHead = columns
        .map((column) => `<th>${phase42EscapeHtml(column.label)}</th>`)
        .join("");

    const tableRows = rows
        .map((row) => {
            const cells = columns
                .map((column) => `<td>${phase42EscapeHtml(row[column.key] ?? "")}</td>`)
                .join("");

            return `<tr>${cells}</tr>`;
        })
        .join("");

    target.innerHTML = `
        <table class="phase42-table">
            <thead>
                <tr>${tableHead}</tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
    `;
}

function phase42RenderExactValidationDashboard(data) {
    phase42SetText("exactValidationStatus", "Exact-validation data loaded successfully.");

    phase42RenderMetrics(data.summary || {});

    const tables = data.tables || {};

    phase42RenderTable(
        "exactValidationResultsTable",
        tables.exact_validation_results || [],
        [
            { key: "sequence_id", label: "Sequence ID" },
            { key: "length", label: "Length" },
            { key: "variable_count", label: "Variables" },
            { key: "assignment_count", label: "Assignments" },
            { key: "exact_minimum_energy", label: "Exact Min Energy" },
            { key: "best_bitstring", label: "Best Bitstring" },
            { key: "feasible", label: "Feasible" },
            { key: "dot_bracket", label: "Dot-Bracket" }
        ]
    );

    phase42RenderTable(
        "exactValidationEnergyTable",
        tables.energy_audit_summary || [],
        [
            { key: "sequence_id", label: "Sequence ID" },
            { key: "linear_energy", label: "Linear" },
            { key: "overlap_penalty_energy", label: "Overlap" },
            { key: "crossing_penalty_energy", label: "Crossing" },
            { key: "interaction_energy", label: "Interaction" },
            { key: "total_energy", label: "Total" },
            { key: "feasible", label: "Feasible" }
        ]
    );

    phase42RenderTable(
        "exactValidationIsingTable",
        tables.ising_coefficients || [],
        [
            { key: "sequence_id", label: "Sequence ID" },
            { key: "coefficient_type", label: "Type" },
            { key: "term", label: "Term" },
            { key: "value", label: "Value" },
            { key: "mapping_note", label: "Mapping Note" }
        ]
    );

    phase42RenderTable(
        "exactValidationBenchmarkTable",
        tables.final_benchmark_with_exact_validation || [],
        [
            { key: "phase41_row_type", label: "Row Type" },
            { key: "sequence_id", label: "Sequence ID" },
            { key: "sequence", label: "Sequence" },
            { key: "phase41_exact_minimum_energy", label: "Exact Energy" },
            { key: "phase41_exact_feasible", label: "Feasible" },
            { key: "phase41_best_bitstring", label: "Best Bitstring" },
            { key: "phase41_ising_coupling_count", label: "Ising Couplings" },
            { key: "phase41_validation_note", label: "Note" }
        ]
    );
}

async function loadExactValidationDashboard() {
    phase42SetText("exactValidationStatus", "Loading exact-validation dashboard...");

    try {
        const response = await fetch("/api/exact-validation-dashboard");
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || "Unknown dashboard API error.");
        }

        phase42RenderExactValidationDashboard(data);
    } catch (error) {
        phase42SetText("exactValidationStatus", `Error loading exact-validation dashboard: ${error.message}`);
    }
}

window.addEventListener("load", () => {
    const target = document.getElementById("exact-validation-panel");

    if (target) {
        loadExactValidationDashboard();
    }
});
'''
    js = js.rstrip() + "\n\n" + block + "\n"
    write_text(JS_PATH, js)


def patch_css() -> None:
    css = read_text(CSS_PATH)

    if CSS_MARKER in css:
        return

    block = r'''
/* PHASE42_EXACT_VALIDATION_DASHBOARD_CSS */

.phase42-exact-validation-card {
    border: 1px solid rgba(90, 120, 255, 0.25);
}

.phase42-status {
    margin: 1rem 0;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    background: rgba(90, 120, 255, 0.08);
    font-weight: 600;
}

.phase42-metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.75rem;
    margin: 1rem 0 1.5rem;
}

.phase42-metric-card {
    padding: 0.9rem;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.phase42-metric-card span {
    display: block;
    font-size: 0.8rem;
    opacity: 0.75;
    margin-bottom: 0.35rem;
}

.phase42-metric-card strong {
    display: block;
    font-size: 1.15rem;
}

.phase42-table-wrap {
    width: 100%;
    overflow-x: auto;
    margin: 0.75rem 0 1.5rem;
}

.phase42-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}

.phase42-table th,
.phase42-table td {
    padding: 0.6rem 0.7rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    text-align: left;
    vertical-align: top;
}

.phase42-table th {
    font-weight: 700;
    background: rgba(90, 120, 255, 0.12);
}
'''
    css = css.rstrip() + "\n\n" + block + "\n"
    write_text(CSS_PATH, css)


def write_phase42_doc() -> None:
    content = """# Phase 42 — Dashboard Integration for Exact Validation Results

## Purpose

Phase 42 connects the Phase 40/41 exact-validation outputs to the live Flask dashboard.

## What This Adds

The dashboard can now display:

- exact minimum energy
- feasibility
- best bitstring
- decoded dot-bracket structure
- QUBO-to-Ising summary
- energy audit summary
- final benchmark with exact validation

## New Backend Module

`src/evaluation/exact_validation_dashboard.py`

This module reads the generated CSV files and prepares dashboard-ready summaries.

## New API Route

`/api/exact-validation-dashboard`

This route returns exact-validation, energy-audit, QUBO-to-Ising, and final benchmark data as JSON.

## Updated Frontend Files

- `templates/index.html`
- `static/js/app.js`
- `static/css/style.css`

## Research Meaning

The dashboard now makes the mathematical validation layer visible instead of leaving it only in CSV tables.

This strengthens the research workflow because exact small-instance ground truth can be reviewed from the live web app.

## Safe Interpretation

This phase improves auditability and visibility.

It does not claim quantum advantage, clinical accuracy, or final biological validation.
"""
    write_text(DOC_PATH, content)


def main() -> None:
    create_exact_validation_dashboard_module()
    patch_app_py()
    patch_html()
    patch_js()
    patch_css()
    write_phase42_doc()

    print("Phase 42 dashboard integration patch complete.")
    print(f"Created module: {MODULE_PATH}")
    print(f"Patched app: {APP_PATH}")
    print(f"Patched HTML: {HTML_PATH}")
    print(f"Patched JS: {JS_PATH}")
    print(f"Patched CSS: {CSS_PATH}")
    print(f"Created doc: {DOC_PATH}")


if __name__ == "__main__":
    main()