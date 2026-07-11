function scrollToSection(id) {
    document.getElementById(id).scrollIntoView({ behavior: "smooth" });
}

function getSequence() {
    return document.getElementById("sequence").value.trim();
}

function getStructure() {
    return document.getElementById("structure").value.trim();
}

function setMetric(id, value) {
    const element = document.getElementById(id);

    if (!element) {
        return;
    }

    if (value === undefined || value === null || value === "") {
        element.textContent = "—";
    } else {
        element.textContent = value;
    }
}

function findSolverRow(comparisonRows, keyword) {
    if (!comparisonRows) {
        return null;
    }

    return comparisonRows.find((row) =>
        row.solver && row.solver.toLowerCase().includes(keyword)
    );
}

function updateSummaryCards(data) {
    const mfe =
        data?.mfe_energy ??
        data?.comparison?.vienna_mfe_energy ??
        data?.evaluation?.vienna_mfe_energy ??
        null;

    const quboVariables =
        data?.qubo?.num_variables ??
        data?.qubo?.estimated_qubits ??
        data?.result?.total_qubo_variables ??
        data?.summary?.estimated_binary_variables ??
        data?.summary?.candidate_stem_count ??
        null;

    const estimatedQubits =
    	 data?.qubo?.estimated_qubits ??
    	 data?.result?.total_qubo_variables ??
   	 data?.summary?.estimated_qubits ??
   	 data?.qaoa_readiness?.problem?.estimated_qaoa_qubits ??
   	 data?.vqe_readiness?.problem?.estimated_vqe_qubits ??
   	 null;

    const greedyF1 =
        data?.evaluation?.metrics?.f1_score ??
        data?.comparison?.greedy_evaluation?.metrics?.f1_score ??
        findSolverRow(data?.comparison?.comparison_rows, "greedy")?.f1_score ??
        null;

    const annealingF1 =
        data?.comparison?.annealing_evaluation?.metrics?.f1_score ??
        findSolverRow(data?.comparison?.comparison_rows, "annealing")?.f1_score ??
        null;

    const bestSolver =
        data?.comparison?.best_solver_by_f1?.solver ??
        null;

    if (mfe !== null) {
        setMetric("metric-mfe", Number(mfe).toFixed(3));
    }

    if (quboVariables !== null) {
        setMetric("metric-variables", quboVariables);
    }

    if (estimatedQubits !== null) {
        setMetric("metric-qubits", estimatedQubits);
    }

    if (greedyF1 !== null) {
        setMetric("metric-greedy-f1", greedyF1);
    }

    if (annealingF1 !== null) {
        setMetric("metric-annealing-f1", annealingF1);
    }

    if (bestSolver !== null) {
        setMetric("metric-best-solver", bestSolver.replace(" stem-QUBO baseline", ""));
    }
}

function showResults(data) {
    const resultsBox = document.getElementById("results");
    resultsBox.textContent = JSON.stringify(data, null, 2);

    const rawJsonWrapper = document.querySelector(".raw-json-wrapper");
    if (rawJsonWrapper) {
        rawJsonWrapper.removeAttribute("open");
    }

    updateSummaryCards(data);
    renderFromResponse(data);
    renderGraphImages(data);
    renderProfessionalResults(data);
    renderBioinformaticsMetrics(data);
    renderDataVisuals(data);
    renderAlgorithmGraphImages(data);
    renderQuantumBenchmark(data);
    renderQuantumBenchmarkGraphs(data);
    renderQaoaCircuitResults(data);
    renderVqeCircuitResults(data);
    renderCircuitComparison(data);
    renderCircuitComparisonGraphs(data);
    renderQaoaParameterSweep(data);
    renderQaoaParameterSweepGraphs(data);
    renderVqeParameterSweep(data);
    renderVqeParameterSweepGraphs(data);
    renderMeasuredBitstringEnergy(data);
    renderMeasuredBitstringGraphs(data);
    renderHardwareReadiness(data);
    renderHardwareReadinessGraphs(data);
    renderQubitCompressionEstimator(data);
    renderQubitCompressionGraphs(data);
    renderQraoSubsetMapping(data);
    renderQraoMappingGraphs(data);
    updateFocusedResultSummary(data);
}


function renderGraphImages(data) {
    const container = document.getElementById("graphsContainer");

    if (!container) {
        return;
    }

    const graphs =
        data?.graphs?.generated_graphs ||
        data?.graphs?.graphs?.generated_graphs ||
        data?.generated_graphs ||
        [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${graph.title}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${graph.title}">
                </article>
            `;
        })
        .join("");
}




async function runBioinformaticsMetrics() {
    await postJson(
        "/api/bioinformatics-metrics",
        { sequence: getSequence() },
        "Running expanded bioinformatics metrics..."
    );
}

async function generateScalingGraphs() {
    const resultsBox = document.getElementById("results");
    const graphsContainer = document.getElementById("graphsContainer");

    resultsBox.textContent = "Generating scaling plots from results/scaling_results.csv...";

    if (graphsContainer) {
        graphsContainer.innerHTML = "<p class='helper-text'>Generating graphs...</p>";
    }

    try {
        const response = await fetch("/api/generate-graphs", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({})
        });

        const data = await response.json();

        resultsBox.textContent = JSON.stringify(data, null, 2);

        updateSummaryCards(data);
        renderGraphImages(data);

        const graphsPanel = document.getElementById("graphs-panel");
        if (graphsPanel) {
            graphsPanel.scrollIntoView({ behavior: "smooth" });
        }

    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;

        if (graphsContainer) {
            graphsContainer.innerHTML = "<p class='helper-text'>Graph generation failed.</p>";
        }
    }
}

async function postJson(url, payload, loadingMessage) {
    const resultsBox = document.getElementById("results");
    resultsBox.textContent = loadingMessage;

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        showResults(data);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}

async function analyzeSequence() {
    await postJson(
        "/api/validate-sequence",
        { sequence: getSequence() },
        "Analyzing RNA sequence..."
    );
}

async function runViennaBenchmark() {
    await postJson(
        "/api/run-vienna",
        { sequence: getSequence() },
        "Running ViennaRNA benchmark..."
    );
}

async function generateCandidatePairs() {
    await postJson(
        "/api/candidate-pairs",
        { sequence: getSequence() },
        "Generating candidate base-pair variables..."
    );
}

async function generateCandidateStems() {
    await postJson(
        "/api/candidate-stems",
        { sequence: getSequence() },
        "Generating candidate stem variables..."
    );
}

async function buildQubo() {
    await postJson(
        "/api/build-qubo",
        { sequence: getSequence() },
        "Building stem-based QUBO..."
    );
}

async function runGreedySolver() {
    await postJson(
        "/api/solve-greedy",
        { sequence: getSequence() },
        "Running greedy stem-QUBO solver..."
    );
}

async function runAnnealingSolver() {
    await postJson(
        "/api/solve-annealing",
        { sequence: getSequence() },
        "Running simulated annealing stem-QUBO solver..."
    );
}

async function evaluateGreedy() {
    await postJson(
        "/api/evaluate-greedy",
        { sequence: getSequence() },
        "Evaluating greedy solver against ViennaRNA..."
    );
}

async function compareSolvers() {
    await postJson(
        "/api/compare-solvers",
        { sequence: getSequence() },
        "Comparing solvers against ViennaRNA..."
    );
}

async function runScalingAnalysis() {
    await postJson(
        "/api/run-scaling",
        {},
        "Running scaling analysis..."
    );
}

async function validateStructure() {
    await postJson(
        "/api/validate-structure",
        {
            sequence: getSequence(),
            structure: getStructure()
        },
        "Validating dot-bracket RNA structure..."
    );
}

async function generateAlgorithmComparisonGraphs() {
    await postJson(
        "/api/algorithm-comparison-graphs",
        { sequence: getSequence() },
        "Generating all-algorithm comparison graphs..."
    );
}



function renderQaoaParameterSweep(data) {
    const container = document.getElementById("qaoaSweepGrid");

    if (!container) {
        return;
    }

    const result = data?.qaoa_parameter_sweep;

    if (!result || !result.best_result) {
        return;
    }

    const best = result.best_result;

    const metricOrder = [
        ["Phase", result.phase],
        ["Parameter Count", result.parameter_count],
        ["Shots", result.shots],
        ["Best Gamma", best.gamma],
        ["Best Beta", best.beta],
        ["Best Top Bitstring", best.top_bitstring],
        ["Best Top Count", best.top_count],
        ["Best Top Probability", best.top_probability],
        ["Best Estimated QUBO Energy", best.top_energy],
        ["Qubits", best.num_qubits],
        ["Linear Terms", best.linear_term_count],
        ["Quadratic Terms", best.quadratic_term_count],
        ["Circuit Depth", best.circuit_depth],
        ["Transpiled Depth", best.transpiled_depth],
        ["Circuit Size", best.circuit_size],
        ["Best Runtime", `${best.runtime_seconds} s`],
        ["Total Runtime", `${result.total_runtime_seconds} s`],
    ];

    container.innerHTML = metricOrder
        .map(([label, value]) => {
            return `
                <article class="bio-metric-card">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(value)}</strong>
                </article>
            `;
        })
        .join("");
}

function renderQaoaParameterSweepGraphs(data) {
    const container = document.getElementById("qaoaSweepGraphsContainer");

    if (!container) {
        return;
    }

    const graphs = data?.qaoa_parameter_sweep?.generated_graphs || [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${escapeHtml(graph.title)}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${escapeHtml(graph.title)}">
                </article>
            `;
        })
        .join("");
}

