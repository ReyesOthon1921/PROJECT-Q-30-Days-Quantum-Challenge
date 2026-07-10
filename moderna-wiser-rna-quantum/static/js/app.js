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
    renderDataVisuals(data);
    renderAlgorithmGraphImages(data);
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