async function runVqeParameterSweep() {
    await postJson(
        "/api/vqe-parameter-sweep",
        { sequence: getSequence() },
        "Running VQE parameter sweep..."
    );
}

async function runMeasuredBitstringEnergy() {
    await postJson(
        "/api/measured-bitstring-energy",
        { sequence: getSequence() },
        "Evaluating measured bitstring energy..."
    );
}

async function runHardwareReadinessCheck() {
    await postJson(
        "/api/hardware-readiness",
        { sequence: getSequence() },
        "Running hardware readiness check..."
    );
}


function dotBracketToPairs(structure) {
    const stack = [];
    const pairs = [];

    for (let index = 0; index < structure.length; index++) {
        const char = structure[index];

        if (char === "(") {
            stack.push(index);
        }

        if (char === ")") {
            const left = stack.pop();

            if (left !== undefined) {
                pairs.push([left, index]);
            }
        }
    }

    return pairs;
}

function findStructureInResponse(data) {
    return (
        data?.summary?.structure ||
        data?.structure ||
        data?.result?.predicted_structure ||
        data?.evaluation?.greedy_structure ||
        data?.comparison?.annealing_evaluation?.predicted_structure ||
        data?.comparison?.greedy_evaluation?.predicted_structure ||
        data?.comparison?.vienna_structure ||
        getStructure()
    );
}

function renderFromResponse(data) {
    const sequence = getSequence();
    const structure = findStructureInResponse(data);

    drawRnaSimulation(sequence, structure);
}


function renderCircuitComparison(data) {
    const container = document.getElementById("circuitComparisonGrid");

    if (!container) {
        return;
    }

    const metrics = data?.circuit_comparison?.metrics;

    if (!metrics) {
        return;
    }

    const metricOrder = [
        ["Sequence Length", metrics.sequence_length],
        ["Shots", metrics.shots],
        ["QAOA Qubits", metrics.qaoa_qubits],
        ["VQE Qubits", metrics.vqe_qubits],
        ["QAOA Circuit Depth", metrics.qaoa_circuit_depth],
        ["VQE Circuit Depth", metrics.vqe_circuit_depth],
        ["QAOA Transpiled Depth", metrics.qaoa_transpiled_depth],
        ["VQE Transpiled Depth", metrics.vqe_transpiled_depth],
        ["QAOA Circuit Size", metrics.qaoa_circuit_size],
        ["VQE Circuit Size", metrics.vqe_circuit_size],
        ["QAOA Top Bitstring", metrics.qaoa_top_bitstring],
        ["VQE Top Bitstring", metrics.vqe_top_bitstring],
        ["QAOA Top Probability", metrics.qaoa_top_probability],
        ["VQE Top Probability", metrics.vqe_top_probability],
        ["QAOA Runtime", `${metrics.qaoa_runtime_seconds} s`],
        ["VQE Runtime", `${metrics.vqe_runtime_seconds} s`],
        ["QAOA Linear Terms", metrics.qaoa_linear_terms],
        ["QAOA Quadratic Terms", metrics.qaoa_quadratic_terms],
        ["VQE Z Terms", metrics.vqe_z_terms],
        ["VQE ZZ Terms", metrics.vqe_zz_terms],
        ["VQE Exact Baseline Energy", metrics.vqe_exact_subset_baseline_energy],
    ];

    container.innerHTML = metricOrder
        .map(([label, value]) => {
            return `
                <article class="bio-metric-card">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(value)}</strong>
                </article>
            `;
        })
        .join("");
}

function renderCircuitComparisonGraphs(data) {
    const container = document.getElementById("circuitComparisonGraphsContainer");

    if (!container) {
        return;
    }

    const graphs = data?.circuit_comparison?.generated_graphs || [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${escapeHtml(graph.title)}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${escapeHtml(graph.title)}">
                </article>
            `;
        })
        .join("");
}


async function runQaoaParameterSweep() {
    await postJson(
        "/api/qaoa-parameter-sweep",
        { sequence: getSequence() },
        "Running QAOA parameter sweep..."
    );
}

function drawCurrentInput() {
    drawRnaSimulation(getSequence(), getStructure());
}

async function runVqeReadiness() {
    await postJson(
        "/api/vqe-readiness",
        { sequence: getSequence() },
        "Preparing VQE-ready Hamiltonian subset..."
    );
}

async function runQaoaReadiness() {
    await postJson(
        "/api/qaoa-readiness",
        { sequence: getSequence() },
        "Preparing QAOA-ready small QUBO subset..."
    );
}

async function generateAlgorithmComparisonGraphs() {
    await postJson(
        "/api/algorithm-comparison-graphs",
        { sequence: getSequence() },
        "Generating all-algorithm comparison graphs..."
    );
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function cleanLabel(label) {
    return String(label)
        .replaceAll("_", " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatMetric(value) {
    if (value === undefined || value === null || value === "") {
        return "—";
    }

    if (typeof value === "number") {
        return Number.isInteger(value) ? value : value.toFixed(4);
    }

    return value;
}

function detectResultTitle(data) {
    if (data?.graphs) return "Scaling Graph Generation Complete";
    if (data?.qaoa_readiness) return "QAOA Readiness Prototype";
    if (data?.vqe_readiness) return "VQE Readiness Prototype";
    if (data?.comparison) return "Solver Comparison Complete";
    if (data?.evaluation) return "Evaluation Against ViennaRNA";
    if (data?.qubo) return "Stem-Based QUBO Built";
    if (data?.result?.predicted_structure) return "Solver Prediction Complete";
    if (data?.summary?.candidate_stem_count !== undefined) return "Candidate Stems Generated";
    if (data?.summary?.candidate_pair_count !== undefined) return "Candidate Pairs Generated";
    if (data?.mfe_energy !== undefined) return "ViennaRNA Benchmark Complete";
    if (data?.summary) return "RNA Summary Complete";

    return "Dashboard Action Complete";
}

function detectResultDescription(data) {
    if (data?.graphs) {
        return "Scaling graphs were generated from the current CSV and are now available in the plot section.";
    }

    if (data?.qaoa_readiness) {
        return "A small QUBO subset was prepared for future QAOA experimentation. This is a readiness layer, not a quantum advantage claim.";
    }

    if (data?.vqe_readiness) {
        return "A small Hamiltonian-style subset was prepared for future VQE experimentation. This is a readiness layer, not a full quantum run.";
    }

    if (data?.comparison) {
        return "The available solvers were compared against the ViennaRNA benchmark using structure-level metrics.";
    }

    if (data?.evaluation) {
        return "The predicted structure was evaluated against the ViennaRNA reference using precision, recall, and F1 score.";
    }

    if (data?.qubo) {
        return "The RNA sequence was transformed into a stem-based QUBO model with binary variables and quadratic penalties.";
    }

    return "The action completed successfully. A clean summary is shown here, and the full JSON is available below.";
}

function buildMetricCards(metrics) {
    return `
        <div class="result-metric-grid">
            ${metrics.map((metric) => `
                <div class="result-metric-card">
                    <span>${escapeHtml(metric.label)}</span>
                    <strong>${escapeHtml(formatMetric(metric.value))}</strong>
                </div>
            `).join("")}
        </div>
    `;
}


async function runVqeCircuitPrototype() {
    await postJson(
        "/api/vqe-circuit",
        { sequence: getSequence() },
        "Running VQE circuit prototype on Qiskit AerSimulator..."
    );
}


function renderQubitCompressionEstimator(data) {
    const container = document.getElementById("qubitCompressionGrid");

    if (!container) {
        return;
    }

    const result = data?.qubit_compression_estimator;

    if (!result || !result.estimates) {
        return;
    }

    const metricOrder = [
        ["Phase", result.phase],
        ["Variable Count", result.variable_count],
        ["Direct Qubits", result.direct_qubits],
        ["64 Variables Log Encoding Example", result.example_64_variables_log_encoding_qubits],
        ["80 Variables Log Encoding Example", result.example_80_variables_log_encoding_qubits],
        ["Total Runtime", `${result.total_runtime_seconds} s`],
    ];

    result.estimates.forEach((estimate) => {
        metricOrder.push([`${estimate.model} Qubits`, estimate.estimated_qubits]);
        metricOrder.push([`${estimate.model} Ratio`, estimate.compression_ratio_vs_direct]);
        metricOrder.push([`${estimate.model} Risk`, estimate.risk_note]);
    });

    container.innerHTML = metricOrder
        .map(([label, value]) => {
            return `
                <article class="bio-metric-card">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(value)}</strong>
                </article>
            `;
        })
        .join("");
}

function renderQubitCompressionGraphs(data) {
    const container = document.getElementById("qubitCompressionGraphsContainer");

    if (!container) {
        return;
    }

    const graphs = data?.qubit_compression_estimator?.generated_graphs || [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${escapeHtml(graph.title)}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${escapeHtml(graph.title)}">
                </article>
            `;
        })
        .join("");
}

function renderQraoSubsetMapping(data) {
    const grid = document.getElementById("qraoMappingGrid");
    const table = document.getElementById("qraoMappingTable");

    const result = data?.qrao_subset_mapping;

    if (!result) {
        return;
    }

    if (grid) {
        const metricOrder = [
            ["Phase", result.phase],
            ["Selected Variables", result.selected_variable_count],
            ["Direct Qubits", result.direct_qubits],
            ["2-to-1 Compressed Qubits", result.two_to_one_qubits],
            ["3-to-1 Compressed Qubits", result.three_to_one_qubits],
            ["2-to-1 Compression Ratio", result.two_to_one_compression_ratio],
            ["3-to-1 Compression Ratio", result.three_to_one_compression_ratio],
            ["Total Runtime", `${result.total_runtime_seconds} s`],
        ];

        const axisCounts = result.three_to_one_axis_counts || {};

        Object.keys(axisCounts).forEach((axis) => {
            metricOrder.push([`3-to-1 ${axis} Axis Count`, axisCounts[axis]]);
        });

        grid.innerHTML = metricOrder
            .map(([label, value]) => {
                return `
                    <article class="bio-metric-card">
                        <span>${escapeHtml(label)}</span>
                        <strong>${escapeHtml(value)}</strong>
                    </article>
                `;
            })
            .join("");
    }

    if (table) {
        const rows = result.three_to_one_mapping || [];

        table.innerHTML = `
            <h4>First QRAO Variable Mappings</h4>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Variable</th>
                        <th>Compressed Qubit</th>
                        <th>Pauli Axis</th>
                        <th>Encoding</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.slice(0, 18).map((row) => {
                        return `
                            <tr>
                                <td>${escapeHtml(row.variable)}</td>
                                <td>${escapeHtml(row.compressed_qubit)}</td>
                                <td>${escapeHtml(row.pauli_axis)}</td>
                                <td>${escapeHtml(row.encoding)}</td>
                            </tr>
                        `;
                    }).join("")}
                </tbody>
            </table>
        `;
    }
}

function renderQraoMappingGraphs(data) {
    const container = document.getElementById("qraoMappingGraphsContainer");

    if (!container) {
        return;
    }

    const graphs = data?.qrao_subset_mapping?.generated_graphs || [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${escapeHtml(graph.title)}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${escapeHtml(graph.title)}">
                </article>
            `;
        })
        .join("");
}


function collectProfessionalMetrics(data) {
    const metrics = [];

    if (data?.success !== undefined) {
        metrics.push({ label: "Status", value: data.success ? "Success" : "Failed" });
    }

    if (data?.mfe_energy !== undefined) {
        metrics.push({ label: "ViennaRNA MFE", value: data.mfe_energy });
    }

    if (data?.qubo) {
        metrics.push({ label: "QUBO Variables", value: data.qubo.num_variables });
        metrics.push({ label: "Estimated Qubits", value: data.qubo.estimated_qubits });
        metrics.push({ label: "Linear Terms", value: data.qubo.num_linear_terms });
        metrics.push({ label: "Quadratic Terms", value: data.qubo.num_quadratic_terms });
    }

    if (data?.result) {
        metrics.push({ label: "Solver", value: data.result.solver });
        metrics.push({ label: "Selected Stems", value: data.result.selected_stem_count });
        metrics.push({ label: "Selected Pairs", value: data.result.selected_pair_count });
        metrics.push({ label: "Objective / Energy", value: data.result.objective_score ?? data.result.best_energy });
    }

    if (data?.evaluation?.metrics) {
        metrics.push({ label: "Precision", value: data.evaluation.metrics.precision });
        metrics.push({ label: "Recall", value: data.evaluation.metrics.recall });
        metrics.push({ label: "F1 Score", value: data.evaluation.metrics.f1_score });
    }

    if (data?.comparison) {
        metrics.push({ label: "ViennaRNA MFE", value: data.comparison.vienna_mfe_energy });
        metrics.push({ label: "Best Solver", value: data.comparison.best_solver_by_f1?.solver });
    }

    if (data?.qaoa_readiness) {
        const qaoa = data.qaoa_readiness;
        metrics.push({ label: "Phase", value: qaoa.phase });
        metrics.push({ label: "Original QUBO Variables", value: qaoa.problem?.original_qubo_variables });
        metrics.push({ label: "QAOA Qubits", value: qaoa.problem?.estimated_qaoa_qubits });
        metrics.push({ label: "Best Energy", value: qaoa.exact_subset_baseline?.best_energy });
        metrics.push({ label: "Selected Variables", value: qaoa.exact_subset_baseline?.selected_variable_count });
    }

    if (data?.vqe_readiness) {
        const vqe = data.vqe_readiness;
        metrics.push({ label: "Phase", value: vqe.phase });
        metrics.push({ label: "Original QUBO Variables", value: vqe.problem?.original_qubo_variables });
        metrics.push({ label: "VQE Qubits", value: vqe.problem?.estimated_vqe_qubits });
        metrics.push({ label: "Z Terms", value: vqe.hamiltonian?.num_z_terms });
        metrics.push({ label: "ZZ Terms", value: vqe.hamiltonian?.num_zz_terms });
        metrics.push({ label: "Best Energy", value: vqe.exact_subset_baseline?.best_energy });
    }

    if (data?.graphs) {
        metrics.push({ label: "Graphs Generated", value: data.graphs.generated_graph_count });
        metrics.push({ label: "CSV Source", value: data.graphs.csv_path });
        metrics.push({ label: "Rows Analyzed", value: data.graphs.row_count });
    }

    if (data?.summary) {
        metrics.push({ label: "Length", value: data.summary.length });
        metrics.push({ label: "GC Content", value: data.summary.gc_content_percent });
        metrics.push({ label: "Candidate Pairs", value: data.summary.candidate_pair_count });
        metrics.push({ label: "Candidate Stems", value: data.summary.candidate_stem_count });
        metrics.push({ label: "Estimated Variables", value: data.summary.estimated_binary_variables });
        metrics.push({ label: "Estimated Qubits", value: data.summary.estimated_qubits });
    }

    return metrics.filter((metric) => metric.value !== undefined && metric.value !== null);
}


function renderVqeCircuitResults(data) {
    const grid = document.getElementById("vqeCircuitGrid");
    const countsContainer = document.getElementById("vqeCountsContainer");

    const result = data?.vqe_circuit;

    if (!result) {
        return;
    }

    if (grid) {
        const metrics = [
            ["Simulator", result.simulator],
            ["Shots", result.shots],
            ["Qubits", result.num_qubits],
            ["Selected Variables", result.selected_variable_count],
            ["Z Terms", result.z_term_count],
            ["ZZ Terms", result.zz_term_count],
            ["Circuit Depth", result.circuit_depth],
            ["Transpiled Depth", result.transpiled_depth],
            ["Circuit Size", result.circuit_size],
            ["Top Bitstring", result.top_bitstring],
            ["Top Probability", result.top_probability],
            ["Exact Baseline Energy", result.exact_subset_baseline_energy],
            ["Runtime", `${result.runtime_seconds} s`],
        ];

        grid.innerHTML = metrics
            .map(([label, value]) => {
                return `
                    <article class="bio-metric-card">
                        <span>${escapeHtml(label)}</span>
                        <strong>${escapeHtml(value)}</strong>
                    </article>
                `;
            })
            .join("");
    }

    if (countsContainer) {
        const rows = result.top_10_counts || [];

        countsContainer.innerHTML = `
            <h4>Top Measurement Counts</h4>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Bitstring</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map((row) => {
                        return `
                            <tr>
                                <td>${escapeHtml(row[0])}</td>
                                <td>${escapeHtml(row[1])}</td>
                            </tr>
                        `;
                    }).join("")}
                </tbody>
            </table>
        `;
    }
}

function renderVqeParameterSweep(data) {
    const container = document.getElementById("vqeSweepGrid");

    if (!container) {
        return;
    }

    const result = data?.vqe_parameter_sweep;

    if (!result || !result.best_result) {
        return;
    }

    const best = result.best_result;

    const metricOrder = [
        ["Phase", result.phase],
        ["Parameter Count", result.parameter_count],
        ["Shots", result.shots],
        ["Best Angle Scale", best.angle_scale],
        ["Best Entanglement", best.entanglement_mode],
        ["Top Bitstring", best.top_bitstring],
        ["Top Count", best.top_count],
        ["Top Probability", best.top_probability],
        ["Qubits", best.num_qubits],
        ["Z Terms", best.z_term_count],
        ["ZZ Terms", best.zz_term_count],
        ["Circuit Depth", best.circuit_depth],
        ["Transpiled Depth", best.transpiled_depth],
        ["Circuit Size", best.circuit_size],
        ["Exact Baseline Energy", best.exact_subset_baseline_energy],
        ["Best Runtime", `${best.runtime_seconds} s`],
        ["Total Runtime", `${result.total_runtime_seconds} s`],
    ];

    container.innerHTML = metricOrder
        .map(([label, value]) => {
            return `
                <article class="bio-metric-card">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(value)}</strong>
                </article>
            `;
        })
        .join("");
}

function renderVqeParameterSweepGraphs(data) {
    const container = document.getElementById("vqeSweepGraphsContainer");

    if (!container) {
        return;
    }

    const graphs = data?.vqe_parameter_sweep?.generated_graphs || [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${escapeHtml(graph.title)}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${escapeHtml(graph.title)}">
                </article>
            `;
        })
        .join("");
}

function renderMeasuredBitstringEnergy(data) {
    const grid = document.getElementById("measuredBitstringGrid");
    const table = document.getElementById("measuredBitstringTable");

    const result = data?.measured_bitstring_energy;

    if (!result) {
        return;
    }

    const best = result.best_result || {};

    if (grid) {
        const metricOrder = [
            ["Phase", result.phase],
            ["Variable Count", result.variable_count],
            ["Best Source", best.source],
            ["Best Bitstring", best.bitstring],
            ["Best Probability", best.probability],
            ["Best QUBO Energy", best.estimated_qubo_energy],
            ["Selected Variables", best.selected_variable_count],
            ["Total Runtime", `${result.total_runtime_seconds} s`],
        ];

        grid.innerHTML = metricOrder
            .map(([label, value]) => {
                return `
                    <article class="bio-metric-card">
                        <span>${escapeHtml(label)}</span>
                        <strong>${escapeHtml(value)}</strong>
                    </article>
                `;
            })
            .join("");
    }

    if (table) {
        const rows = result.evaluated_results || [];

        table.innerHTML = `
            <h4>Evaluated Bitstrings</h4>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Source</th>
                        <th>Bitstring</th>
                        <th>Probability</th>
                        <th>Estimated QUBO Energy</th>
                        <th>Selected Variables</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map((row) => {
                        return `
                            <tr>
                                <td>${escapeHtml(row.source)}</td>
                                <td>${escapeHtml(row.bitstring)}</td>
                                <td>${escapeHtml(row.probability)}</td>
                                <td>${escapeHtml(row.estimated_qubo_energy)}</td>
                                <td>${escapeHtml(row.selected_variable_count)}</td>
                            </tr>
                        `;
                    }).join("")}
                </tbody>
            </table>
        `;
    }
}

function renderMeasuredBitstringGraphs(data) {
    const container = document.getElementById("measuredBitstringGraphsContainer");

    if (!container) {
        return;
    }

    const graphs = data?.measured_bitstring_energy?.generated_graphs || [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${escapeHtml(graph.title)}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${escapeHtml(graph.title)}">
                </article>
            `;
        })
        .join("");
}

function renderHardwareReadiness(data) {
    const container = document.getElementById("hardwareReadinessGrid");

    if (!container) {
        return;
    }

    const result = data?.hardware_readiness;

    if (!result || !result.summaries) {
        return;
    }

    const metricOrder = [
        ["Phase", result.phase],
        ["Hardware Run", result.hardware_run],
        ["Backend Used", result.backend_used],
        ["Total Runtime", `${result.total_runtime_seconds} s`],
    ];

    result.summaries.forEach((summary) => {
        metricOrder.push([`${summary.name} Qubits`, summary.num_qubits]);
        metricOrder.push([`${summary.name} Original Depth`, summary.original_depth]);
        metricOrder.push([`${summary.name} Transpiled Depth`, summary.transpiled_depth]);
        metricOrder.push([`${summary.name} Circuit Size`, summary.circuit_size]);
        metricOrder.push([`${summary.name} CX Count`, summary.cx_count]);
        metricOrder.push([`${summary.name} Readiness`, summary.readiness]);
    });

    container.innerHTML = metricOrder
        .map(([label, value]) => {
            return `
                <article class="bio-metric-card">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(value)}</strong>
                </article>
            `;
        })
        .join("");
}

function renderHardwareReadinessGraphs(data) {
    const container = document.getElementById("hardwareReadinessGraphsContainer");

    if (!container) {
        return;
    }

    const graphs = data?.hardware_readiness?.generated_graphs || [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${escapeHtml(graph.title)}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${escapeHtml(graph.title)}">
                </article>
            `;
        })
        .join("");
}


function renderQaoaCircuitResults(data) {
    const grid = document.getElementById("qaoaCircuitGrid");
    const countsContainer = document.getElementById("qaoaCountsContainer");

    const result = data?.qaoa_circuit;

    if (!result) {
        return;
    }

    if (grid) {
        const metrics = [
            ["Simulator", result.simulator],
            ["Shots", result.shots],
            ["Qubits", result.num_qubits],
            ["Linear Terms", result.linear_term_count],
            ["Quadratic Terms", result.quadratic_term_count],
            ["Circuit Depth", result.circuit_depth],
            ["Transpiled Depth", result.transpiled_depth],
            ["Circuit Size", result.circuit_size],
            ["Top Bitstring", result.top_bitstring],
            ["Top Probability", result.top_probability],
            ["Runtime", `${result.runtime_seconds} s`],
            ["Gamma", result.gamma],
            ["Beta", result.beta],
        ];

        grid.innerHTML = metrics
            .map(([label, value]) => {
                return `
                    <article class="bio-metric-card">
                        <span>${escapeHtml(label)}</span>
                        <strong>${escapeHtml(value)}</strong>
                    </article>
                `;
            })
            .join("");
    }

    if (countsContainer) {
        const rows = result.top_10_counts || [];

        countsContainer.innerHTML = `
            <h4>Top Measurement Counts</h4>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Bitstring</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map((row) => {
                        return `
                            <tr>
                                <td>${escapeHtml(row[0])}</td>
                                <td>${escapeHtml(row[1])}</td>
                            </tr>
                        `;
                    }).join("")}
                </tbody>
            </table>
        `;
    }
}



function renderComparisonTable(data) {
    const rows = data?.comparison?.comparison_rows;

    if (!rows || !rows.length) {
        return "";
    }

    return `
        <div class="result-detail-card">
            <h4>Solver Comparison</h4>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Solver</th>
                        <th>F1</th>
                        <th>Precision</th>
                        <th>Recall</th>
                        <th>Runtime</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map((row) => `
                        <tr>
                            <td>${escapeHtml(row.solver ?? "—")}</td>
                            <td>${escapeHtml(formatMetric(row.f1_score))}</td>
                            <td>${escapeHtml(formatMetric(row.precision))}</td>
                            <td>${escapeHtml(formatMetric(row.recall))}</td>
                            <td>${escapeHtml(formatMetric(row.runtime_seconds))}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
    `;
}

function renderStructureCards(data) {
    const predicted =
        data?.result?.predicted_structure ||
        data?.evaluation?.greedy_structure ||
        data?.comparison?.greedy_evaluation?.predicted_structure ||
        data?.comparison?.annealing_evaluation?.predicted_structure;

    const reference =
        data?.vienna_structure ||
        data?.evaluation?.vienna_structure ||
        data?.comparison?.vienna_structure;

    let html = "";

    if (predicted) {
        html += `
            <div class="result-detail-card">
                <h4>Predicted Structure</h4>
                <div class="structure-line">${escapeHtml(predicted)}</div>
            </div>
        `;
    }

    if (reference) {
        html += `
            <div class="result-detail-card">
                <h4>ViennaRNA Reference Structure</h4>
                <div class="structure-line">${escapeHtml(reference)}</div>
            </div>
        `;
    }

    return html;
}

async function runQubitCompressionEstimator() {
    await postJson(
        "/api/qubit-compression-estimator",
        { sequence: getSequence() },
        "Running qubit compression estimator..."
    );
}

async function runQraoSubsetMapping() {
    await postJson(
        "/api/qrao-subset-mapping",
        { sequence: getSequence() },
        "Running QRAO subset mapping..."
    );
}

function renderVariableTags(data) {
    const variables =
        data?.qaoa_readiness?.exact_subset_baseline?.selected_variables ||
        data?.vqe_readiness?.exact_subset_baseline?.selected_variables ||
        [];

    if (!variables.length) {
        return "";
    }

    return `
        <div class="result-detail-card">
            <h4>Selected Variables</h4>
            <div class="tag-list">
                ${variables.map((variable) => `<span>${escapeHtml(variable)}</span>`).join("")}
            </div>
        </div>
    `;
}

function renderAlgorithmGraphImages(data) {
    const container = document.getElementById("algorithmGraphsContainer");

    if (!container) {
        return;
    }

    const graphs =
        data?.algorithm_graphs?.generated_graphs ||
        data?.algorithm_graphs?.algorithm_graphs?.generated_graphs ||
        [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${graph.title}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${graph.title}">
                </article>
            `;
        })
        .join("");
}

function renderGraphSummary(data) {
    const graphs = data?.graphs?.generated_graphs || [];

    if (!graphs.length) {
        return "";
    }

    return `
        <div class="result-detail-card">
            <h4>Generated Graph Files</h4>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Graph</th>
                        <th>CSV Column</th>
                        <th>File</th>
                    </tr>
                </thead>
                <tbody>
                    ${graphs.map((graph) => `
                        <tr>
                            <td>${escapeHtml(graph.title)}</td>
                            <td>${escapeHtml(graph.csv_column)}</td>
                            <td>${escapeHtml(graph.filename)}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
    `;
}

function renderProfessionalResults(data) {
    const container = document.getElementById("professionalResults");

    if (!container) {
        return;
    }

    const metrics = collectProfessionalMetrics(data);

    container.innerHTML = `
        <div class="result-hero">
            <h4>${escapeHtml(detectResultTitle(data))}</h4>
            <p>${escapeHtml(detectResultDescription(data))}</p>
        </div>

        ${metrics.length ? buildMetricCards(metrics) : ""}

        ${renderComparisonTable(data)}
        ${renderStructureCards(data)}
        ${renderVariableTags(data)}
        ${renderGraphSummary(data)}
    `;
}

function collectVisualMetrics(data) {
    const metrics = [];

    function addMetric(label, value) {
        if (value !== undefined && value !== null && value !== "") {
            metrics.push({
                label: label,
                value: Number(value)
            });
        }
    }

    addMetric("QUBO vars", data?.qubo?.num_variables);
    addMetric("Qubits", data?.qubo?.estimated_qubits);

    addMetric("Pairs", data?.summary?.candidate_pair_count);
    addMetric("Stems", data?.summary?.candidate_stem_count);
    addMetric("Variables", data?.summary?.estimated_binary_variables);
    addMetric("Est. qubits", data?.summary?.estimated_qubits);

    addMetric("Selected stems", data?.result?.selected_stem_count);
    addMetric("Selected pairs", data?.result?.selected_pair_count);

    addMetric("Precision", data?.evaluation?.metrics?.precision);
    addMetric("Recall", data?.evaluation?.metrics?.recall);
    addMetric("F1", data?.evaluation?.metrics?.f1_score);

    addMetric("QAOA qubits", data?.qaoa_readiness?.problem?.estimated_qaoa_qubits);
    addMetric("QAOA energy", Math.abs(data?.qaoa_readiness?.exact_subset_baseline?.best_energy));

    addMetric("VQE qubits", data?.vqe_readiness?.problem?.estimated_vqe_qubits);
    addMetric("Z terms", data?.vqe_readiness?.hamiltonian?.num_z_terms);
    addMetric("ZZ terms", data?.vqe_readiness?.hamiltonian?.num_zz_terms);
    addMetric("VQE energy", Math.abs(data?.vqe_readiness?.exact_subset_baseline?.best_energy));

    addMetric("Graphs", data?.graphs?.generated_graph_count);
    addMetric("Rows", data?.graphs?.row_count);

    return metrics.filter((metric) => !Number.isNaN(metric.value));
}

function getVisualMode(data) {
    if (data?.qaoa_readiness) return "QAOA readiness";
    if (data?.vqe_readiness) return "VQE readiness";
    if (data?.graphs) return "Scaling graphs";
    if (data?.comparison) return "Solver comparison";
    if (data?.evaluation) return "Evaluation";
    if (data?.qubo) return "QUBO build";
    if (data?.result) return "Solver result";
    if (data?.summary) return "RNA analysis";
    return "Dashboard result";
}

function drawRoundedRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
}

function renderBioinformaticsMetrics(data) {
    const container = document.getElementById("bioinformaticsMetricsGrid");

    if (!container) {
        return;
    }

    const metrics = data?.bioinformatics_metrics?.metrics;

    if (!metrics) {
        return;
    }

    const metricOrder = [
        ["Sequence Length", metrics.sequence_length],
        ["GC %", metrics.gc_percent],
        ["Stem Count", metrics.stem_count],
        ["Loop Count", metrics.loop_count],
        ["Candidate Pairs", metrics.candidate_pairs],
        ["Candidate Stems", metrics.candidate_stems],
        ["QUBO Variables", metrics.qubo_variables],
        ["Quadratic Terms", metrics.quadratic_terms],
        ["Estimated Qubits", metrics.estimated_qubits],
        ["Circuit Depth", metrics.circuit_depth_estimate],
        ["Approximation Ratio", metrics.approximation_ratio],
        ["ViennaRNA Energy", metrics.vienna_mfe_energy],
        ["Runtime", `${metrics.runtime_seconds} s`],
        ["Memory Estimate", `${metrics.memory_estimate_mb} MB`],
        ["Greedy F1", metrics.greedy_f1],
        ["Annealing F1", metrics.annealing_f1],
        ["Greedy MCC", metrics.greedy_mcc],
        ["Annealing MCC", metrics.annealing_mcc],
        ["Sensitivity", metrics.greedy_sensitivity],
        ["Specificity", metrics.greedy_specificity],
        ["QAOA Readiness", `${metrics.qaoa_readiness_percent}%`],
        ["VQE Readiness", `${metrics.vqe_readiness_percent}%`],
        ["Best Solver", metrics.best_solver],
    ];

    container.innerHTML = metricOrder
        .map(([label, value]) => {
            return `
                <article class="bio-metric-card">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(value)}</strong>
                </article>
            `;
        })
        .join("");
}

async function runQuantumBenchmark() {
    await postJson(
        "/api/quantum-benchmark",
        { sequence: getSequence() },
        "Running quantum benchmark layer..."
    );
}

async function runCircuitComparison() {
    await postJson(
        "/api/circuit-comparison",
        { sequence: getSequence() },
        "Running QAOA vs VQE circuit comparison..."
    );
}

function renderQuantumBenchmark(data) {
    const container = document.getElementById("quantumBenchmarkGrid");

    if (!container) {
        return;
    }

    const metrics = data?.quantum_benchmark?.metrics;

    if (!metrics) {
        return;
    }

    const metricOrder = [
        ["Sequence Length", metrics.sequence_length],
        ["Full QUBO Variables", metrics.full_qubo_variables],
        ["Full Estimated Qubits", metrics.full_estimated_qubits],
        ["Full Linear Terms", metrics.full_linear_terms],
        ["Full Quadratic Terms", metrics.full_quadratic_terms],
        ["QAOA Subset Variables", metrics.qaoa_subset_variables],
        ["QAOA Subset Qubits", metrics.qaoa_subset_qubits],
        ["QAOA Quadratic Terms", metrics.qaoa_quadratic_terms],
        ["QAOA Estimated Depth", metrics.qaoa_estimated_depth],
        ["QAOA Best Energy", metrics.qaoa_best_energy],
        ["QAOA Selected Variables", metrics.qaoa_selected_variable_count],
        ["VQE Subset Variables", metrics.vqe_subset_variables],
        ["VQE Subset Qubits", metrics.vqe_subset_qubits],
        ["VQE Z Terms", metrics.vqe_z_terms],
        ["VQE ZZ Terms", metrics.vqe_zz_terms],
        ["VQE Estimated Depth", metrics.vqe_estimated_depth],
        ["VQE Best Energy", metrics.vqe_best_energy],
        ["VQE Selected Variables", metrics.vqe_selected_variable_count],
        ["QAOA/VQE Energy Ratio", metrics.qaoa_vqe_energy_ratio],
        ["Runtime", `${metrics.runtime_seconds} s`],
    ];

    container.innerHTML = metricOrder
        .map(([label, value]) => {
            return `
                <article class="bio-metric-card">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(value)}</strong>
                </article>
            `;
        })
        .join("");
}

function renderQuantumBenchmarkGraphs(data) {
    const container = document.getElementById("quantumBenchmarkGraphsContainer");

    if (!container) {
        return;
    }

    const graphs = data?.quantum_benchmark?.generated_graphs || [];

    if (!graphs.length) {
        return;
    }

    const timestamp = Date.now();

    container.innerHTML = graphs
        .map((graph) => {
            return `
                <article class="graph-card">
                    <h4>${graph.title}</h4>
                    <img src="${graph.static_path}?v=${timestamp}" alt="${graph.title}">
                </article>
            `;
        })
        .join("");
}

function drawResult3dSimulation(data) {
    const canvas = document.getElementById("result3dCanvas");

    if (!canvas) {
        return;
    }

    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const background = ctx.createLinearGradient(0, 0, width, height);
    background.addColorStop(0, "#000000");
    background.addColorStop(0.35, "#2A0048");
    background.addColorStop(0.7, "#800080");
    background.addColorStop(1, "#D50048");

    ctx.fillStyle = background;
    ctx.fillRect(0, 0, width, height);

    const mode = getVisualMode(data);
    const metrics = collectVisualMetrics(data);

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 30px Arial";
    ctx.fillText("QUBO / Quantum Readiness State", 34, 48);

    ctx.font = "16px Arial";
    ctx.fillStyle = "rgba(255,255,255,0.82)";
    ctx.fillText(`Current mode: ${mode}`, 34, 78);

    const centerX = width * 0.52;
    const centerY = height * 0.55;

    const nodeCount = Math.min(Math.max(metrics.length, 8), 18);
    const radiusX = 300;
    const radiusY = 105;

    for (let ring = 0; ring < 3; ring++) {
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX - ring * 55, radiusY - ring * 18, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 180, 220, ${0.12 + ring * 0.08})`;
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    const nodePositions = [];

    for (let i = 0; i < nodeCount; i++) {
        const angle = (Math.PI * 2 * i) / nodeCount;
        const depth = (Math.sin(angle) + 1) / 2;
        const x = centerX + Math.cos(angle) * radiusX;
        const y = centerY + Math.sin(angle) * radiusY;
        const size = 12 + depth * 12;

        nodePositions.push({ x, y, size, depth, metric: metrics[i % Math.max(metrics.length, 1)] });
    }

    for (let i = 0; i < nodePositions.length; i++) {
        const current = nodePositions[i];
        const next = nodePositions[(i + 1) % nodePositions.length];

        ctx.beginPath();
        ctx.moveTo(current.x, current.y);
        ctx.lineTo(next.x, next.y);
        ctx.strokeStyle = "rgba(255,255,255,0.25)";
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    for (const node of nodePositions.sort((a, b) => a.depth - b.depth)) {
        const glow = ctx.createRadialGradient(
            node.x - 4,
            node.y - 4,
            2,
            node.x,
            node.y,
            node.size * 2.4
        );

        glow.addColorStop(0, "#ffffff");
        glow.addColorStop(0.35, "#ff4fa3");
        glow.addColorStop(1, "rgba(86,0,114,0.1)");

        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
        ctx.fillStyle = glow;
        ctx.fill();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px Arial";
        ctx.textAlign = "center";
        ctx.fillText(node.metric?.label?.slice(0, 10) || "RNA", node.x, node.y + node.size + 18);
    }

    ctx.textAlign = "left";

    drawRoundedRect(ctx, 34, 112, 280, 190, 18);
    ctx.fillStyle = "rgba(0,0,0,0.48)";
    ctx.fill();

    ctx.fillStyle = "#ffb4d0";
    ctx.font = "bold 14px Arial";
    ctx.fillText("LIVE RESULT SUMMARY", 54, 145);

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 22px Arial";
    ctx.fillText(mode, 54, 176);

    ctx.font = "15px Arial";
    ctx.fillStyle = "rgba(255,255,255,0.82)";

    const summaryLines = metrics.slice(0, 5).map((metric) => {
        return `${metric.label}: ${formatMetric(metric.value)}`;
    });

    if (!summaryLines.length) {
        summaryLines.push("Run an action to render data.");
    }

    summaryLines.forEach((line, index) => {
        ctx.fillText(line, 54, 212 + index * 24);
    });
}


async function runQaoaCircuitPrototype() {
    await postJson(
        "/api/qaoa-circuit",
        { sequence: getSequence() },
        "Running QAOA circuit prototype on Qiskit AerSimulator..."
    );
}


function drawMetricChart(data) {
    const canvas = document.getElementById("metricChartCanvas");

    if (!canvas) {
        return;
    }

    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const background = ctx.createLinearGradient(0, 0, width, height);
    background.addColorStop(0, "#050009");
    background.addColorStop(0.7, "#2A0048");
    background.addColorStop(1, "#560072");

    ctx.fillStyle = background;
    ctx.fillRect(0, 0, width, height);

    const metrics = collectVisualMetrics(data).slice(0, 8);

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 28px Arial";
    ctx.fillText("Professional Metric Graph", 34, 46);

    if (!metrics.length) {
        ctx.font = "17px Arial";
        ctx.fillStyle = "rgba(255,255,255,0.75)";
        ctx.fillText("Run a dashboard action to generate chart-ready metrics.", 34, 82);
        return;
    }

    const maxValue = Math.max(...metrics.map((metric) => Math.abs(metric.value)), 1);
    const chartX = 70;
    const chartY = 95;
    const chartW = width - 120;
    const chartH = height - 155;
    const barGap = 14;
    const barW = (chartW - barGap * (metrics.length - 1)) / metrics.length;

    ctx.strokeStyle = "rgba(255,255,255,0.18)";
    ctx.lineWidth = 1;

    for (let i = 0; i <= 4; i++) {
        const y = chartY + (chartH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(chartX, y);
        ctx.lineTo(chartX + chartW, y);
        ctx.stroke();
    }

    metrics.forEach((metric, index) => {
        const value = Math.abs(metric.value);
        const barHeight = (value / maxValue) * chartH;
        const x = chartX + index * (barW + barGap);
        const y = chartY + chartH - barHeight;

        const gradient = ctx.createLinearGradient(x, y, x, chartY + chartH);
        gradient.addColorStop(0, "#ff2f7d");
        gradient.addColorStop(0.55, "#a90072");
        gradient.addColorStop(1, "#560072");

        drawRoundedRect(ctx, x, y, barW, barHeight, 12);
        ctx.fillStyle = gradient;
        ctx.fill();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 14px Arial";
        ctx.textAlign = "center";
        ctx.fillText(formatMetric(metric.value), x + barW / 2, y - 10);

        ctx.save();
        ctx.translate(x + barW / 2, chartY + chartH + 22);
        ctx.rotate(-0.28);
        ctx.fillStyle = "rgba(255,255,255,0.84)";
        ctx.font = "12px Arial";
        ctx.fillText(metric.label, 0, 0);
        ctx.restore();
    });

    ctx.textAlign = "left";
}

function renderDataVisuals(data) {
    drawResult3dSimulation(data);
    drawMetricChart(data);
}


function drawRnaSimulation(sequence, structure) {
    const canvas = document.getElementById("rnaCanvas");

    if (!canvas) {
        return;
    }

    const ctx = canvas.getContext("2d");

    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, "#000000");
    gradient.addColorStop(0.35, "#2A0048");
    gradient.addColorStop(0.7, "#800080");
    gradient.addColorStop(1, "#D50048");

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    if (!sequence) {
        ctx.fillStyle = "#ffffff";
        ctx.font = "28px Arial";
        ctx.fillText("Enter an RNA sequence to visualize.", 40, 80);
        return;
    }

    const cleanSequence = sequence.replace(/\s/g, "").toUpperCase();
    const cleanStructure = structure || ".".repeat(cleanSequence.length);
    const pairs = dotBracketToPairs(cleanStructure);

    const margin = 70;
    const usableWidth = width - margin * 2;
    const centerY = height * 0.58;
    const spacing = usableWidth / Math.max(cleanSequence.length - 1, 1);

    const positions = [];

    for (let i = 0; i < cleanSequence.length; i++) {
        const x = margin + i * spacing;
        const wave = Math.sin(i * 0.65) * 38;
        const y = centerY + wave;
        positions.push({ x, y });
    }

    for (const [i, j] of pairs) {
        if (!positions[i] || !positions[j]) {
            continue;
        }

        const start = positions[i];
        const end = positions[j];
        const midX = (start.x + end.x) / 2;
        const arcHeight = Math.min(150, 30 + Math.abs(end.x - start.x) * 0.22);

        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.quadraticCurveTo(midX, centerY - arcHeight, end.x, end.y);
        ctx.strokeStyle = "rgba(255, 120, 180, 0.75)";
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    ctx.beginPath();

    for (let i = 0; i < positions.length; i++) {
        const point = positions[i];

        if (i === 0) {
            ctx.moveTo(point.x, point.y);
        } else {
            ctx.lineTo(point.x, point.y);
        }
    }

    ctx.strokeStyle = "rgba(255, 255, 255, 0.55)";
    ctx.lineWidth = 3;
    ctx.stroke();

    for (let i = 0; i < positions.length; i++) {
        const point = positions[i];
        const base = cleanSequence[i];

        const nodeGradient = ctx.createRadialGradient(
            point.x - 4,
            point.y - 5,
            2,
            point.x,
            point.y,
            14
        );

        nodeGradient.addColorStop(0, "#ffffff");
        nodeGradient.addColorStop(0.45, "#D50048");
        nodeGradient.addColorStop(1, "#560072");

        ctx.beginPath();
        ctx.arc(point.x, point.y, 13, 0, Math.PI * 2);
        ctx.fillStyle = nodeGradient;
        ctx.fill();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px Arial";
        ctx.textAlign = "center";
        ctx.fillText(base, point.x, point.y + 4);
    }

    ctx.textAlign = "left";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 24px Arial";
    ctx.fillText("RNA Secondary Structure Simulation", 34, 44);

    ctx.font = "15px Arial";
    ctx.fillStyle = "rgba(255,255,255,0.8)";
    ctx.fillText(`Length: ${cleanSequence.length} bases`, 34, 72);
    ctx.fillText(`Base pairs shown: ${pairs.length}`, 34, 94);
}



window.addEventListener("load", () => {
    drawCurrentInput();
});

// Phase 36 — Guided Workflow + Smart Output Display

const PHASE36_ALWAYS_VISIBLE = [
    "workflow-guide-panel",
    "focused-result-panel",
    "input-panel",
    "summary-panel",
    "results-panel"
];

const PHASE36_WORKFLOWS = {
    overview: {
        title: "Overview",
        description: "Use this mode to understand the project and start from the RNA input. It keeps the dashboard clean before choosing a specific research path.",
        required: "RNA sequence",
        recommended: "Analyze Sequence, then choose Classical RNA, QUBO Optimization, Quantum Experiments, or Compression Research.",
        output: "Project context, input controls, focused action summary, and optional raw JSON.",
        panels: [
            "context-panel"
        ]
    },

    classical: {
        title: "Classical RNA Analysis",
        description: "Use this workflow to inspect the RNA sequence, validate dot-bracket structure, run the classical benchmark, and view bioinformatics resources.",
        required: "RNA sequence and optional dot-bracket structure.",
        recommended: "Analyze Sequence → Validate Structure → Run Classical Benchmark → Run Bioinformatics Metrics.",
        output: "Sequence length, GC percentage, dot-bracket validation, ViennaRNA-style MFE output, and BLAST/RCSB links.",
        panels: [
            "simulation-panel",
            "bioinformatics-panel"
        ]
    },

    qubo: {
        title: "QUBO Optimization",
        description: "Use this workflow to build the optimization problem from RNA candidate pairs and stems, then compare baseline solvers.",
        required: "RNA sequence.",
        recommended: "Generate Candidate Pairs → Generate Candidate Stems → Build Stem QUBO → Run Greedy Solver → Run Simulated Annealing → Compare Solvers.",
        output: "Candidate pairs, candidate stems, QUBO variables, quadratic terms, solver comparison, F1 metrics, and scaling graphs.",
        panels: [
            "qubo-panel",
            "graphs-panel",
            "algorithm-panel"
        ]
    },

    quantum: {
        title: "Quantum Experiments",
        description: "Use this workflow for QAOA/VQE readiness, circuit simulation, parameter sweeps, measured bitstring energy, and hardware-readiness planning.",
        required: "RNA sequence and QUBO-ready candidate stems.",
        recommended: "Run Quantum Benchmark → Run QAOA Circuit Prototype → Run VQE Circuit Prototype → Run Circuit Comparison → Run QAOA/VQE Sweeps → Run Hardware Readiness Check.",
        output: "Estimated qubits, circuit depth, transpiled depth, top bitstrings, top probabilities, runtime, energy checks, and hardware-readiness notes.",
        panels: [
            "quantum-benchmark-panel",
            "qaoa-circuit-panel",
            "vqe-circuit-panel",
            "circuit-comparison-panel",
            "qaoa-sweep-panel",
            "vqe-sweep-panel",
            "measured-bitstring-panel",
            "hardware-readiness-panel"
        ]
    },

    compression: {
        title: "Compression Research",
        description: "Use this workflow to compare direct one-variable-per-qubit mapping against QRAC/QRAO-style compression and qubit-efficient log encoding estimates.",
        required: "RNA sequence and QUBO variables.",
        recommended: "Run Qubit Compression Estimator → Run QRAO Subset Mapping.",
        output: "Direct qubits, 2-to-1 QRAC estimate, 3-to-1 QRAC estimate, 3-to-2 QRAC estimate, log-style estimate, compression ratios, risk notes, and X/Y/Z mapping table.",
        panels: [
            "qubit-compression-panel",
            "qrao-mapping-panel"
        ]
    },

    demo: {
        title: "Full Research Demo",
        description: "Use this workflow for a professor or demo-day walkthrough. It shows only the major checkpoints instead of every raw technical panel.",
        required: "RNA sequence.",
        recommended: "Analyze Sequence → Build Stem QUBO → Run Simulated Annealing → Run Quantum Benchmark → Run Circuit Comparison → Run Qubit Compression Estimator → Run QRAO Subset Mapping.",
        output: "A clean end-to-end view of the classical, QUBO, quantum, and compression research pipeline.",
        panels: [
            "context-panel",
            "qubo-panel",
            "quantum-benchmark-panel",
            "circuit-comparison-panel",
            "qubit-compression-panel",
            "qrao-mapping-panel"
        ]
    }
};

function phase36Escape(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function phase36QueryPanelById(panelId) {
    return document.querySelectorAll(`#${panelId}`);
}

function getAllPhase36PanelIds() {
    const ids = new Set();

    Object.values(PHASE36_WORKFLOWS).forEach((workflow) => {
        workflow.panels.forEach((panelId) => ids.add(panelId));
    });




    PHASE36_ALWAYS_VISIBLE.forEach((panelId) => ids.add(panelId));

    return Array.from(ids);
}

function setWorkflowMode(workflowName) {
    const workflow = PHASE36_WORKFLOWS[workflowName] || PHASE36_WORKFLOWS.overview;

    const allPanels = getAllPhase36PanelIds();
    const visiblePanels = new Set([
        ...PHASE36_ALWAYS_VISIBLE,
        ...workflow.panels
    ]);

    allPanels.forEach((panelId) => {
        const panels = phase36QueryPanelById(panelId);

        panels.forEach((panel) => {
            if (visiblePanels.has(panelId)) {
                panel.classList.remove("workflow-hidden");
            } else {
                panel.classList.add("workflow-hidden");
            }
        });
    });

    const buttons = document.querySelectorAll(".workflow-tab");
    buttons.forEach((button) => button.classList.remove("active"));

    const activeButton = Array.from(buttons).find((button) => {
        return button.getAttribute("onclick") === `setWorkflowMode('${workflowName}')`;
    });

    if (activeButton) {
        activeButton.classList.add("active");
    }

    const instructionBox = document.getElementById("workflowInstructionBox");

    if (instructionBox) {
        instructionBox.innerHTML = `
            <h4>${phase36Escape(workflow.title)}</h4>
            <p>${phase36Escape(workflow.description)}</p>
            <ul>
                <li><strong>Required input:</strong> ${phase36Escape(workflow.required)}</li>
                <li><strong>Recommended actions:</strong> ${phase36Escape(workflow.recommended)}</li>
                <li><strong>Focused output:</strong> ${phase36Escape(workflow.output)}</li>
            </ul>
        `;
    }
}

function updateFocusedResultSummary(data) {
    const container = document.getElementById("focusedResultSummaryCard");

    if (!container || !data) {
        return;
    }

    const summary = getFocusedActionSummary(data);

    container.innerHTML = `
        <h4>${phase36Escape(summary.title)}</h4>
        <p>${phase36Escape(summary.purpose)}</p>

        <div class="focused-summary-grid">
            <article class="focused-summary-item">
                <span>Required Input</span>
                <strong>${phase36Escape(summary.required)}</strong>
            </article>

            <article class="focused-summary-item">
                <span>Main Output</span>
                <strong>${phase36Escape(summary.output)}</strong>
            </article>

            <article class="focused-summary-item">
                <span>Recommended Next Step</span>
                <strong>${phase36Escape(summary.next)}</strong>
            </article>

            <article class="focused-summary-item">
                <span>Status</span>
                <strong>${phase36Escape(data.success === false ? "Needs review" : "Success")}</strong>
            </article>
        </div>
    `;
}

function getFocusedActionSummary(data) {
    if (data.qubit_compression_estimator) {
        const result = data.qubit_compression_estimator;

        return {
            title: "Qubit Compression Estimator",
            purpose: "Compares direct one-variable-per-qubit mapping against QRAC/QRAO-style compression and qubit-efficient log encoding estimates.",
            required: "RNA sequence and generated QUBO variables.",
            output: `${result.variable_count} variables, ${result.direct_qubits} direct qubits, plus compression estimates.`,
            next: "Run QRAO Subset Mapping to see how variables map into compressed qubit slots."
        };
    }

    if (data.qrao_subset_mapping) {
        const result = data.qrao_subset_mapping;

        return {
            title: "QRAO Subset Mapping",
            purpose: "Maps RNA QUBO variables into compressed qubit slots using X, Y, and Z Pauli-axis labels.",
            required: "RNA sequence and QUBO variables.",
            output: `${result.selected_variable_count} selected variables, ${result.direct_qubits} direct qubits, ${result.three_to_one_qubits} compressed qubits with 3-to-1 mapping.`,
            next: "Compare this result with the Quantum Benchmark and Hardware Readiness sections."
        };
    }

    if (data.hardware_readiness) {
        return {
            title: "Hardware Readiness Check",
            purpose: "Estimates whether the QAOA and VQE circuits are small enough for possible future hardware testing.",
            required: "QAOA and VQE circuit prototypes.",
            output: "Qubit counts, transpiled depth, circuit size, CX gate count, and readiness notes.",
            next: "Use this as a planning estimate before any real hardware run."
        };
    }

    if (data.measured_bitstring_energy) {
        const result = data.measured_bitstring_energy;
        const best = result.best_result || {};

        return {
            title: "Measured Bitstring Energy",
            purpose: "Converts measured simulator bitstrings back into QUBO assignments and estimates their QUBO energy.",
            required: "QAOA/VQE measured bitstrings and QUBO terms.",
            output: `Best source: ${best.source || "not available"}, estimated energy: ${best.estimated_qubo_energy ?? "not available"}.`,
            next: "Use this to compare whether circuit outputs are producing useful QUBO solutions."
        };
    }

    if (data.vqe_parameter_sweep) {
        const best = data.vqe_parameter_sweep.best_result || {};

        return {
            title: "VQE Parameter Sweep",
            purpose: "Tests multiple VQE ansatz settings on the VQE-ready Hamiltonian subset.",
            required: "VQE-ready subset and simulator.",
            output: `Best angle scale: ${best.angle_scale ?? "not available"}, top probability: ${best.top_probability ?? "not available"}.`,
            next: "Run Measured Bitstring Energy to evaluate the measured output against the QUBO objective."
        };
    }

    if (data.qaoa_parameter_sweep) {
        const best = data.qaoa_parameter_sweep.best_result || {};

        return {
            title: "QAOA Parameter Sweep",
            purpose: "Tests multiple gamma and beta values for the QAOA-style circuit.",
            required: "QAOA-ready QUBO subset.",
            output: `Best gamma: ${best.gamma ?? "not available"}, best beta: ${best.beta ?? "not available"}, energy: ${best.top_energy ?? "not available"}.`,
            next: "Compare this with VQE Parameter Sweep and Measured Bitstring Energy."
        };
    }

    if (data.circuit_comparison) {
        return {
            title: "QAOA vs VQE Circuit Comparison",
            purpose: "Compares QAOA and VQE simulator prototypes side by side.",
            required: "QAOA and VQE circuit prototypes.",
            output: "Circuit depth, transpiled depth, runtime, circuit size, and top measurement probability.",
            next: "Run Hardware Readiness Check to estimate future hardware feasibility."
        };
    }

    if (data.vqe_circuit) {
        return {
            title: "VQE Circuit Prototype",
            purpose: "Runs a small VQE-style ansatz circuit on Qiskit Aer.",
            required: "VQE-ready Ising/Hamiltonian subset.",
            output: "Top bitstring, top probability, circuit depth, transpiled depth, and runtime.",
            next: "Run Circuit Comparison or VQE Parameter Sweep."
        };
    }

    if (data.qaoa_circuit) {
        return {
            title: "QAOA Circuit Prototype",
            purpose: "Runs a small QAOA-style circuit on Qiskit Aer.",
            required: "QAOA-ready QUBO subset.",
            output: "Top bitstring, top probability, circuit depth, transpiled depth, and runtime.",
            next: "Run Circuit Comparison or QAOA Parameter Sweep."
        };
    }

    if (data.quantum_benchmark) {
        return {
            title: "Quantum Benchmark",
            purpose: "Compares QAOA-ready and VQE-ready subsets against exact subset baselines.",
            required: "RNA sequence and QUBO formulation.",
            output: "Estimated qubits, circuit-depth estimates, Hamiltonian terms, and subset energies.",
            next: "Run QAOA Circuit Prototype and VQE Circuit Prototype."
        };
    }

    if (data.bioinformatics_metrics) {
        return {
            title: "Bioinformatics Metrics",
            purpose: "Connects RNA/QUBO metrics with bioinformatics interpretation and external resources.",
            required: "RNA sequence.",
            output: "Sequence metrics, QUBO metrics, solver metrics, and BLAST/RCSB resource links.",
            next: "Use this before explaining biological motivation or validation direction."
        };
    }

    if (data.success === false) {
        return {
            title: "Action Needs Review",
            purpose: "The selected action returned an error or did not complete.",
            required: "Check the input sequence and terminal logs.",
            output: data.error || "No error message provided.",
            next: "Fix the error, then rerun the same action."
        };
    }

    return {
        title: "Dashboard Action Complete",
        purpose: "The selected dashboard action completed successfully.",
        required: "RNA sequence or selected workflow input.",
        output: "Focused metrics are shown in the relevant section, with raw JSON available below.",
        next: "Choose another workflow action or open the raw JSON for full technical details."
    };
}

document.addEventListener("DOMContentLoaded", () => {
    setWorkflowMode("overview");
});


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

